from decimal import Decimal

import random
import uuid
import requests

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, response
from django.template.loader import render_to_string
from django.urls import reverse

from store.models import SIMCard, Product
from cart.cart import Cart
from .models import Order, OrderItem


def generate_order_id():
    return str(random.randint(1000000000, 9999999999))


# =========================================================
# CART
# =========================================================


def cart_summary_view(request):
    cart = Cart(request)

    cart_items = cart.get_items()
    cart_total = cart.get_total_price()

    return render(
        request,
        "cart_summary.html",
        {
            "cart_items": cart_items,
            "cart_total": cart_total,
        },
    )


def cart_add_view(request):

    if request.method != "POST" or request.POST.get("action") != "post":
        return JsonResponse({"error": "Invalid request"}, status=400)

    sim_id = request.POST.get("sim_id")

    if not sim_id:
        return JsonResponse({"error": "Missing sim_id"}, status=400)

    try:
        sim_id = int(sim_id)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid sim_id"}, status=400)

    sim = get_object_or_404(SIMCard, id=sim_id)

    cart = Cart(request)

    cart.add_sim(sim)

    return _cart_response(request, cart, item_name=sim.name)


def product_cart_add_view(request):

    if request.method != "POST" or request.POST.get("action") != "post":
        return JsonResponse({"error": "Invalid request"}, status=400)

    product_id = request.POST.get("product_id")

    if not product_id:
        return JsonResponse({"error": "Missing product_id"}, status=400)

    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid product_id"}, status=400)

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True,
    )

    cart = Cart(request)

    cart.add_product(product)

    return _cart_response(request, cart, item_name=product.name)


def cart_delete_view(request):

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    cart_id = request.POST.get("cart_id")

    if not cart_id:

        sim_id = request.POST.get("sim_id")

        if sim_id:
            cart_id = f"sim_{sim_id}"

    if not cart_id:
        return JsonResponse({"error": "Missing cart_id"}, status=400)

    cart = Cart(request)

    cart.delete(cart_id)

    return _cart_response(request, cart)


def cart_update_view(request):

    if request.method != "POST" or request.POST.get("action") != "post":
        return JsonResponse({"error": "Invalid request"}, status=400)

    cart_id = request.POST.get("cart_id")

    if not cart_id:

        sim_id = request.POST.get("sim_id")

        if sim_id:
            cart_id = f"sim_{sim_id}"

    quantity = request.POST.get("quantity")

    if not cart_id or not quantity:
        return JsonResponse({"error": "Missing data"}, status=400)

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid quantity"}, status=400)

    if quantity < 1 or quantity > 5:
        return JsonResponse({"error": "Quantity must be between 1 and 5"}, status=400)

    cart = Cart(request)

    cart.update(cart_id, quantity)

    return _cart_response(request, cart)


def _cart_response(request, cart, item_name=None):

    cart_items = cart.get_items()

    cart_total = cart.get_total_price()

    html = render_to_string(
        "cart_summary.html",
        {
            "cart_items": cart_items,
            "cart_total": cart_total,
        },
        request=request,
    )

    response = {
        "html": html,
        "cart_count": len(cart),
    }

    if item_name:
        response["item"] = item_name

    return JsonResponse(response)


def checkout_view(request):
    cart = Cart(request)

    if not cart.get_items():
        return redirect("orders:cart-summary")

    if request.method == "POST":

        request.session["checkout_data"] = {
            "name": request.POST.get("name"),
            "phone": request.POST.get("phone"),
            "email": request.POST.get("email"),
            "address": request.POST.get("address"),
            "city": request.POST.get("city"),
            "state": request.POST.get("state"),
        }

        request.session.modified = True

        return redirect("orders:delivery_method")

    initial_data = request.session.get("checkout_data", {})

    return render(request, "checkout.html", {"initial_data": initial_data})


def delivery_method_view(request):

    checkout_data = request.session.get("checkout_data", {})

    if request.method == "POST":

        shipping_method = request.POST.get("shipping_method")

        if not shipping_method:
            return render(
                request,
                "shipping_method.html",
                {"error": "Please select a shipping method."},
            )

        # ---------------------------------------------
        # DELIVERY OPTIONS
        # ---------------------------------------------

        delivery_options = {
            "standard": {
                "name": "Standard Delivery",
                "fee": Decimal("0.00"),
                "duration": "5–7 business days",
            },
            "express": {
                "name": "Express Delivery",
                "fee": Decimal("8500.00"),
                "duration": "1–3 business days",
            },
        }

        delivery = delivery_options.get(shipping_method)

        if not delivery:
            return render(
                request,
                "shipping_method.html",
                {"error": "Invalid shipping method."},
            )

        checkout_data["shipping_method"] = shipping_method
        checkout_data["shipping_name"] = delivery["name"]
        checkout_data["delivery_fee"] = str(delivery["fee"])
        checkout_data["delivery_duration"] = delivery["duration"]

        request.session["checkout_data"] = checkout_data
        request.session.modified = True

        return redirect("orders:checkout_review")

    return render(
        request,
        "shipping_method.html",
    )


def review_order_view(request):

    checkout_data = request.session.get("checkout_data", {})

    cart = Cart(request)

    cart_items = cart.get_items()
    cart_total = cart.get_total_price()

    if not checkout_data or not cart_items:
        return redirect("orders:cart-summary")

    # Delivery information saved by shipping_method_view
    shipping_name = checkout_data.get("shipping_name", "Standard Delivery")

    delivery_duration = checkout_data.get("delivery_duration", "")

    delivery_fee = Decimal(str(checkout_data.get("delivery_fee", "0")))

    # Final amount customer will pay
    total_payable = cart_total + delivery_fee

    return render(
        request,
        "checkout_review.html",
        {
            "cart_items": cart_items,
            "cart_total": cart_total,
            # Delivery
            "shipping_name": shipping_name,
            "delivery_duration": delivery_duration,
            "delivery_fee": delivery_fee,
            # Final total
            "total_payable": total_payable,
            # Customer checkout information
            "checkout_data": checkout_data,
            # Existing cart
            "cart": cart.cart,
        },
    )


def flutterwave_payment_view(request):

    if request.method != "POST":
        return redirect("orders:checkout_review")

    checkout_data = request.session.get("checkout_data", {})

    cart = Cart(request)
    cart_items = cart.get_items()
    cart_total = cart.get_total_price()

    if not checkout_data or not cart_items:
        return redirect("orders:cart-summary")

    # ---------------------------------------------------------
    # DELIVERY
    # ---------------------------------------------------------

    delivery_fee = Decimal(
        str(checkout_data.get("delivery_fee", "0.00"))
    )

    total_payable = cart_total + delivery_fee

    shipping_method = checkout_data.get(
        "shipping_method",
        "standard"
    )

    shipping_name = checkout_data.get(
        "shipping_name",
        "Standard Delivery"
    )

    # ---------------------------------------------------------
    # CREATE ORDER
    # ---------------------------------------------------------

    order = Order.objects.create(
        name=checkout_data.get("name", ""),
        email=checkout_data.get("email", ""),
        phone=checkout_data.get("phone", ""),
        address=checkout_data.get("address", ""),
        city=checkout_data.get("city", ""),
        state=checkout_data.get("state", ""),
        total_price=total_payable,
        delivery_method=shipping_name,
        delivery_fee=delivery_fee,
        payment_method="flutterwave",
        status="pending",
    )

    # ---------------------------------------------------------
    # CREATE ORDER ITEMS
    # ---------------------------------------------------------

    for item in cart_items:

        OrderItem.objects.create(
            order=order,
            product_type=item["type"],
            product_id=item["id"],
            product_name=item["name"],
            product_price=item["price"],
            quantity=item["quantity"],
        )

    # ---------------------------------------------------------
    # FLUTTERWAVE TRANSACTION REFERENCE
    # ---------------------------------------------------------

    tx_ref = (
        f"XEELOOS-{order.order_id}-"
        f"{uuid.uuid4().hex[:8].upper()}"
    )

    order.flutterwave_tx_ref = tx_ref
    order.save(update_fields=["flutterwave_tx_ref"])

    # ---------------------------------------------------------
    # CALLBACK URL
    # ---------------------------------------------------------

    callback_url = request.build_absolute_uri(
        reverse("orders:flutterwave_callback")
    )

    # ---------------------------------------------------------
    # FLUTTERWAVE PAYMENT PAYLOAD
    # ---------------------------------------------------------

    payload = {
        "tx_ref": tx_ref,
        "amount": str(total_payable),
        "currency": "NGN",

        "redirect_url": callback_url,

        "customer": {
            "email": checkout_data.get("email", ""),
            "name": checkout_data.get("name", ""),
            "phonenumber": checkout_data.get("phone", ""),
        },

        "customizations": {
            "title": "Xeloos",
            "description": f"Payment for Order {order.order_id}",
        },

        "meta": {
            "order_id": order.order_id,
            "shipping_method": shipping_method,
        },
    }

    # ---------------------------------------------------------
    # SEND REQUEST TO FLUTTERWAVE
    # ---------------------------------------------------------

    try:

        response = requests.post(
            "https://api.flutterwave.com/v3/payments",

            json=payload,

            headers={
                "Authorization": (
                    f"Bearer {settings.FLW_SECRET_KEY}"
                ),
                "Content-Type": "application/json",
            },

            timeout=30,
        )

        response_data = response.json()

        print("========== FLUTTERWAVE RESPONSE ==========")
        print("STATUS CODE:", response.status_code)
        print("RESPONSE:", response_data)
        print("==========================================")

    except requests.RequestException:

        order.status = "cancelled"
        order.save(update_fields=["status"])

        return render(
            request,
            "checkout_review.html",
            {
                "cart_items": cart_items,
                "cart_total": cart_total,
                "shipping_name": shipping_name,
                "delivery_duration": checkout_data.get(
                    "delivery_duration",
                    ""
                ),
                "delivery_fee": delivery_fee,
                "total_payable": total_payable,
                "checkout_data": checkout_data,
                "cart": cart.cart,
                "payment_error": (
                    "Unable to connect to Flutterwave. "
                    "Please try again."
                ),
            },
        )

    # ---------------------------------------------------------
    # REDIRECT CUSTOMER TO FLUTTERWAVE
    # ---------------------------------------------------------

    if (
        response_data.get("status") == "success"
        and response_data.get("data", {}).get("link")
    ):

        return redirect(
            response_data["data"]["link"]
        )

    # ---------------------------------------------------------
    # PAYMENT INITIALIZATION FAILED
    # ---------------------------------------------------------

    order.status = "cancelled"
    order.save(update_fields=["status"])

    return render(
        request,
        "checkout_review.html",
        {
            "cart_items": cart_items,
            "cart_total": cart_total,
            "shipping_name": shipping_name,
            "delivery_duration": checkout_data.get(
                "delivery_duration",
                ""
            ),
            "delivery_fee": delivery_fee,
            "total_payable": total_payable,
            "checkout_data": checkout_data,
            "cart": cart.cart,
            "payment_error": response_data.get(
                "message",
                "Unable to initialize payment.",
            ),
        },
    )


def flutterwave_callback_view(request):

    tx_ref = request.GET.get("tx_ref")
    transaction_id = request.GET.get("transaction_id")
    status = request.GET.get("status")

    # -----------------------------------------------------
    # BASIC VALIDATION
    # -----------------------------------------------------

    if not tx_ref or not transaction_id:

        return render(
            request,
            "payment_confirm.html",
            {
                "payment_failed": True,
                "message": "Payment cancelled. You have not been charged.",
            },
        )

    # -----------------------------------------------------
    # FIND ORDER
    # -----------------------------------------------------

    order = get_object_or_404(
        Order,
        flutterwave_tx_ref=tx_ref,
    )

    # -----------------------------------------------------
    # PREVENT REPROCESSING
    # -----------------------------------------------------

    if order.status == "paid":

        return render(
            request,
            "payment_confirm.html",
            {
                "order": order,
                "payment_successful": True,
            },
        )

    # -----------------------------------------------------
    # VERIFY TRANSACTION WITH FLUTTERWAVE
    # -----------------------------------------------------

    try:

        response = requests.get(
            f"https://api.flutterwave.com/v3/transactions/" f"{transaction_id}/verify",
            headers={
                "Authorization": f"Bearer {settings.FLW_SECRET_KEY}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        response_data = response.json()

    except requests.RequestException:

        return render(
            request,
            "payment_confirm.html",
            {
                "order": order,
                "payment_failed": True,
                "message": (
                    "We could not verify your payment. " "Please contact support."
                ),
            },
        )

    # -----------------------------------------------------
    # EXTRACT VERIFIED DATA
    # -----------------------------------------------------

    transaction = response_data.get("data")

    if not transaction:

        return render(
            request,
            "payment_confirm.html",
            {
                "order": order,
                "payment_failed": True,
                "message": "Payment verification failed.",
            },
        )

    verified_status = transaction.get("status")
    verified_tx_ref = transaction.get("tx_ref")
    verified_currency = transaction.get("currency")

    verified_amount = Decimal(
        str(
            transaction.get(
                "charged_amount",
                transaction.get("amount", "0"),
            )
        )
    )

    # -----------------------------------------------------
    # EXPECTED VALUES
    # -----------------------------------------------------

    expected_amount = Decimal(str(order.total_price))

    expected_currency = "NGN"

    # -----------------------------------------------------
    # SECURITY CHECKS
    # -----------------------------------------------------

    if verified_tx_ref != order.flutterwave_tx_ref:

        return render(
            request,
            "payment_confirm.html",
            {
                "order": order,
                "payment_failed": True,
                "message": "Transaction reference mismatch.",
            },
        )

    if verified_currency != expected_currency:

        return render(
            request,
            "payment_confirm.html",
            {
                "order": order,
                "payment_failed": True,
                "message": "Payment currency mismatch.",
            },
        )

    if verified_status != "successful":
        return render(
            request,
            "payment_confirm.html",
            {
                "order": order,
                "payment_failed": True,
                "message": "Payment was not successful. You can try again.",
            },
        )
    
    if verified_amount != expected_amount:

        return render(
            request,
            "payment_confirm.html",
            {
                "order": order,
                "payment_failed": True,
                "message": ("The amount received does not match " "the order total."),
            },
        )

    # -----------------------------------------------------
    # PAYMENT VERIFIED
    # -----------------------------------------------------

    order.status = "paid"
    order.flutterwave_transaction_id = str(transaction.get("id"))

    order.save(
        update_fields=[
            "status",
            "flutterwave_transaction_id",
        ]
    )

    # -----------------------------------------------------
    # CLEAR CART
    # -----------------------------------------------------

    cart = Cart(request)
    cart.clear()

    if "checkout_data" in request.session:
        del request.session["checkout_data"]

    request.session.modified = True

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    return render(
        request,
        "payment_confirm.html",
        {
            "order": order,
            "payment_successful": True,
        },
    )