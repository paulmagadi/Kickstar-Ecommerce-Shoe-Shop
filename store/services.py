import re
from django.db.models import Q
from .models import Product, Category

class SearchService:
    def __init__(self, query):
        self.query = query.strip()
        self.normalized_query = re.sub(r'\s+', ' ', self.query.lower())  # Normalize query
        self.keywords = self.normalized_query.split()
        self.products = Product.objects.none()
        self.brand_products = Product.objects.none()
        self.category_products = Product.objects.none()
        self.related_products = Product.objects.none()
        self.results_count = 0
        self.matched_brand = None
        self.exact_category = None

    def search_products(self):
        """Search products matching the query across multiple fields."""
        search_q = Q()
        for word in self.keywords:
            search_q |= Q(name__icontains=word)
            search_q |= Q(description__icontains=word)
            search_q |= Q(brand__icontains=word)
            search_q |= Q(category__name__icontains=word)
            search_q |= Q(color__icontains=word)
            search_q |= Q(key_words__icontains=word)

        self.products = Product.objects.filter(search_q).select_related('category')
        self.results_count = self.products.count()

    def find_brand_match(self):
        """Detect if the query contains a brand name."""
        all_brands = Product.objects.values_list('brand', flat=True).distinct()
        for brand in all_brands:
            if brand and brand.lower() in self.normalized_query:
                self.matched_brand = brand
                break

        if self.matched_brand:
            self.brand_products = Product.objects.filter(brand__iexact=self.matched_brand)

    def find_category_match(self):
        """Detect if the query contains a category name."""
        categories = Category.objects.all()
        for cat in categories:
            if cat.name.lower() in self.normalized_query:
                self.exact_category = cat
                break

        if self.exact_category:
            descendants = self.exact_category.get_descendants(include_self=True)
            self.category_products = Product.objects.filter(category__in=descendants)

    def get_related_products(self):
        """Fetch related products based on matched categories and brands."""
        if self.products.exists():
            self.related_products = Product.objects.filter(
                Q(brand__in=self.products.values_list('brand', flat=True)) |
                Q(category__in=self.products.values_list('category', flat=True))
            ).exclude(id__in=self.products.values_list("id", flat=True))[:12]
        else:
            self.related_products = Product.objects.all()[:12]

    def execute_search(self):
        """Run the entire search pipeline."""
        self.search_products()
        self.find_brand_match()
        self.find_category_match()
        self.get_related_products()

        return {
            'products': self.products,
            'brand_products': self.brand_products,
            'category_products': self.category_products,
            'related_products': self.related_products,
            'results_count': self.results_count,
            'matched_brand': self.matched_brand,
            'exact_category': self.exact_category,
        }
