import re
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from store.models import Category, Product
from django.db.models import Q
from django.db.models import Max
from django.db.models import Count
import random

from store.products import ProductSession
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Prefetch


# Create your views here.

def products(request):
    products = Product.objects.all()
    list_products = list(Product.objects.all())
    
    paginator = Paginator(list_products, 15)
    products_count = products.count()

    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
        
    breadcrumbs = [
        ('Home', reverse('home')),
        ('Products', None),  # Current page, not linked
    ]
        
    context = {
        'products': products,
        'breadcrumbs': breadcrumbs,
        'products_count': products_count
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
    
     # Related products logic
    related_products = Product.objects.filter(
        Q(category=product.category) | Q(brand__iexact=product.brand),
        is_listed=True
    ).exclude(id=product.id).distinct().order_by('?')[:12]  

    '''We use sessions to track viewed products'''
    product_session = ProductSession(request)
    product_session.add_product(product.id)  

    viewed_products = product_session.get_recently_viewed_products(limit=12)  
    
    product_ids = product_session.get_product_ids() 
    viewed_products.sort(key=lambda x: product_ids.index(str(x.id)))
    
    # ❌ Remove current product from the viewed list
    viewed_products = [p for p in viewed_products if p.id != product.id]

    context = {
        'product': product,
        'thumbnails': thumbnails,
        'breadcrumbs': breadcrumbs,
        'related_products': related_products,
        'viewed_products': viewed_products,
    }
    return render(request, 'store/product.html', context)

def viewed_products(request):
    #  Sessions for recently viewed 
    product_session = ProductSession(request)
    viewed_products = product_session.get_recently_viewed_products(limit=60)
    product_ids = product_session.get_product_ids()
    products = list(viewed_products)
    products.sort(key=lambda x: product_ids.index(str(x.id)))
    
    
    paginator = Paginator(products, 15)  
    page = request.GET.get('page')

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
        
    breadcrumbs = [
        ('Home', reverse('home')),
        ('Products', reverse('products')),
        ('Recently Viewed Products', None),  # Current page, not linked
    ]
    
    context = {
        'products': page_obj,
        'products_count': paginator.count,
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'store/recently-viewed-products.html', context)


from django.db.models import Count, Max
from django.urls import reverse
from django.shortcuts import render
from store.models import Product

def brands(request): 
    # Get all distinct non-null brands with a count of listed products
    raw_brands = (
        Product.objects.filter(is_listed=True)
        .exclude(brand__isnull=True)
        .exclude(brand__exact='')
        .values('brand')
        .annotate(product_count=Count('id'))
        .order_by('brand')
    )

    # Now enrich each brand with a list of up to 12 products and the max discount
    brand_sections = []
    for item in raw_brands:
        brand_name = item['brand']
        brand_products = Product.objects.filter(
            is_listed=True,
            brand__iexact=brand_name
        )

        products = brand_products[:12]

        # Get the max discount for this brand
        highest_discount = brand_products.aggregate(Max('percentage_discount'))['percentage_discount__max'] or 0

        brand_sections.append({
            'name': brand_name,
            'product_count': item['product_count'],
            'products': products,
            'highest_discount': round(highest_discount)
        })

    breadcrumbs = [
        ('Home', reverse('home')),
        ('Brands', None),
    ]

    context = {
        'brands': brand_sections,
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'store/brands.html', context)


def brand(request, brand_slug):
    products = Product.objects.filter(is_listed=True, brand__iexact=brand_slug)
    list_products = list(Product.objects.filter(is_listed=True, brand__iexact=brand_slug))
    
    paginator = Paginator(list_products, 15)  
    page = request.GET.get('page')

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
        
    breadcrumbs = [
        ('Home', reverse('home')),
        ('Brands', reverse('brands')),  
        (brand_slug.title(), None), 
    ]
    highest_discount = products.aggregate(Max('percentage_discount'))['percentage_discount__max']
    context = {
        'brand': brand_slug,
        'products': page_obj,
        'breadcrumbs': breadcrumbs,
        'product_count': paginator.count,
        'highest_discount': highest_discount or 0,
    }
    return render(request, 'store/brand.html', context)


def categories(request):
    products = Product.objects.filter(is_listed=True)
    
    # Get categories with listed products
    category_ids = products.values_list('category', flat=True).distinct()
    categories = Category.objects.filter(id__in=category_ids)

    # Optionally include ancestors of those categories (for full tree display)
    full_category_set = Category.objects.none()
    for cat in categories:
        full_category_set |= cat.get_ancestors(include_self=True)
    categories = full_category_set.distinct()
    
    # category products 
    category_products = {}
    category_discounts = {}

    for category in categories:
        subcategories = category.get_descendants(include_self=True)
        product_qs = Product.objects.filter(category__in=subcategories, in_stock=True)

        category_products[category] = product_qs[:12] # Use to render products in the specific category

        # Get max discount for the category
        max_discount = product_qs.aggregate(Max('percentage_discount'))['percentage_discount__max'] or 0
        category_discounts[category.id] = round(max_discount)

    # Breadcrumbs and discounts]
    breadcrumbs = [
        ('Home', reverse('home')),
        ('Categories', reverse('categories')),
    ]

    context = {
        'categories': categories,
        'breadcrumbs': breadcrumbs,
        'category_discounts': category_discounts,
    }
    return render(request, 'store/categories.html', context)



def category(request, slug):
    # Get the current category
    category = get_object_or_404(Category, slug=slug)
    
    main_categories = Category.objects.filter(parent=None)
    
    # Get all descendant categories (including self)
    all_descendants = category.get_descendants(include_self=True)
    
    # Get products from all these categories
    products = Product.objects.filter(is_listed=True, category__in=all_descendants)
    
    # Get the biggest discount from all the produsts in the entire category tree 
    category_discounts = products.aggregate(Max('percentage_discount'))['percentage_discount__max']
   
   # Get products in the category
    direct_products = list(Product.objects.filter(is_listed=True, category=category))
    # Get products from the descendant categories in the tree
    tree_products_list = list(Product.objects.filter(is_listed=True, category__in=all_descendants).exclude(id__in=[p.id for p in direct_products]))
    # Check if there are atleast 12 items in the main category. If not fill the remaining with products from the tree 
    
    if len(direct_products) >= 12:
        display_products = direct_products
    else:
        remaining_count = 12 - len(direct_products)
        display_products = direct_products + tree_products_list[:remaining_count]
        

 
    # Get other products if there is no product in all these categories
    if not products.exists():
        fallback_products = Product.objects.filter(is_listed=True).order_by('?')[:12]  
    else:
        fallback_products = None

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
    
    # children of the category
    descendants = category.get_descendants(include_self=False)
    descendant_category_discounts = {}
    for child in descendants:
        # Products listed in this descendant category or its subcategories
        sub_descendants = child.get_descendants(include_self=True)
        sub_products = Product.objects.filter(is_listed=True, category__in=sub_descendants)

        max_discount = sub_products.aggregate(Max('percentage_discount'))['percentage_discount__max'] or 0
        descendant_category_discounts[child.id] = round(max_discount)
  
  
    paginator = Paginator(display_products, 15)  
    page = request.GET.get('page')

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
        
        
    paginator = Paginator(direct_products, 15)  
    page = request.GET.get('page')

    try:
        page_obj_1 = paginator.page(page)
    except PageNotAnInteger:
        page_obj_1 = paginator.page(1)
    except EmptyPage:
        page_obj_1 = paginator.page(paginator.num_pages)
        
    context = {
        'category': category,
        'main_categories': main_categories,
        'products': page_obj_1,
        'breadcrumbs': breadcrumbs,
        'subcategories': category.get_children(),  
        'fallback_products': fallback_products,
        'display_products': page_obj,
        'direct_products': direct_products,
        'category_discounts': category_discounts or 0,
        'descendant_category_discounts': descendant_category_discounts or 0,
    }
    return render(request, 'store/category.html', context)


def search(request):
    query = request.GET.get('query', '').strip()
    normalized_query = re.sub(r'\s+', ' ', query.lower())  
    products = Product.objects.none()
    results_count = 0
    fallback_products = Product.objects.all()[:12]

    if query:
        keywords = normalized_query.split()
        search_q = Q()

        for word in keywords:
            search_q |= Q(name__icontains=word)
            search_q |= Q(description__icontains=word)
            search_q |= Q(brand__icontains=word)
            search_q |= Q(category__name__icontains=word)
            search_q |= Q(color__icontains=word)
            search_q |= Q(key_words__icontains=word)

        # 3. Search products matching the query
        products = Product.objects.filter(search_q, is_listed=True).select_related('category')
        results_count = products.count()
        
        query_products = list(Product.objects.filter(search_q, is_listed=True).select_related('category'))
        
    paginator = Paginator(query_products, 15)  
    page = request.GET.get('page')

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
        
    #    Sessions for recently viewed 
    product_session = ProductSession(request)
    viewed_products = product_session.get_recently_viewed_products(limit=12)
    product_ids = product_session.get_product_ids()
    viewed_products = list(viewed_products)
    viewed_products.sort(key=lambda x: product_ids.index(str(x.id)))
        
    # Breadcrumbs
    breadcrumbs = [
        ('Home', reverse('home')),
        ('All Products', reverse('products')),
    ]
    if query:
        breadcrumbs.append((query, None))

    context = {
        'query': query,
        'products': page_obj,
        'results_count': results_count,
        'viewed_products': viewed_products,
        'breadcrumbs': breadcrumbs,
        'fallback_products': fallback_products,
    }
    return render(request, 'store/search.html', context)
