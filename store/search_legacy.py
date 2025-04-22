from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from store.models import Category, Product
from django.db.models import Q

from django.db.models import Count
import random

from store.products import ProductSession


# Create your views here.

def products(request):
    products = Product.objects.all()
    context = {
        'products': products,
    }
    return render(request, 'store/products.html', context)


def product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    thumbnails = product.thumbnails.all()[:10]
    
    breadcrumbs = [('Home', reverse('home'))]
    if product.category:
        ancestors = product.category.get_ancestors(include_self=True)
        for ancestor in ancestors:
            breadcrumbs.append((ancestor.name, reverse('category', args=[ancestor.slug])))
    breadcrumbs.append((product.name, request.path))
    
    product_session = ProductSession(request)
    product_session.add_product(product.id)  

    viewed_products = product_session.get_recently_viewed_products(limit=5)  
    
    product_ids = product_session.get_product_ids() 
    viewed_products.sort(key=lambda x: product_ids.index(str(x.id)))

    context = {
        'product': product,
        'thumbnails': thumbnails,
        'breadcrumbs': breadcrumbs,
        'viewed_products': viewed_products,
    }
    return render(request, 'store/product.html', context)


def brands(request):
    products = Product.objects.select_related('category').all()  
    context = {
        'products': products
    }
    return render(request, 'store/brands.html', context)

def brand(request, brand_slug):
    products = Product.objects.filter(brand__iexact=brand_slug)
    context = {
        'products': products
    }
    return render(request, 'store/brand.html', context)


def categories(request):
    categories = Category.objects.all()
    products = Product.objects.select_related('category').all()  
    context = {
        'categories': categories,
        'products': products,
    }
    return render(request, 'store/categories.html', context)


def category(request, slug):
    # Get the current category
    category = get_object_or_404(Category, slug=slug)
    
    # Get all descendant categories (including self)
    descendants = category.get_descendants(include_self=True)
    
    # Get products from all these categories
    products = Product.objects.filter(category__in=descendants)
    
    # Build breadcrumbs
    breadcrumbs = [
        ('Home', reverse('home')),
        ('All Products', reverse('products')), 
    ]
    
    # Add ancestor categories to breadcrumbs
    for ancestor in category.get_ancestors():
        breadcrumbs.append((ancestor.name, reverse('category', args=[ancestor.slug])))
    
    # Add current category (not linked)
    breadcrumbs.append((category.name, None))
    
    context = {
        'category': category,
        'products': products,
        'breadcrumbs': breadcrumbs,
        'subcategories': category.get_children(),  # For showing subcategory list
    }
    return render(request, 'store/category.html', context)

def search(request):
    query = request.GET.get('query')
    products = Product.objects.none()
    brand_products = Product.objects.none()
    category_products = Product.objects.none()
    results_count = 0
    related_products = Product.objects.none()

    if query:
        # ---------------------------
        # 1. Category Matching (Deep)
        # ---------------------------
        # Categories matching query in name or ancestors
        matching_categories = Category.objects.filter(
            Q(name__icontains=query) | 
            Q(parent__name__icontains=query) |
            Q(parent__parent__name__icontains=query)
        ).values_list('id', flat=True)

        # ---------------------------
        # 2. Products Matching Query
        # ---------------------------
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(key_words__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(category__name__icontains=query) | 
            Q(color__icontains=query) |
            Q(category__id__in=matching_categories)
        ).select_related('category')

        results_count = products.count()

        # ---------------------------
        # 3. Brand Exact Match Section
        # ---------------------------
        brand_products = Product.objects.filter(brand__iexact=query)

        # ---------------------------
        # 4. Category Exact Match Section
        # ---------------------------
        exact_category = Category.objects.filter(name__iexact=query).first()
        if exact_category:
            descendants = exact_category.get_descendants(include_self=True)
            category_products = Product.objects.filter(category__in=descendants)

        # ---------------------------
        # 5. Related Products Section
        # ---------------------------
        if products.exists():
            related_products = Product.objects.filter(
                Q(brand__in=products.values_list('brand', flat=True)) |
                Q(category__in=products.values_list('category', flat=True))
            ).exclude(id__in=products.values_list("id", flat=True))[:12]
        else:
            related_products = Product.objects.all()[:12]

    # ---------------------------
    # Breadcrumbs
    # ---------------------------
    breadcrumbs = [
        ('Home', reverse('home')),
        ('All Products', reverse('products')),
    ]
    if query:
        breadcrumbs.append((query, None))

    # ---------------------------
    # Context
    # ---------------------------
    context = {
        'query': query,
        'products': products,  # Main listing (paginate later)
        'brand_products': brand_products,
        'category_products': category_products,
        'results_count': results_count,
        'related_products': related_products,
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'store/search.html', context)


from django.shortcuts import render
from django.urls import reverse
from .services import SearchService

def search(request):
    query = request.GET.get('query', '').strip()
    search_service = SearchService(query)
    results = search_service.execute_search()

    # Breadcrumbs
    breadcrumbs = [
        ('Home', reverse('home')),
        ('All Products', reverse('products')),
    ]
    if query:
        breadcrumbs.append((query, None))

    context = {
        'query': query,
        **results,  # Unpacking results from the search service
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'store/search.html', context)
