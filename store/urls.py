from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("xeloos-store/catalogue/<slug:slug>", views.store, name="store"),
    path("xeloos-store/catalogue/", views.store_category, name="store-category"),
    path("xeloos-services/", views.services, name="services"),
    path("about-us/", views.about_us, name="about-us"),
    path("frequently-asked-questions/", views.faqs, name="faqs"),
    path("auth/sign-up/", views.sign_up, name="sign_up"),
    path("auth/sign-in/", views.sign_in, name="sign_in"),
    path("auth/sign-out/", views.sign_out, name="sign_out"),
    path("terms-and-conditions/", views.terms_view, name="terms"),
    path("privacy-policy/", views.policy_view, name="policy"),
    path("profile/", views.user_profile_view, name="user_profile"),
    path("order-history/", views.order_history_view, name="user-order-history"),
    path('order/<str:order_id>/', views.order_detail_view, name='order_detail'),
    path("change-password/", views.change_password_view, name="change_password"),

]
