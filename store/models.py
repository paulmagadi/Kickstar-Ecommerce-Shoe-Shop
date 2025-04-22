from django.db import models
from datetime import timedelta
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.apps import apps
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils import timezone
from PIL import Image
from django.templatetags.static import static
from mptt.models import MPTTModel, TreeForeignKey

class Category(MPTTModel):
    name = models.CharField(max_length=50)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    slug = models.SlugField(unique=True, blank=True)
    key_words = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='uploads/categories/', blank=True, null=True)
    
    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        unique_together = ('parent', 'name')  # 👈 This ensures same name can't appear under same parent
        verbose_name_plural = 'Categories'
        
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


    def get_full_path(self):
        """Builds the full category path: Home > Footwear > Men's Shoes > Sneakers"""
        ancestors = self.get_ancestors(include_self=True)
        return " > ".join([category.name for category in ancestors])

    def __str__(self):
        return self.get_full_path()
      
    @property
    def imageURL(self):
        if self.image:
            return self.image.url
        return static('images/brand/holder2.png')
                

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', blank=True, null=True)
    name = models.CharField(max_length=255, verbose_name='Product Name')
    slug = models.SlugField(unique=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    image =  models.ImageField(upload_to='uploads/products', null=True, blank=True)
    description = models.TextField(verbose_name='Product Description', blank=True, null=True)
    key_words = models.CharField(max_length=255, blank=True, null=True)
    is_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(default=0, max_digits=9, decimal_places=2, null=True, blank=True)
    percentage_discount = models.DecimalField(default=0, max_digits=5, decimal_places=0, null=True, blank=True)
    is_listed = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(default=1)
    brand = models.CharField(max_length=255, blank=True, null=True)
    material = models.CharField(max_length=255, blank=True, null=True)
    color = models.CharField(max_length=255, blank=True)
    size = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.stock_quantity < 0:
            raise ValidationError({'stock_quantity': 'Stock quantity cannot be less than 0'})

    def save(self, *args, **kwargs):
        is_new_instance = self.pk is None  
    
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs) 

        if is_new_instance:  
            self.is_new = (timezone.now() - self.created_at) <= timedelta(days=30)
            super().save(update_fields=['is_new'])  

        self.in_stock = self.stock_quantity > 0
        if self.stock_quantity <= 0:
            self.is_listed = False

        if self.sale_price:
            self.is_sale = True
        else:
            self.is_sale = False

        if self.is_sale and self.sale_price and self.sale_price < self.price:
            self.discount = round(self.price - self.sale_price, 2)
            self.percentage_discount = round((self.discount / self.price) * 100)
        else:
            self.discount = 0
            self.percentage_discount = 0
            
        if self.brand:
            self.brand = self.brand.strip().title()  # or .lower() for lowercase

        super().save(update_fields=['in_stock', 'is_listed', 'is_sale', 'discount', 'percentage_discount', 'brand']) 


    @property
    def imageURL(self):
        if self.image:
            return self.image.url
        return static('images/brand/holder2.png')
    

@receiver(pre_save, sender=Category)
@receiver(pre_save, sender=Product)
def resize_image(sender, instance, **kwargs):
    if instance.image:
        try:
            img = Image.open(instance.image)
            if img.height > 1125 or img.width > 1125:
                img.thumbnail((1125, 1125))
                img.save(instance.image.path, quality=70, optimize=True)
        except Exception as e:
            print(f"Error resizing product image: {e}")   
            
class Thumbnail(models.Model):
    product = models.ForeignKey(Product, default=None, on_delete=models.CASCADE, related_name='thumbnails')
    thumbnail = models.ImageField(upload_to='uploads/products', null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Thumbnails'

    def __str__(self):
        return self.product.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def imageURL(self):
        try:
            url = self.thumbnail.url
        except:
            url = ''
        return url
    
@receiver(pre_save, sender=Thumbnail)
def resize_thumbnail(sender, instance, **kwargs):
    if instance.thumbnail:
        try:
            img = Image.open(instance.thumbnail)
            if img.height > 1125 or img.width > 1125:
                img.thumbnail((1125, 1125))
                img.save(instance.thumbnail.path, quality=70, optimize=True)
        except Exception as e:
            print(f"Error resizing thumbnail: {e}")


    
