from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # -----------------------------------------------------
    # CART
    # -----------------------------------------------------
    path(
        "cart/",
        views.cart_summary_view,
        name="cart-summary",
    ),
    path(
        "cart/add/",
        views.cart_add_view,
        name="cart-add",
    ),
    path(
        "cart/add-product/",
        views.product_cart_add_view,
        name="product-cart-add",
    ),
    path(
        "cart/update/",
        views.cart_update_view,
        name="cart-update",
    ),
    path(
        "cart/delete/",
        views.cart_delete_view,
        name="cart-delete",
    ),
    # -----------------------------------------------------
    # CHECKOUT
    # -----------------------------------------------------
    path(
        "check-out/",
        views.checkout_view,
        name="checkout",
    ),
    path(
        "checkout-review/",
        views.review_order_view,
        name="checkout_review",
    ),
    path(
        "delivery-method/",
        views.delivery_method_view,
        name="delivery_method",
    ),
    path(
        "payment/",
        views.payment_method_view,
        name="payment",
    ),
    path(
        "payment/flutterwave/",
        views.flutterwave_payment_view,
        name="flutterwave_payment",
    ),
    path(
        "payment/flutterwave/callback/",
        views.flutterwave_callback_view,
        name="flutterwave_callback",
    ),
    path(
        "payment/nowpayments/",
        views.nowpayments_payment_view,
        name="nowpayments_payment",
    ),
    path(
        "payment/nowpayments/ipn/",
        views.nowpayments_ipn,
        name="nowpayments_ipn",
    ),
    path(
        "payment/nowpayments/success/<int:order_id>/",
        views.nowpayments_success_view,
        name="nowpayments_success",
    ),
    path(
        "payment/nowpayments/cancel/<int:order_id>/",
        views.nowpayments_cancel_view,
        name="nowpayments_cancel",
    ),
]
