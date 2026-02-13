app_name = "orders"

from django.urls import path
from . import views

urlpatterns = [
    path("check-out/", views.checkout_shipping_info_view, name="checkout"),
    path("payment/", views.payment_info_view, name="payment_info"),
    path("checkout-review/", views.review_order_view, name="checkout_review"),
    path("checkout-confirmation/", views.place_order_view, name="place_order"),
    path(
        "payment/confirm/<int:order_id>/",
        views.payment_confirm_view,
        name="payment_confirm",
    ),
    path("delivery-method/", views.shipping_method_view, name="shipping_method"),
]
