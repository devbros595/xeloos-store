from django.urls import path
from . import views

urlpatterns = [
    path("", views.cart_summary_view, name="cart-summary"),

    path(
        "add/",
        views.cart_add_view,
        name="cart_add",
    ),

    path(
        "product/add/",
        views.product_add_view,
        name="product_add",
    ),

    path(
        "remove/",
        views.cart_delete_view,
        name="cart_remove",
    ),

    path(
        "update/",
        views.cart_update_view,
        name="cart_update",
    ),
]