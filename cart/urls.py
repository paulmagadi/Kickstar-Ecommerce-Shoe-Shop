from django.urls import path
from . import views


urlpatterns = [
    path('cart/', views.cart, name='cart'),
    path('cart/add/', views.add_to_cart, name='cart_add'),
    path('cart/delete/', views.cart_delete, name='cart_delete'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('checkout/', views.checkout, name='checkout'),
]
