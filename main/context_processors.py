from store.models import Category, Product

def categories_processor(request):
    categories = Category.objects.filter(parent__isnull=True).prefetch_related("children")
    
    return {'categories': categories,}


def brand_list(request):
    brand_list = (
        Product.objects.filter(is_listed=True)
        .exclude(brand__isnull=True)
        .exclude(brand__exact='')
        .values_list('brand', flat=True)
        .distinct()
        .order_by('brand')
    )

    return {
        'brand_list': brand_list
    }





