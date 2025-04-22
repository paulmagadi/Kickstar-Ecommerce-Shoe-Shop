from django.core.management.base import BaseCommand
from store.models import Product
from django.db.models import Count

class Command(BaseCommand):
    help = 'Normalize brand names by title-casing them and merging duplicates'

    def handle(self, *args, **kwargs):
        # Get all products with a non-null, non-empty brand
        products = Product.objects.exclude(brand__isnull=True).exclude(brand__exact='')

        total_updated = 0
        for product in products:
            normalized = product.brand.strip().title()
            if product.brand != normalized:
                product.brand = normalized
                product.save()
                total_updated += 1

        self.stdout.write(self.style.SUCCESS(f'Normalized {total_updated} product brand(s).'))
