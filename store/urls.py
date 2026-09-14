from django.urls import path
from . import views

urlpatterns = [
    # =========================================================
    # HOME
    # =========================================================
    path("", views.index, name="index"),

    # =========================================================
    # STORE
    # =========================================================

    # Main country/category selection page
    path(
        "xeloos-store/catalogue/",
        views.store_category,
        name="store-category",
    ),

    # Physical SIMs by country
    path(
        "xeloos-store/catalogue/<slug:slug>/",
        views.physicalSim_store,
        name="physical-sim-store",
    ),

    # eSIMs by country
    path(
        "xeloos-store/esim/<slug:slug>/",
        views.eSIM_store,
        name="esim-country-store",
    ),

    # Digital product categories
    path(
        "xeloos-store/<slug:slug>/",
        views.category_products,
        name="category-products",
    ),

    # Individual digital product
    path(
        "xeloos-store/product/<slug:slug>/",
        views.product_detail,
        name="product-detail",
    ),

    # =========================================================
    # SERVICES / STATIC PAGES
    # =========================================================
    path("xeloos-services/", views.services, name="services"),
    path("about-us/", views.about_us, name="about-us"),
    path(
        "frequently-asked-questions/",
        views.faqs,
        name="faqs",
    ),

    # =========================================================
    # AUTHENTICATION
    # =========================================================
    path(
        "auth/sign-up/",
        views.sign_up,
        name="sign_up",
    ),
    path(
        "auth/sign-in/",
        views.sign_in,
        name="sign_in",
    ),
    path(
        "auth/sign-out/",
        views.sign_out,
        name="sign_out",
    ),

    # =========================================================
    # LEGAL
    # =========================================================
    path(
        "terms-and-conditions/",
        views.terms_view,
        name="terms",
    ),
    path(
        "privacy-policy/",
        views.policy_view,
        name="policy",
    ),

    # =========================================================
    # ACCOUNT
    # =========================================================
    path(
        "profile/",
        views.user_profile_view,
        name="user_profile",
    ),
    path(
        "order-history/",
        views.order_history_view,
        name="user-order-history",
    ),
    path(
        "order/<str:order_id>/",
        views.order_detail_view,
        name="order_detail",
    ),
    path(
        "change-password/",
        views.change_password_view,
        name="change_password",
    ),
]