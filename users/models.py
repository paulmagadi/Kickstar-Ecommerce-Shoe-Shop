from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from users.managers import CustomUserManager
from django.db.models.signals import post_save, pre_save
from django.templatetags.static import static

from django.dispatch import receiver
import uuid
from django.utils import timezone
from django.core.mail import send_mail
from django.urls import reverse


from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

# from django_rest_passwordreset.signals import reset_password_token_created

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name='email', unique=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_email_verified = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='uploads/users', null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name_plural = "Users"
    
    def generate_email_verification_token(self):
        return str(uuid.uuid4())
    
    @property
    def imageURL(self):
        if self.profile_image:
            return self.profile_image.url
        return static('images/brand/logo2.svg')



class EmailVerificationToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

@receiver(post_save, sender=CustomUser)
def send_email_verification(sender, instance, created, **kwargs):
    if created:
        # Create verification token
        token = instance.generate_email_verification_token()
        expires_at = timezone.now() + timezone.timedelta(hours=24)
        
        EmailVerificationToken.objects.create(
            user=instance,
            token=token,
            expires_at=expires_at
        )
        
        verification_url = f"http://127.0.0.1:8000{reverse('verify-email', kwargs={'token': token})}"
        
        subject = 'Verify your email address'
        from_email = 'noreply@yourdomain.com'
        to_email = [instance.email]
        
        text_content = f'Please click the following link to verify your email: {verification_url}'
        html_content = render_to_string('users/emails/verification-mail.html', {
            'user': instance,
            'verification_url': verification_url
        })
        
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
             

class BillingAddress(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="billing_address")
    phone = models.CharField(max_length=20, blank=True)
    full_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255, null=True, blank=True)
    zipcode = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=255)

    def __str__(self):
        return self.user.email
    
    class Meta:
        verbose_name_plural = 'Billing Address'


@receiver(post_save, sender=CustomUser)
def handle_billing_address(sender, instance, created, **kwargs):
    if created:
        BillingAddress.objects.create(
            user=instance,
            full_name=f"{instance.first_name} {instance.last_name}",
            email=instance.email
        )
    else:
        try:
            billing = instance.billing_address
            billing.full_name = f"{instance.first_name} {instance.last_name}"
            billing.email = instance.email
            billing.save()
        except BillingAddress.DoesNotExist:
            BillingAddress.objects.create(
                user=instance,
                full_name=f"{instance.first_name} {instance.last_name}",
                email=instance.email
            )



# @receiver(post_save, sender=CustomUser)
# def handle_billing_address(sender, instance, created, **kwargs):
#     if created:
#         BillingAddress.objects.create(
#             user=instance,
#             full_name=f"{instance.first_name} {instance.last_name}",
#             email=instance.email
#         )
#     else:
#         try:
#             billing = instance.billing_address
#             billing.full_name = f"{instance.first_name} {instance.last_name}"
#             billing.email = instance.email
#             billing.save()
#         except BillingAddress.DoesNotExist:
#             pass


