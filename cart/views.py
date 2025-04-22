import random
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls import reverse

from store.products import ProductSession

from .cart import Cart
from store.models import Product
from django.contrib import messages
from django.http import JsonResponse
from orders.models import ShippingAddress

def cart(request):
    cart_instance = Cart(request)
    cart_items = cart_instance.get_prods()
    cart_quantities = cart_instance.get_quants()
    
    # Create a dictionary to track product stock status
    stock_updates = {
        'removed_items': [],
        'updated_items': []
    }

    for item in cart_items:
        product = Product.objects.get(id=item.id)
        cart_quantity = cart_quantities.get(str(item.id), 0)

        if product.stock_quantity == 0:
            # Remove item if out of stock
            cart_instance.delete(item.id)
            stock_updates['removed_items'].append(product.name)
            
        elif cart_quantity > product.stock_quantity:
            # Update quantity to match available stock
            cart_instance.update(request=request, product=product, quantity=product.stock_quantity)
            stock_updates['updated_items'].append({
                'name': product.name,
                'quantity': product.stock_quantity
            })

    # Add flash messages based on updates
    if stock_updates['removed_items']:
        items_list = ", ".join(stock_updates['removed_items'])
        messages.warning(request, f"These items are out of stock and were removed: {items_list}")
    
    if stock_updates['updated_items']:
        for item in stock_updates['updated_items']:
            messages.warning(request, 
                f"Stock updated: {item['name']} quantity reduced to {item['quantity']} (max available)")

    # Recalculate totals after potential updates
    cart_items = cart_instance.get_prods()  # Refresh after possible deletions
    cart_quantities = cart_instance.get_quants()
    total_quantity = sum(cart_quantities.values())
    order_total = cart_instance.order_total()
    
    breadcrumbs = [
        ('Home', reverse('home')),
        ('Cart', reverse('cart')), 
    ]
    
    '''We use sessions to track viewed products'''
    product_session = ProductSession(request)

    viewed_products = product_session.get_recently_viewed_products(limit=12)  
    product_ids = product_session.get_product_ids() 
    viewed_products = list(viewed_products)
    viewed_products.sort(key=lambda x: product_ids.index(str(x.id)))

    # 🛒 Exclude products in the cart
    cart_product_ids = [str(item.id) for item in cart_items]
    viewed_products = [p for p in viewed_products if str(p.id) not in cart_product_ids]


    context = {
        'cart_items': cart_items,
        'cart_quantities': cart_quantities,
        'total_quantity': total_quantity,
        'order_total': order_total,
        'breadcrumbs': breadcrumbs,
        'viewed_products': viewed_products
    }
    return render(request, 'cart/cart.html', context)
        


def add_to_cart(request):
    cart = Cart(request)
    if request.POST.get('product_id'):
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))
        product = get_object_or_404(Product, id=product_id)
        cart.add(product=product, quantity=product_qty, request=request)

        cart_quantity = cart.__len__()
        response = JsonResponse({'qty': cart_quantity})
        return response  
    
def cart_update(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('product_id'))
        product = get_object_or_404(Product, id=product_id) 
        product_qty = int(request.POST.get('product_qty'))

        cart.update(request, product=product, quantity=product_qty)  

        response = JsonResponse({'qty': product_qty})
        return response


def cart_delete(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('product_id'))
        product = get_object_or_404(Product, id=product_id)
        cart.delete(product=product_id)

        response = JsonResponse({'product': product_id})
        messages.info(request, f'{product.name} removed from cart')
        return response
    

@login_required()
def checkout(request):
    cart_instance = Cart(request)  
    cart_items = cart_instance.get_prods() 
    cart_quantities = cart_instance.get_quants()
    total_quantity = sum(cart_quantities.values())
    order_total = cart_instance.order_total()
    products = Product.objects.all()
        
    shipping_address = ShippingAddress.objects.filter(user=request.user).first()

    breadcrumbs = [
        ('Home', reverse('home')),
        ('Cart', reverse('cart')), 
        ('Checkout', reverse('checkout')), 
    ]
    
    context = {
        'cart_items': cart_items,
        'cart_quantities': cart_quantities,
        'total_quantity': total_quantity,
        'order_total': order_total,
        'products': products,
        'shipping_address': shipping_address,  
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'cart/checkout.html', context)