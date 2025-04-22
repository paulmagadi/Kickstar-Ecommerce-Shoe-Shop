from django.shortcuts import render

from store.models import Category, Product
from django.db.models import Max, Q

# Create your views here.
def home(request):
    products = Product.objects.all()
    featured_products = products.filter(is_featured=True, in_stock=True)[:12]
    sale_products = products.filter(is_sale=True, in_stock=True)[:12]
    new_products = products.filter(is_new=True, in_stock=True)[:12] 
    main_categories = Category.objects.filter(parent=None)[:5]
    
    # category_products = {}

    # for category in main_categories:
    #     subcategories = category.get_descendants(include_self=True)
    #     category_products[category] = Product.objects.filter(category__in=subcategories, in_stock=True)[:12]
    
    category_products = {}
    category_discounts = {}

    for category in main_categories:
        subcategories = category.get_descendants(include_self=True)
        product_qs = Product.objects.filter(category__in=subcategories, in_stock=True)

        category_products[category] = product_qs[:12]

        # Get max discount for the category
        max_discount = product_qs.aggregate(Max('percentage_discount'))['percentage_discount__max'] or 0
        category_discounts[category.id] = round(max_discount)
    
    highest_discount = Product.objects.aggregate(Max('percentage_discount'))['percentage_discount__max']
    highest_discount_new = new_products.aggregate(Max('percentage_discount'))['percentage_discount__max']
    highest_discount_featured = featured_products.aggregate(Max('percentage_discount'))['percentage_discount__max']
    
    context = {
        'products': products,
        'featured_products': featured_products,
        'sale_products': sale_products,
        'new_products': new_products,
        'main_categories': main_categories,
        'category_products': category_products,
        'category_discounts': category_discounts,
        'highest_discount': highest_discount or 0,  
        'highest_discount_new': highest_discount_new or 0,  
        'highest_discount_featured': highest_discount_featured or 0,  
    }
    return render(request, 'main/index.html', context)