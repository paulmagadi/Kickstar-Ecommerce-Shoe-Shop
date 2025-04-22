from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.products, name='products'),
    path('products/<str:slug>', views.product, name='product'),
    path('categories/', views.categories, name='categories'),
    path('categories/<str:slug>/', views.category, name='category'),
    path('search/', views.search, name='search'),
    path('brands/', views.brands, name='brands'),
    path('brands/<slug:brand_slug>/', views.brand, name='product.brand'),
    path('recently-viewed/', views.viewed_products, name='viewed_products')
]
