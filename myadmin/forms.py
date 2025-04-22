from django import forms
from store.models import Category, Product, Thumbnail
from mptt.forms import TreeNodeChoiceField


class CategoryForm(forms.ModelForm):
    parent = TreeNodeChoiceField(queryset=Category.objects.all(), required=False)

    class Meta:
        model = Category
        fields = [
            'name', 'parent', 'key_words', 'description', 'image'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'price', 'sale_price', 'description', 'key_words',
            'image', 'stock_quantity', 'brand', 'material', 'color', 'size', 
            'is_listed', 'is_featured', 'is_new'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'color': forms.TextInput(attrs={'placeholder': 'e.g. Black, White'}),
            'size': forms.TextInput(attrs={'placeholder': 'e.g. M, L, XL'}),
        }


class ThumbnailForm(forms.ModelForm):
    class Meta:
        model = Thumbnail
        fields = ['product', 'thumbnail']
