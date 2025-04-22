from django.db import models

from store.models import Product
from users.models import CustomUser

class ShippingAddress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    full_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255, null=True, blank=True)
    zipcode = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=255)
    primary = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Shipping Addresses"

    def save(self, *args, **kwargs):
        if self.primary:
            # Unset other primary addresses for the user
            ShippingAddress.objects.filter(user=self.user, primary=True).update(primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.address1} ({'Primary' if self.primary else 'Secondary'})"


class Order(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("Pay on Delivery", "Pay on Delivery"),
        ("Card", "Card"),
        ("Mpesa", "Mpesa"),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_address = models.TextField(max_length=15000)
    date_ordered = models.DateTimeField(auto_now_add=True)
    is_shipped = models.BooleanField(default=False)
    shipped_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
   
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        import random
        import string
        from datetime import datetime

        prefix = datetime.now().strftime("%Y%m%d")  # e.g., 20250410
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"ORD-{prefix}-{suffix}"

    def __str__(self):
        return self.order_number
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} - {self.order.user.email}"