from django.contrib import admin
from .models import Category, Product, Thumbnail
from mptt.admin import DraggableMPTTAdmin

@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    mptt_indent_field = "name"
    list_display = ('tree_actions', 'indented_title', 'slug')
    prepopulated_fields = {'slug': ('name',)}

class ProductImageInline(admin.TabularInline):
    model = Thumbnail
    extra = 0

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    list_display = ('name', 'price', 'is_sale', 'stock_quantity', 'is_listed', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

admin.site.register(Product, ProductAdmin)