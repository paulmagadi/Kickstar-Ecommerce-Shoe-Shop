class ProductSession:
    def __init__(self, request):
        self.session = request.session
        self.request = request
        if 'viewed_products' not in self.session:
            self.session['viewed_products'] = []
    
    def add_product(self, product_id):
        product_id = str(product_id)  # Store as string for consistency
        viewed_products = self.session['viewed_products']

        if product_id in viewed_products:
            viewed_products.remove(product_id)  # Remove existing to move it to the top
        
        viewed_products.insert(0, product_id)  # Add product to the top
        self.session['viewed_products'] = viewed_products[:20]  # Limit to last 20
        self.session.modified = True  # Mark session as modified

    def get_recently_viewed_products(self, limit=5):
        from store.models import Product
        product_ids = self.session.get('viewed_products', [])[:limit]
        return list(Product.objects.filter(id__in=product_ids))

    def get_product_ids(self):
        return self.session.get('viewed_products', [])
