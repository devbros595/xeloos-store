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
        views.checkout_shipping_info_view,
        name="checkout",
    ),

    path(
        "payment/",
        views.payment_info_view,
        name="payment_info",
    ),

    path(
        "checkout-review/",
        views.review_order_view,
        name="checkout_review",
    ),

    path(
        "checkout-confirmation/",
        views.place_order_view,
        name="place_order",
    ),

    path(
        "payment/confirm/<int:order_id>/",
        views.payment_confirm_view,
        name="payment_confirm",
    ),

    path(
        "delivery-method/",
        views.shipping_method_view,
        name="shipping_method",
    ),
]