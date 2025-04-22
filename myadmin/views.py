from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from myadmin.forms import CategoryForm, ProductForm
from orders.models import Order
from store.models import Category, Product, Thumbnail
from users.models import CustomUser
from django.utils.http import url_has_allowed_host_and_scheme



def dashboard(request):
    products = Product.objects.all()
    products_in_stock = Product.objects.filter(in_stock=True)
    customers = CustomUser.objects.all()
    orders = Order.objects.all()
    context = {
        'products': products,
        'products_in_stock': products_in_stock,
        'customers': customers,
        'orders': orders,
    }
    return render(request, 'myadmin/dashboard.html', context)

def stock_management(request):
    products = Product.objects.all().order_by('-created_at')
    listed_products = products.filter(is_listed=True)
    products_in_stock = products.filter(in_stock=True)
    context = {
        'products': products[:20],
        'listed_products': listed_products,
        "products_in_stock": products_in_stock,
        }
    return render(request, 'myadmin/stock_management.html', context)

def customers_management(request):
    return render(request, 'myadmin/customers.html')

def orders_management(request):
    return render(request, 'myadmin/orders.html')

def analytics(request):
    return render(request, 'myadmin/analytics.html')

def product_list(request):
    products = Product.objects.all().order_by('-created_at')
    context = {
        'products': products,
    }
    return render(request, 'myadmin/product-list.html', context)

def product_item(request, slug):
    product = get_object_or_404(Product, slug=slug)
    context = {
        'product': product,
    }
    return render(request, 'myadmin/product-item.html', context)


def category_list(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'myadmin/category-list.html', context)

def category_products_list(request, slug):
    category = get_object_or_404(Category, slug=slug)
    # Get all descendant categories (including self)
    all_descendants = category.get_descendants(include_self=True)
    
    # Get products from all these categories
    products = Product.objects.filter(is_listed=True, category__in=all_descendants)
    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'myadmin/category-products-list.html', context)


def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        thumbnails = request.FILES.getlist('thumbnails')

        if form.is_valid():
            product = form.save()  # Save the product first

            # Save thumbnails if any
            for thumb in thumbnails:
                Thumbnail.objects.create(product=product, thumbnail=thumb)

            return redirect('stock_management')
    else:
        form = ProductForm()
    category_form = CategoryForm()
        
    return render(request, 'myadmin/forms/add-product.html', {'form': form, 'category_form': category_form,})

def update_product(request, slug):
    product = get_object_or_404(Product, slug=slug)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        thumbnails = request.FILES.getlist('thumbnails')

        if form.is_valid():
            product = form.save()  # Save the updated product info

            # Save new thumbnails if any
            for thumb in thumbnails:
                Thumbnail.objects.create(product=product, thumbnail=thumb)

            return redirect('stock_management')
    else:
        form = ProductForm(instance=product)  

    category_form = CategoryForm()  # for the popup modal
    context = {
        'form': form,
        'category_form': category_form,
        'product': product,
    }
    return render(request, 'myadmin/forms/update-product.html', context)

    

from django.http import JsonResponse
from django.views.generic import View
from django.template.loader import render_to_string

class CategoryAddPopupView(View):
    def get(self, request):
        categories = Category.objects.all()
        form_html = render_to_string('category_popup_form.html', {
            'categories': categories
        })
        return JsonResponse({'form': form_html})

    def post(self, request):
        name = request.POST.get('name')
        parent_id = request.POST.get('parent')
        description = request.POST.get('description')
        
        try:
            parent = Category.objects.get(id=parent_id) if parent_id else None
            category = Category.objects.create(
                name=name,
                parent=parent,
                description=description,
                image=request.FILES.get('image')
            )
            return JsonResponse({
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'full_path': category.get_full_path()
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


def add_category(request):
    form = CategoryForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('stock_management')
    return render(request, 'myadmin/forms/add-category.html', {'form': form})