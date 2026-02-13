from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart_summary_view, name='cart_summary'),
    path('cart/add/', views.cart_add_view, name='cart_add'),
    path('cart/remove/', views.cart_delete_view, name='cart_remove'),
    path('cart/update/', views.cart_update_view, name='cart_update'),
]
