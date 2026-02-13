from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from cart.cart import Cart
from .models import Order, OrderItem
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import random
from django.templatetags.static import static


def generate_order_id():
    return str(random.randint(1000000000, 9999999999))  # 10-digit number


def checkout_shipping_info_view(request):
    cart = Cart(request)
    if not cart.get_sims():
        return redirect("store")

    if request.method == "POST":
        request.session["checkout_data"] = {
            "name": request.POST.get("name"),
            "phone": request.POST.get("phone"),
            "email": request.POST.get("email"),
            "address": request.POST.get("address"),
            "city": request.POST.get("city"),
            "state": request.POST.get("state"),
        }
        return redirect("orders:shipping_method")  # FIXED

    initial_data = request.session.get("checkout_data", {})
    return render(request, "checkout.html", {"initial_data": initial_data})


def shipping_method_view(request):
    if request.method == "POST":
        shipping_method = request.POST.get("shipping_method")
        if not shipping_method:
            return render(
                request,
                "shipping_method.html",
                {"error": "Please select a shipping method."},
            )

        request.session["checkout_data"]["shipping_method"] = shipping_method
        request.session.modified = True
        return redirect("orders:payment_info")  # FIXED

    return render(request, "shipping_method.html")


import uuid


def payment_info_view(request):
    # Generate a temporary unique payment reference
    payment_reference = (
        str(uuid.uuid4()).replace("-", "").upper()[:10]
    )  # 10-char unique string
    return render(request, "payment.html", {"payment_reference": payment_reference})


def review_order_view(request):
    checkout_data = request.session.get("checkout_data", {})
    cart = Cart(request)
    cart_items = cart.get_sims()
    cart_total = cart.get_total_price()
    checkout_data = request.session.get("checkout_data")

    if not cart_items:
        return redirect("cart_summary")

    return render(
        request,
        "checkout_review.html",
        {
            "cart_items": cart_items,
            "cart_total": cart_total,
            "checkout_data": checkout_data,
            "cart": cart.cart,
        },
    )


def place_order_view(request):
    cart = Cart(request)
    cart_items = cart.get_sims()
    cart_total = cart.get_total_price()

    checkout_data = request.session.get("checkout_data")
    if not checkout_data or not cart_items:
        return redirect("cart_summary")

    order = Order.objects.create(
        order_id=generate_order_id(),
        name=checkout_data["name"],
        email=checkout_data["email"],
        phone=checkout_data["phone"],
        address=checkout_data["address"],
        city=checkout_data["city"],
        state=checkout_data["state"],
        total_price=cart_total,
    )

    for item in cart.get_sims():
        sim = item["sim"]
        quantity = item["quantity"]

        OrderItem.objects.create(
            order=order, sim_name=sim.name, sim_price=sim.price, quantity=quantity
        )

    cart.clear()
    del request.session["checkout_data"]

    return redirect("orders:payment_confirm", order_id=order.id)  # FIXED


def payment_confirm_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "payment_confirm.html", {"order": order})
