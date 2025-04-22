from store.models import Product
from cart.cart import Cart
from orders.models import Order, OrderItem
from django.db import transaction

class OrderService:
    @staticmethod
    def create_order(user, shipping_address, payment_method):
        """
        Process an order and save it to the database.
        """
        cart_instance = Cart(user)  
        cart_items = cart_instance.get_prods()  
        cart_quantities = cart_instance.get_quants()
        order_total = cart_instance.order_total()

        if not cart_items:
            return None  # No items in cart

        with transaction.atomic():  # Ensures atomic DB transaction
            order = Order.objects.create(
                user=user,
                full_name=user.get_full_name(),
                email=user.email,
                amount_paid=order_total,
                shipping_address=shipping_address,
                payment_method=payment_method,
                status="Pending",
            )

            order_items = [
                OrderItem(
                    order=order,
                    product=item,
                    quantity=cart_quantities.get(item.id, 1),
                    price=item.price,
                ) for item in cart_items
            ]
            
            OrderItem.objects.bulk_create(order_items)  # Efficient bulk insert

            # Clear the cart after successful order placement
            cart_instance.clear()

        return order
