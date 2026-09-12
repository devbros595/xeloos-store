from django.shortcuts import render, get_object_or_404, redirect
from .models import (
    SIMCard,
    Country,
    NewsletterEmail,
    UserProfile,
    Category,
    Product,
)

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator

from blog.models import BlogPost
from orders.models import Order


# =========================================================
# HOME
# =========================================================

def index(request):
    if request.method == "POST":
        email = request.POST.get("email")

        if not email:
            messages.error(request, "No email provided.")
            return redirect("index")

        if NewsletterEmail.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("index")

        NewsletterEmail.objects.create(email=email)
        messages.success(request, "Subscribed successfully.")
        return redirect("index")

    recent_posts = BlogPost.objects.order_by("-created_at")[:3]

    countries = Country.objects.all().order_by("name")

    categories = Category.objects.filter(
        is_active=True
    ).order_by("ordering", "name")

    featured_products = Product.objects.filter(
        is_active=True,
        featured=True
    ).select_related("category")[:8]

    context = {
        "country": countries,
        "categories": categories,
        "featured_products": featured_products,
        "recent_posts": recent_posts,
    }

    return render(request, "store/index.html", context)


# =========================================================
# CATEGORY STORE
# =========================================================

def store_category(request):
    categories = Category.objects.filter(
        is_active=True
    ).order_by("ordering", "name")

    return render(
        request,
        "store/store_category.html",
        {
            "categories": categories
        }
    )


# =========================================================
# GENERIC CATEGORY PAGE
# =========================================================

def category_products(request, slug):

    category = get_object_or_404(
        Category,
        slug=slug,
        is_active=True
    )

    products = Product.objects.filter(
        category=category,
        is_active=True
    ).order_by("-created_at")

    paginator = Paginator(products, 12)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    context = {
        "category": category,
        "products": page_obj,
        "page_obj": page_obj,
        "categories": Category.objects.filter(
            is_active=True
        ).order_by("ordering", "name"),
    }

    return render(
        request,
        "store/category_products.html",
        context
    )


# =========================================================
# PRODUCT DETAIL
# =========================================================

def product_detail(request, slug):

    product = get_object_or_404(
        Product,
        slug=slug,
        is_active=True
    )

    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(
        id=product.id
    )[:4]

    context = {
        "product": product,
        "related_products": related_products,
    }

    return render(
        request,
        "store/product_detail.html",
        context
    )


# =========================================================
# EXISTING PHYSICAL SIM STORE
# =========================================================

def store(request, slug):

    country = get_object_or_404(
        Country,
        slug=slug
    )

    sims = SIMCard.objects.filter(
        country=country
    ).order_by("name")

    paginator = Paginator(sims, 8)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "country_obj": sims,
        "country": country,
    }

    return render(
        request,
        "store/store.html",
        context
    )


# =========================================================
# USER PROFILE
# =========================================================

@login_required
def user_profile_view(request):

    profile = request.user.userprofile

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")

        request.user.username = username

        profile.email = email
        profile.phone = phone

        request.user.save()
        profile.save()

        messages.success(
            request,
            "Profile updated successfully."
        )

        return redirect("user_profile")

    return render(
        request,
        "store/profile.html",
        {
            "profile": profile
        }
    )


# =========================================================
# AUTHENTICATION
# =========================================================

def sign_up(request):

    if request.method == "POST":

        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return redirect("sign_up")

        if User.objects.filter(
            email=email
        ).exists():

            messages.error(
                request,
                "Email already registered."
            )

            return redirect("sign_up")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.save()

        messages.success(
            request,
            "Account created successfully!"
        )

        return redirect("sign_in")

    return render(
        request,
        "store/sign_up.html"
    )


def sign_in(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("index")

        messages.error(
            request,
            "Invalid email or password."
        )

    return render(
        request,
        "store/sign_in.html"
    )


@login_required
def sign_out(request):

    logout(request)

    return redirect("sign_in")


# =========================================================
# STATIC PAGES
# =========================================================

def services(request):
    return render(request, "store/services.html")


def about_us(request):
    return render(request, "store/about_us.html")


def faqs(request):
    return render(request, "store/faqs.html")


def terms_view(request):
    return render(
        request,
        "store/terms-and-conditions.html"
    )


def policy_view(request):
    return render(
        request,
        "store/privacy-policy.html"
    )


# =========================================================
# ORDERS
# =========================================================

@login_required
def order_history_view(request):

    orders = Order.objects.filter(
        email=request.user.email
    ).order_by("-created_at")

    return render(
        request,
        "store/order_history.html",
        {
            "orders": orders
        }
    )


@login_required
def order_detail_view(request, order_id):

    order = get_object_or_404(
        Order,
        order_id=order_id,
        email=request.user.email
    )

    return render(
        request,
        "store/order_detail.html",
        {
            "order": order
        }
    )


# =========================================================
# CHANGE PASSWORD
# =========================================================

@login_required
def change_password_view(request):

    if request.method == "POST":

        current_password = request.POST.get(
            "current_password"
        )

        new_password = request.POST.get(
            "new_password"
        )

        user = request.user

        if not user.check_password(
            current_password
        ):

            messages.error(
                request,
                "Current password is incorrect."
            )

            return redirect(
                "change_password"
            )

        user.set_password(new_password)

        user.save()

        update_session_auth_hash(
            request,
            user
        )

        messages.success(
            request,
            "Your password has been updated successfully."
        )

        return redirect(
            "change_password"
        )

    return render(
        request,
        "store/change_password.html"
    )