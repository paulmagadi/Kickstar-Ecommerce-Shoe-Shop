import json
from django.conf import settings
from cart.models import CartItem, Cart as CartModel
from store.models import Product
from django.contrib import messages

class Cart():
    def __init__(self, request):
        self.session = request.session
        self.request = request
        cart = self.session.get('session_key')
        # Check if you have a session, if not create one
        if 'session_key' not in request.session:
            cart = request.session['session_key'] = {}
        self.cart = cart
    
        
    # Add product to session
    def add(self, request, product, quantity):
        product_id = str(product.id)
        available_quantity = product.stock_quantity

        if product_id in self.cart:
            total_quantity = self.cart[product_id] + quantity
            if total_quantity > available_quantity:
                self.cart[product_id] = available_quantity
                messages.warning(request, f"Quantity limit reached for {product.name}. Cart updated to maximum available quantity.")
            else:
                self.cart[product_id] = total_quantity
                messages.success(request, 'Product updated in cart.')
        else:
            if quantity > available_quantity:
                self.cart[product_id] = available_quantity
                messages.warning(request, f"Quantity limit reached for {product.name}. Cart updated to maximum available quantity.")
            else:
                self.cart[product_id] = quantity
                messages.success(request, 'Product added to cart.')

        self.session.modified = True

        # Logged-in user handling
        if self.request.user.is_authenticated:
            user_cart, created = CartModel.objects.get_or_create(user=self.request.user)

            # Update or create CartItem for the product
            cart_item, created = CartItem.objects.get_or_create(cart=user_cart, product=product)
            cart_item.quantity = self.cart[product_id]  # Ensure it matches session cart
            cart_item.save()

            user_cart.save()
            
    def db_add(self, product, quantity):
        product_id = str(product.id)  # Ensure it's the product ID as a string
        product_qty = int(quantity)   # Ensure quantity is an integer

        # Store in the database for logged-in users
        if self.request.user.is_authenticated:
            user_cart, created = CartModel.objects.get_or_create(user=self.request.user)

            # Update CartItem table
            cart_item, created = CartItem.objects.get_or_create(cart=user_cart, product=product)

            # ✅ Update quantity correctly (Set to max, not add)
            cart_item.quantity = max(product_qty, cart_item.quantity)  
            cart_item.save()

            # Ensure session syncs with the DB value
            self.cart[product_id] = cart_item.quantity  

        else:
            # ✅ Only modify session for guest users
            if product_id in self.cart:
                self.cart[product_id] += product_qty
            else:
                self.cart[product_id] = product_qty

        self.session.modified = True

        
    def update(self, request, product, quantity):
        product_id = str(product.id)  
        available_quantity = product.stock_quantity

        # Check if the requested quantity exceeds the available stock
        if quantity > available_quantity:
            # Limit the quantity to the available stock
            self.cart[product_id] = available_quantity
            messages.warning(request, f"Quantity limit reached for {product.name}. Cart updated to maximum available quantity.")
        else:
            # Update the quantity in the cart
            self.cart[product_id] = quantity
            messages.success(request, 'Cart updated successfully')

        self.session.modified = True
    
        #Logged in user
        if self.request.user.is_authenticated:
            user_cart, created = CartModel.objects.get_or_create(user=self.request.user)
            
            # Get the CartItem for this product
            cart_item, created = CartItem.objects.get_or_create(cart=user_cart, product=product)

            # Update the quantity in CartItem
            cart_item.quantity = quantity
            cart_item.save()

            user_cart.save()
            
        # Return the updated cart
        return self.cart


    # Define the cart length(for updating cart count)
    def __len__(self):
        return len(self.cart)
    
    
    def get_prods(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        
        # Add total price for each product based on quantity
        for product in products:
            product.quantity = self.cart[str(product.id)]  # Add quantity to product object
            if product.is_sale:  # Check if product is on sale
                product.total_price = product.sale_price * product.quantity  # Use sale price
            else:
                product.total_price = product.price * product.quantity  # Use regular price
        
        return products

    
    def get_quants(self):
        return self.cart


    def delete(self, product):
        product_id = str(product)
        # Delete from cart
        if product_id in self.cart:
            del self.cart[product_id]
            
        self.session.modified = True
        #Logged in user
        if self.request.user.is_authenticated:
            user_cart = CartModel.objects.filter(user=self.request.user).first()
            
            if user_cart:
                CartItem.objects.filter(cart=user_cart, product=product).delete()
                
                # Check if cart is empty and delete it
                if not CartItem.objects.filter(cart=user_cart).exists():
                    user_cart.delete()

    
    def order_total(self):
        total = 0
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)

        for product in products:
            quantity = self.cart[str(product.id)]
            price = product.sale_price if product.is_sale else product.price
            total += price * quantity

        return total

    
    def get_items(self):
        return self.cart  # Returns {product_id: quantity}

    def clear(self):
        # ✅ Clear session-based cart
        if 'session_key' in self.session:
            del self.session['session_key']
        self.session.modified = True  # Ensure session updates
        
        # ✅ Clear database cart for authenticated users
        if self.request.user.is_authenticated:
            user_cart = CartModel.objects.filter(user=self.request.user).first()
            
            if user_cart:
                user_cart.cart_items.all().delete()  # ✅ Remove all CartItem entries




    
    


    
    
    
    
    
    
 