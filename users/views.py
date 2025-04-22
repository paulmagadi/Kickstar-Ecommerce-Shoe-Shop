from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse

from orders.models import Order, ShippingAddress
from store.models import Product

from .forms import CustomUserRegistrationForm, UpdateUserForm, UpdateUserPassword, UpdatedBillingAddressForm, UserProfileImageForm
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser, EmailVerificationToken, BillingAddress
from cart.models import Cart as CartModel, CartItem
from cart.cart import Cart
import json
from django.utils.http import url_has_allowed_host_and_scheme

from django.utils import timezone

from django.core.cache import cache
from django.utils.html import mark_safe
from django.contrib.auth.decorators import login_required

def register_user(request):
    next_url = request.GET.get('next') or request.POST.get('next', '/') 
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = '/' 
    
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # User won't be active until email is verified
            user.save()
            
            # No longer logging in immediately after registration
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            return redirect('login')
        else:
            messages.error(request, "Unsuccessful registration. Invalid information.")
    else:
        form = CustomUserRegistrationForm()
    return render(request, 'users/register.html', {'form': form, 'next': next_url})


def verify_email(request, token):
    try:
        verification_token = EmailVerificationToken.objects.get(token=token)
        
        if verification_token.is_expired():
            messages.error(request, 'The verification link has expired.')
            return redirect('login')  
        
        user = verification_token.user
        user.is_email_verified = True
        user.is_active = True  # Activate the user
        user.save()
        
        verification_token.delete()
        
        messages.success(request, 'Email verified successfully! You can now log in.')
        return redirect('login')  
        
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('register')

from django.core.mail import send_mail
from django.shortcuts import redirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import EmailVerificationToken
from django.utils import timezone
from django.conf import settings
import uuid

from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model

def resend_verification(request):
    email = request.GET.get('email') or (request.user.email if request.user.is_authenticated else None)
    
    if not email:
        messages.error(request, 'Please provide an email address.')
        return redirect('login')
    
    User = get_user_model()
    try:
        user = User.objects.get(email=email)
        
        if user.is_email_verified:
            messages.info(request, 'This email is already verified.')
            return redirect('login')
        
        # Delete existing tokens
        EmailVerificationToken.objects.filter(user=user).delete()
        
        # Create new token
        token = str(uuid.uuid4())
        expires_at = timezone.now() + timezone.timedelta(hours=24)
        EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        
        verification_url = f"http://127.0.0.1:8000{reverse('verify-email', kwargs={'token': token})}"
        
        subject = 'Verify your email address'
        from_email = 'noreply@yourdomain.com'
        to_email = [user.email]
        
        text_content = f'Please click the following link to verify your email: {verification_url}'
        html_content = render_to_string('users/emails/verification-mail.html', {
            'user': user,
            'verification_url': verification_url
        })
        
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        messages.success(request, 'Verification email has been resent! Please check your inbox.')
        return redirect('login')
        
    except User.DoesNotExist:
        messages.error(request, 'No account found with this email. Register to get verified')
    except Exception as e:
        messages.error(request, f'Failed to resend verification email: {e}')
    
    return redirect('login')



from django.core.cache import cache
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from django.utils.safestring import mark_safe

def login_user(request):
    # Rate limiting
    remaining_attempts = 5
    # Only check rate limiting on POST requests
    if request.method == 'POST':
        # Create cache key combining IP and username
        username = request.POST.get('username', '')
        cache_key = f'login_attempts_{request.META.get("REMOTE_ADDR")}_{username}'
        attempts = cache.get(cache_key, 0)
        remaining_attempts = max(5 - attempts, 0)
        
        if attempts >= 5:
            messages.error(request, 'Too many login attempts. Please try again later or reset your password.')
            return render(request, 'users/login.html', {
                'form': AuthenticationForm(),
                'remaining_attempts': 0
            })
            
    # Next URL validation
    next_url = request.GET.get('next') or request.POST.get('next', '/')  
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = '/' 
    
    # Redirect if already authenticated
    if request.user.is_authenticated:
        return redirect(next_url)
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request=request, username=username, password=password)  

            if user is not None:
                if user.is_email_verified:
                    # Successful login - reset attempt counter
                    cache.delete(cache_key)
                    
                    login(request, user)
                    
                    # Your exact cart implementation
                    session_cart = Cart(request)
                    session_cart_items = session_cart.get_items()  # {product_id: quantity}

                    user_cart, created = CartModel.objects.get_or_create(user=user)
                    existing_cart_items = {item.product.id: item.quantity for item in CartItem.objects.filter(cart=user_cart)}

                    for product_id, session_quantity in session_cart_items.items():
                        product = Product.objects.get(id=product_id)
                        if product_id in existing_cart_items:
                            new_quantity = max(session_quantity, existing_cart_items[product_id])
                        else:
                            new_quantity = session_quantity
                        
                        CartItem.objects.update_or_create(
                            cart=user_cart,
                            product=product,
                            defaults={"quantity": new_quantity}
                        )

                    db_cart_items = CartItem.objects.filter(cart=user_cart)
                    for item in db_cart_items: 
                        session_cart.db_add(product=item.product, quantity=item.quantity)

                    messages.success(request, 'Login successful!')
                    return redirect(next_url)
                else:
                     # Add resend verification URL to context
                    resend_url = reverse('resend-verification') + f'?email={username}'
                    form.add_error(None, "Please verify your email first")
                    return render(request, 'users/login.html', {
                        'form': form,
                        'next': next_url,
                        'remaining_attempts': remaining_attempts,
                        'show_resend_verification': True,
                        'resend_url': resend_url
                    })
                    
            else:
                # Check if the user exists but password was wrong
                try:
                    user = CustomUser.objects.get(email=username)
                    if user.is_email_verified:
                        # Only show password reset for verified users
                        return render(request, 'users/login.html', {
                            'form': form,
                            'next': next_url,
                            'remaining_attempts': remaining_attempts,
                        })
                except CustomUser.DoesNotExist:
                    pass
            
        # Invalid credentials
        cache.set(cache_key, attempts + 1, timeout=300)  # 5 min timeout
        remaining_attempts = max(4 - attempts, 0)  # Update remaining
        messages.error(request, f'Invalid email or password. {remaining_attempts} attempts remaining')
    else:
        form = AuthenticationForm()

    return render(request, 'users/login.html', {
        'form': form,
        'next': next_url,
        'remaining_attempts': remaining_attempts
    })

def logout_user(request):
    logout(request)
    messages.success(request, ('You have been logged out!!!'))
    return redirect('home')


def update_user(request):
    if request.user.is_authenticated:
        current_user = CustomUser.objects.get(id=request.user.id)
        user_form = UpdateUserForm(request.POST or None, instance=current_user) 
        
        if user_form.is_valid():
            user_form.save()
            
            login(request, current_user)
            messages.success(request, "User Details updated")
            return redirect('home')
        return render(request, 'users/update_user.html', {'user_form': user_form})
    else:
        messages.error(request, "You must be logged in to update your details")
        return redirect('home')


@login_required
def update_billing(request):
    if request.user.is_authenticated:
        billing_address, created = BillingAddress.objects.get_or_create(
        user=request.user,
        defaults={
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            'email': request.user.email
        }
    )

    form = UpdatedBillingAddressForm(request.POST or None, instance=billing_address)

    if request.method == 'POST' and form.is_valid():
        billing = form.save(commit=False)
        # Optionally update full_name and email again (in case user's name or email changed)
        billing.full_name = f"{request.user.first_name} {request.user.last_name}"
        billing.email = request.user.email
        billing.save()
        messages.success(request, "Your billing address info has been updated.")
        return redirect('profile')

    return render(request, 'users/update_billing.html', {'form': form,})




def update_password(request):
    if request.user.is_authenticated:
        current_user = request.user
        if request.method == "POST":
            form = UpdateUserPassword(current_user ,request.POST) 
            
            if form.is_valid():
                form.save()
                messages.success(request, "Your password has been updated. Login with your new password")
                return redirect('signin')
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
                return redirect('update_password')
                     
        else:
            form = UpdateUserPassword(current_user)
            return render(request, 'users/update_password.html', {'form': form})
    else:
        messages.error(request, "You must be logged in to update your password")
        return redirect('home')




from .forms import UserProfileImageForm
from .models import CustomUser
from django.http import JsonResponse

@login_required
def user_profile(request):
    if request.method == 'POST' and request.user.is_authenticated:
        current_user = CustomUser.objects.get(id=request.user.id)
        form = UserProfileImageForm(request.POST, request.FILES, instance=current_user)
        if form.is_valid():
            form.save()
            return JsonResponse({'image_url': current_user.imageURL})
        return JsonResponse({'error': 'Invalid form'}, status=400)
    else:
        form = UserProfileImageForm(instance=request.user)
        user_orders = Order.objects.filter(user=request.user).order_by('-date_ordered')  # Add ordering if needed
        billing_address = BillingAddress.objects.filter(user=request.user)
        shipping_address = ShippingAddress.objects.filter(user=request.user).first()
        
        breadcrumbs = [
        ('Home', reverse('home')),
        ('My account', reverse('profile')),
        ]
        context = {
            'user_profile_image_form': form,
            'orders': user_orders,
            'billing_address': billing_address,
            'shipping_address': shipping_address,
            'breadcrumbs': breadcrumbs,
        }
        return render(request, 'users/user_profile.html', context )
    
    
@login_required
def account_settings(request):
    breadcrumbs = [
        ('Home', reverse('home')),
        ('My account', reverse('profile')),
        ('My account settings', reverse('account_settings')),
        ]
    
    context = {
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'users/account-settings.html', context)



from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy

from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect

class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def form_valid(self, form):
            # Prepare the email options
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': self.extra_email_context,
        }
        
        # Send the email (only once)
        form.save(**opts)
        
        # Mark email as sent in session
        self.request.session['reset_email_sent'] = True
        
        return HttpResponseRedirect(self.get_success_url())
    

