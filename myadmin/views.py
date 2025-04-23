from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from myadmin.forms import CategoryForm, ProductForm
from orders.models import Order
from store.models import Category, Product, Thumbnail
from users.models import CustomUser
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import messages


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

# def stock_management(request):
#     products = Product.objects.all().order_by('-created_at')
#     listed_products = products.filter(is_listed=True)
#     products_in_stock = products.filter(in_stock=True)
#     context = {
#         'products': products[:20],
#         'listed_products': listed_products,
#         "products_in_stock": products_in_stock,
#         }
#     return render(request, 'myadmin/stock_management.html', context)

def stock_management(request):
    products = Product.objects.select_related('category').all()
    

    # Filters
    category = request.GET.get('category')
    brand = request.GET.get('brand')

    stock = request.GET.get('stock')
    is_listed = request.GET.get('is_listed')

    if category:
        selected_category = get_object_or_404(Category, slug=category)
        descendants = selected_category.get_descendants(include_self=True)
        products = products.filter(category__in=descendants)

    if brand == 'none':
        products = products.filter(brand__isnull=True)
    elif brand:
        products = products.filter(brand__iexact=brand)

    if stock == 'in':
        products = products.filter(stock_quantity__gt=0)
    elif stock == 'out':
        products = products.filter(stock_quantity__lte=0)
    elif stock == 'less':
        products = products.filter(stock_quantity__lte=4)
        
    if is_listed == 'true':
        products = products.filter(is_listed=True)
    elif is_listed == 'false':
        products = products.filter(is_listed=False)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('myadmin/partials/product-table-body.html', {'products': products})
        return JsonResponse({'html': html})

    context = {
        'products': products,
        'categories': Category.objects.all(),
        'brands': Product.objects.exclude(brand__isnull=True).values_list('brand', flat=True).distinct()
    }
    return render(request, 'myadmin/stock_management.html', context)


def customers_management(request):
    return render(request, 'myadmin/customers.html')

def orders_management(request):
    return render(request, 'myadmin/orders.html')

def analytics(request):
    return render(request, 'myadmin/analytics.html')


def product_list(request):
    products = Product.objects.select_related('category').all().order_by('-created_at')

    # Filters
    category = request.GET.get('category')
    brand = request.GET.get('brand')

    stock = request.GET.get('stock')
    is_listed = request.GET.get('is_listed')

    if category:
        products = products.filter(category__slug=category)

    if brand == 'none':
        products = products.filter(brand__isnull=True)
    elif brand:
        products = products.filter(brand__iexact=brand)

    if stock == 'in':
        products = products.filter(stock_quantity__gt=0)
    elif stock == 'out':
        products = products.filter(stock_quantity__lte=0)
    elif stock == 'less':
        products = products.filter(stock_quantity__lte=4)
        
    if is_listed == 'true':
        products = products.filter(is_listed=True)
    elif is_listed == 'false':
        products = products.filter(is_listed=False)
        

    context = {
        'products': products,
        'categories': Category.objects.all(),
        'brands': Product.objects.exclude(brand__isnull=True).values_list('brand', flat=True).distinct()
        
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
    categories = Category.objects.all()
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        thumbnails = request.FILES.getlist('thumbnails')

        if form.is_valid():
            product = form.save()  # Save the product first

            # Save thumbnails if any
            for thumb in thumbnails:
                Thumbnail.objects.create(product=product, thumbnail=thumb)

            return redirect('product_list')
    else:
        form = ProductForm()
    category_form = CategoryForm()
    
    context = {
        'form': form, 
        'category_form': category_form, 
        "categories": categories,
        }
    return render(request, 'myadmin/forms/add-product.html', context)

def update_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    thumbnails = Thumbnail.objects.filter(product=product)
    categories = Category.objects.all()
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        thumbnails = request.FILES.getlist('thumbnails')

        if form.is_valid():
            product = form.save()  # Save the updated product info

            # Save new thumbnails if any
            for thumb in thumbnails:
                Thumbnail.objects.create(product=product, thumbnail=thumb)

            return redirect('product_list')
    else:
        form = ProductForm(instance=product)  

    category_form = CategoryForm()  # for the popup modal
    context = {
        'form': form,
        'category_form': category_form,
        'product': product,
        'thumbnails': thumbnails,
        'categories': categories,
    }
    return render(request, 'myadmin/forms/update-product.html', context)

def delete_thumbnail(request, id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    thumbnail = get_object_or_404(Thumbnail, id=id)
    product_slug = thumbnail.product.slug  

    thumbnail.delete()
    
    return redirect('update_product', slug=product_slug)


def delete_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted successfully.")
    else:
        messages.warning(request, "Invalid request method.")
    
    return redirect('product_list')

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
        return redirect('category_list')
    
    categories = Category.objects.all()  
    context = {
        'form': form,
        'categories': categories,
    }
    return render(request, 'myadmin/forms/add-category.html', context)

def update_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    form = CategoryForm(request.POST or None, request.FILES or None, instance=category)
    if form.is_valid():
        form.save()
        return redirect('category_list')
    
    categories = Category.objects.all()
    context = {
        'form': form,
        'category': category,
        'categories': categories,
    }
    return render(request, 'myadmin/forms/update-category.html', context)


def delete_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Category deleted successfully.")
    else:
        messages.warning(request, "Invalid request method.")
    
    return redirect('category_list')



def category_delete_preview(request, slug):
    category = get_object_or_404(Category, slug=slug)
    sub_categories = category.get_descendants()
    products = Product.objects.filter(category__in=[category] + list(sub_categories))

    html = render_to_string('myadmin/partials/category-delete-preview.html', {
        'category': category,
        'sub_categories': sub_categories,
        'products': products,
    })
    return HttpResponse(html)


