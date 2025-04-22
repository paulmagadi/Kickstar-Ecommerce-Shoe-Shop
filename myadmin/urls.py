from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('stock-management', views.stock_management, name='stock_management'),
    path('customers', views.customers_management, name='customers_management'),
    path('orders', views.orders_management, name='orders_management'),
    path('analytics', views.analytics, name='analytics'),
    path('products', views.product_list, name='product_list'),
    path('products/<str:slug>/', views.product_item, name='product_item'),
    path('categories', views.category_list, name='category_list'),
    path('categories/<str:slug>/', views.category_products_list, name='category_products_list'),
    path('product/add/', views.add_product, name='add_product'),
    path('product/update/<str:slug>/', views.update_product, name='update_product'),
    # path('myadmin/add-category/', views.add_category_ajax, name='add_category_ajax'),
    path('category/add/', views.add_category, name='add_category'), 
    path('category/add-popup/', views.CategoryAddPopupView.as_view(), name='category_add_popup'),
]