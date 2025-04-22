from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('stock-management', views.stock_management, name='stock_management'),
    path('customers', views.customers_management, name='customers_management'),
    path('orders', views.orders_management, name='orders_management'),
    path('analytics', views.analytics, name='analytics'),
    path('products', views.products_list, name='products_list'),
    path('categories', views.categories_list, name='categories_list'),
    path('product/add/', views.add_product, name='add_product'),
    # path('myadmin/add-category/', views.add_category_ajax, name='add_category_ajax'),
    path('category/add/', views.add_category, name='add_category'), 
    path('category/add-popup/', views.CategoryAddPopupView.as_view(), name='category_add_popup'),
]