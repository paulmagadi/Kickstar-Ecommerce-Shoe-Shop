from django.urls import path
from . import views

urlpatterns = [
    path('shipping-address/', views.shipping_address, name='shipping_address'),
    path('create_order/', views.create_order, name='create_order'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('orders/', views.orders, name='orders'),
    path('orders/order-details/', views.order, name='order'),
    path('set-order-session/', views.set_order_session, name='set_order_session'),

]