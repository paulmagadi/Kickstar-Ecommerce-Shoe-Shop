import json
from django.conf import settings
from cart.models import CartItem, Cart as CartModel
from store.models import Product
from users.models import CustomUser, Profile
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

    
    
    # def db_add(self, product, quantity):
    #     product_id = str(product.id)  # Ensure it's the product ID as a string
    #     product_qty = int(quantity)   # Ensure quantity is an integer

    #     # Add the product to the session-based cart
    #     if product_id in self.cart:
    #         self.cart[product_id] += product_qty
    #     else:
    #         self.cart[product_id] = product_qty

    #     self.session.modified = True

    #     # Store in the database for logged-in users
    #     if self.request.user.is_authenticated:
    #         user_cart, created = CartModel.objects.get_or_create(user=self.request.user)

    #         # Update CartItem table
    #         cart_item, created = CartItem.objects.get_or_create(cart=user_cart, product=product)
    #         cart_item.quantity = self.cart[product_id]  # Update quantity in DB
    #         cart_item.save()
    
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

            
# def clear(self):
#         # ✅ Clear session-based cart
#         for key in list(self.session.keys()):
#             if key == "session_key":
#                 del self.session[key]
        
#         # ✅ Clear database cart for authenticated users
#         if self.request.user.is_authenticated:
#             user_cart = CartModel.objects.filter(user=self.request.user).first()
            
#             if user_cart:
#                 user_cart.cart_items.all().delete()  # ✅ Remove all CartItem entries


    
    


    
    
    
    
    
    
    
# def oxford_comma(items):
#     """Helper function for Oxford comma formatting"""
#     if len(items) == 0:
#         return ""
#     if len(items) == 1:
#         return items[0]
#     if len(items) == 2:
#         return f"{items[0]} and {items[1]}"
#     return ", ".join(items[:-1]) + f", and {items[-1]}"

# def cart(request):
#     cart_instance = Cart(request)
#     cart_items = cart_instance.get_prods()
#     cart_quantities = cart_instance.get_quants()
    
#     stock_updates = {
#         'removed_items': [],
#         'updated_items': []
#     }

#     for item in cart_items:
#         product = Product.objects.get(id=item.id)
#         cart_quantity = cart_quantities.get(str(item.id), 0)

#         if product.stock_quantity == 0:
#             cart_instance.delete(item.id)
#             stock_updates['removed_items'].append(product.name)
#         elif cart_quantity > product.stock_quantity:
#             cart_instance.update(request=request, product=product, quantity=product.stock_quantity)
#             stock_updates['updated_items'].append({
#                 'name': product.name,
#                 'quantity': product.stock_quantity
#             })

#     # Flash messages
#     if stock_updates['removed_items']:
#         if len(stock_updates['removed_items']) == 1:
#             messages.warning(request, 
#                 f"⚠️ {stock_updates['removed_items'][0]} is out of stock and has been removed.")
#         else:
#             messages.warning(request,
#                 f"⚠️ These items are out of stock and have been removed: {oxford_comma(stock_updates['removed_items'])}")

#     if stock_updates['updated_items']:
#         if len(stock_updates['updated_items']) == 1:
#             item = stock_updates['updated_items'][0]
#             messages.info(request,
#                 f"↻ {item['name']} quantity adjusted to {item['quantity']}")
#         else:
#             primary_items = stock_updates['updated_items'][:2]
#             primary_msg = ", ".join([f"{item['name']} (→{item['quantity']})" 
#                                    for item in primary_items])
            
#             if len(stock_updates['updated_items']) > 2:
#                 extra_count = len(stock_updates['updated_items']) - 2
#                 messages.info(request,
#                     f"↻ Adjusted quantities: {primary_msg} and {extra_count} other item{'s' if extra_count > 1 else ''}")
#             else:
#                 messages.info(request,
#                     f"↻ Adjusted quantities: {primary_msg}")


#     # # Add flash messages based on updates
#     # if stock_updates['removed_items']:
#     #     items_list = ", ".join(stock_updates['removed_items'])
#     #     messages.warning(request, f"These items are out of stock and were removed: {items_list}")
    
#     # if stock_updates['updated_items']:
#     #     for item in stock_updates['updated_items']:
#     #         messages.warning(request, 
#     #             f"Stock updated: {item['name']} quantity reduced to {item['quantity']} (max available)")

#     # Recalculate totals after potential updates
#     cart_items = cart_instance.get_prods()  # Refresh after possible deletions
#     cart_quantities = cart_instance.get_quants()
#     total_quantity = sum(cart_quantities.values())
#     order_total = cart_instance.order_total()

#     # Get related products
#     cart_product_ids = [item.id for item in cart_items]
    
#     if cart_product_ids:
#         related_products = Product.objects.filter(
#             Q(brand__in=Product.objects.filter(id__in=cart_product_ids).values_list('brand', flat=True)) |
#             Q(category__in=Product.objects.filter(id__in=cart_product_ids).values_list('category', flat=True))
#         ).exclude(id__in=cart_product_ids).distinct()[:12]
#     else:
#         all_product_ids = list(Product.objects.values_list("id", flat=True))
#         random_ids = random.sample(all_product_ids, min(len(all_product_ids), 12))
#         related_products = Product.objects.filter(id__in=random_ids)

#     context = {
#         'cart_items': cart_items,
#         'cart_quantities': cart_quantities,
#         'total_quantity': total_quantity,
#         'order_total': order_total,
#         'related_products': related_products,
#     }
#     return render(request, 'cart/cart.html', context)