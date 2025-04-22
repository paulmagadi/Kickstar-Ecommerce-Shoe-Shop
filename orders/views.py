from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import ShippingAddress, Order, OrderItem
from .forms import ShippingAddressForm
from cart.cart import Cart
from cart.models import Cart as CartModel
from store.models import Product
from django.db import transaction


@login_required
def shipping_address(request):
    shipping_address = ShippingAddress.objects.filter(user=request.user).first()
    
    # Preserve `next` for redirection after form submission
    # next_url = request.GET.get('next', request.POST.get('next', '/'))
    next_url = request.GET.get('next') or request.POST.get('next') or reverse("home")


    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=shipping_address)
        if form.is_valid():
            shipping_address = form.save(commit=False)
            shipping_address.user = request.user
            shipping_address.save()
            messages.success(request, "Your shipping information has been updated.")
            return redirect(next_url)  # Redirect to intended page
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ShippingAddressForm(instance=shipping_address)
    
    context = {'form': form, 'next': next_url}

    return render(request, 'orders/shipping_information.html', context)

@login_required
def create_order(request):
    cart_instance = Cart(request)
    cart_items = cart_instance.get_prods()
    cart_quantities = cart_instance.get_quants()
    order_total = cart_instance.order_total()

    if not cart_items:
        messages.error(request, "Your cart is empty. Please add items before placing an order.")
        return redirect("cart")

    try:
        shipping_address = ShippingAddress.objects.get(user=request.user)
    except ShippingAddress.DoesNotExist:
        messages.error(request, "Please add a shipping address before placing an order.")
        next_url = reverse("checkout")
        return redirect(f"{reverse('shipping_address')}?next={next_url}")

    try:
        with transaction.atomic():
            # Step 1: Lock all products in the cart to prevent race conditions
            product_ids = [item.id for item in cart_items]
            products = Product.objects.select_for_update().filter(id__in=product_ids)
            product_dict = {p.id: p for p in products}

            # Step 2: Check stock availability for all items before any operations
            for item in cart_items:
                product = product_dict.get(item.id)
                
                if not product:
                    messages.error(request, f"Product '{item.name}' is no longer available and has been removed from your cart.")
                    cart_instance.delete(item.id)  # Remove it from the cart
                    return redirect("cart")
                
                quantity = cart_quantities.get(str(item.id), 0)
                if product.stock_quantity < quantity:
                    messages.error(request, f"Sorry, only {product.stock_quantity} left for {product.name}. Update your cart.")
                    return redirect("cart")
                
                if not cart_instance.get_prods():  # 🚀 Check if the cart is now empty
                    messages.error(request, "Your cart is empty after removing unavailable items.")
                    return redirect("home")  # Redirect to store instead of cart


            # Step 3: All checks passed; create the order and order items
            order = Order.objects.create(
                user=request.user,
                full_name=shipping_address.full_name,
                email=shipping_address.email,
                amount_paid=order_total,
                shipping_address=f"{shipping_address.address1}, {shipping_address.city}, {shipping_address.state}, {shipping_address.zipcode}, {shipping_address.country}",
                payment_method="Pay on Delivery",
                status="Pending",
            )

            # Step 4: Deduct stock and create order items
            for item in cart_items:
                product = product_dict[item.id]
                quantity = cart_quantities[str(item.id)]
                
                product.stock_quantity -= quantity
                product.save()

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=item.sale_price if item.is_sale else item.price
                )

            # Clear the cart after successful order creation
            cart_instance.clear()

            messages.success(request, "Your order has been placed successfully! Expect delivery soon.")
            return redirect("order_confirmation", order_id=order.id)

    except Exception as e:
        messages.error(request, "An error occurred while processing your order. Please try again.")
        return redirect("cart")

def order_confirmation(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    return render(request, 'orders/order_confirmation.html', {"order": order})



@login_required
def orders(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-date_ordered')
    
    breadcrumbs = [
        ('Home', reverse('home')),
        ('My account', reverse('profile')),
        ('Orders', None),  
    ]
    context = {
        'orders': user_orders,
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'orders/orders.html', context)


@login_required
def set_order_session(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        request.session['view_order_id'] = order_id
        return redirect('order')
    return redirect('orders')


@login_required
def order(request):
    order_id = request.session.get('view_order_id')
    if not order_id:
        messages.error(request, "No order selected.")
        return redirect('orders')

    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = OrderItem.objects.filter(order=order)

    breadcrumbs = [
        ('Home', reverse('home')),
        ('My account', reverse('profile')),
        ('Orders', reverse('orders')),
        ('Order Details', None),  
    ]
    
    context = {
        'order': order,
        'items': items,
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'orders/order.html', context)

