from decimal import Decimal

import random
import uuid
import requests
import hashlib
import hmac
import json

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, response
from django.template.loader import render_to_string
from django.urls import reverse

from store.models import SIMCard, Product, StoreSettings
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


def cart_requires_delivery(cart_items):
    """
    Returns True if the cart contains at least one
    physical item that requires delivery.
    """

    settings_obj = StoreSettings.objects.first()

    esim_category_id = (
        settings_obj.esim_category_id
        if settings_obj and settings_obj.esim_category
        else None
    )

    for item in cart_items:

        # Physical SIMCards always require delivery.
        if item["type"] == "sim":
            return True

        # Products require delivery unless they belong
        # to the configured eSIM category.
        if item["type"] == "product":

            product = (
                Product.objects.filter(id=item["id"]).select_related("category").first()
            )

            if not product:
                continue

            if product.category_id != esim_category_id:
                return True

    return False


def checkout_view(request):

    cart = Cart(request)
    cart_items = cart.get_items()

    if not cart_items:
        return redirect("orders:cart-summary")

    # Determine whether this cart contains only digital/eSIM items.
    is_digital_only = not cart_requires_delivery(cart_items)

    # Existing checkout data, used to repopulate the form.
    checkout_data = request.session.get("checkout_data", {})

    if request.method == "POST":

        checkout_data = {
            "name": request.POST.get("name", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "address": request.POST.get("address", "").strip(),
            "city": request.POST.get("city", "").strip(),
            "state": request.POST.get("state", "").strip(),
        }

        # For eSIM/digital-only orders, physical delivery
        # information is not required.
        if is_digital_only:

            checkout_data["address"] = ""
            checkout_data["city"] = ""
            checkout_data["state"] = ""

            checkout_data["shipping_method"] = "digital"
            checkout_data["shipping_name"] = "Digital Delivery"
            checkout_data["delivery_fee"] = "0.00"
            checkout_data["delivery_duration"] = "Instant"

            request.session["checkout_data"] = checkout_data
            request.session.modified = True

            return redirect("orders:checkout_review")

        # Physical or mixed cart.
        request.session["checkout_data"] = checkout_data
        request.session.modified = True

        return redirect("orders:delivery_method")

    return render(
        request,
        "checkout.html",
        {
            "initial_data": checkout_data,
            "is_digital_only": is_digital_only,
        },
    )


def delivery_method_view(request):

    checkout_data = request.session.get("checkout_data", {})

    # ---------------------------------------------
    # PROTECT DELIVERY STEP
    # ---------------------------------------------
    # If the cart contains only eSIM/digital items,
    # delivery is not required. Skip this page.
    cart = Cart(request)
    cart_items = cart.get_items()

    if not cart_requires_delivery(cart_items):

        checkout_data["shipping_method"] = "digital"
        checkout_data["shipping_name"] = "Digital Delivery"
        checkout_data["delivery_fee"] = "0.00"
        checkout_data["delivery_duration"] = "Instant"

        request.session["checkout_data"] = checkout_data
        request.session.modified = True

        return redirect("orders:checkout_review")

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

    shipping_name = checkout_data.get(
        "shipping_name",
        "Digital Delivery",
    )

    delivery_duration = checkout_data.get(
        "delivery_duration",
        "Instant",
    )

    delivery_fee = Decimal(str(checkout_data.get("delivery_fee", "0.00")))

    # Determine whether this is an eSIM-only order.
    is_digital_only = checkout_data.get("shipping_method") == "digital"

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
            "is_digital_only": is_digital_only,
            # Final total
            "total_payable": total_payable,
            # Customer checkout information
            "checkout_data": checkout_data,
            # Existing cart
            "cart": cart.cart,
        },
    )


def payment_method_view(request):

    if request.method != "POST":
        return redirect("orders:checkout_review")

    payment_method = request.POST.get("payment_method")

    if payment_method == "flutterwave":
        return flutterwave_payment_view(request)

    if payment_method == "nowpayments":
        return nowpayments_payment_view(request)

    return redirect("orders:checkout_review")


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

    delivery_fee = Decimal(str(checkout_data.get("delivery_fee", "0.00")))

    total_payable = cart_total + delivery_fee

    shipping_method = checkout_data.get("shipping_method", "standard")

    shipping_name = checkout_data.get("shipping_name", "Standard Delivery")

    # ---------------------------------------------------------
    # GET EXISTING ORDER FROM SESSION
    # ---------------------------------------------------------

    existing_order_id = request.session.get("pending_order_id")

    order = None

    if existing_order_id:

        order = Order.objects.filter(
            id=existing_order_id,
            status__in=["pending", "cancelled"],
        ).first()

    # ---------------------------------------------------------
    # CREATE ORDER ONLY IF ONE DOES NOT EXIST
    # ---------------------------------------------------------

    if not order:

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

        # Create order items only for a brand-new order
        for item in cart_items:

            OrderItem.objects.create(
                order=order,
                product_type=item["type"],
                product_id=item["id"],
                product_name=item["name"],
                product_price=item["price"],
                quantity=item["quantity"],
            )

        # Remember this order for payment retries
        request.session["pending_order_id"] = order.id
        request.session.modified = True

    else:

        # -----------------------------------------------------
        # REUSE EXISTING ORDER
        # -----------------------------------------------------

        order.name = checkout_data.get("name", "")
        order.email = checkout_data.get("email", "")
        order.phone = checkout_data.get("phone", "")
        order.address = checkout_data.get("address", "")
        order.city = checkout_data.get("city", "")
        order.state = checkout_data.get("state", "")

        order.total_price = total_payable
        order.delivery_method = shipping_name
        order.delivery_fee = delivery_fee
        order.payment_method = "flutterwave"
        order.status = "pending"

        order.save(
            update_fields=[
                "name",
                "email",
                "phone",
                "address",
                "city",
                "state",
                "total_price",
                "delivery_method",
                "delivery_fee",
                "payment_method",
                "status",
            ]
        )

    # ---------------------------------------------------------
    # NEW FLUTTERWAVE TRANSACTION REFERENCE
    # ---------------------------------------------------------
    #
    # Every payment attempt gets a NEW tx_ref.
    # The ORDER remains the same.
    #

    tx_ref = f"XEELOOS-{order.order_id}-" f"{uuid.uuid4().hex[:8].upper()}"

    order.flutterwave_tx_ref = tx_ref

    order.save(update_fields=["flutterwave_tx_ref"])

    # ---------------------------------------------------------
    # CALLBACK URL
    # ---------------------------------------------------------

    callback_url = request.build_absolute_uri(reverse("orders:flutterwave_callback"))

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
            "description": (f"Payment for Order {order.order_id}"),
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
                "Authorization": (f"Bearer {settings.FLW_SECRET_KEY}"),
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        response_data = response.json()

        print("========== FLUTTERWAVE RESPONSE ==========")
        print("STATUS CODE:", response.status_code)
        print("RESPONSE:", response_data)
        print("ORDER:", order.order_id)
        print("TX REF:", tx_ref)
        print("==========================================")

    except requests.RequestException:

        # Keep the same order so it can be retried
        order.status = "cancelled"

        order.save(update_fields=["status"])

        return render(
            request,
            "checkout_review.html",
            {
                "cart_items": cart_items,
                "cart_total": cart_total,
                "shipping_name": shipping_name,
                "delivery_duration": checkout_data.get("delivery_duration", ""),
                "delivery_fee": delivery_fee,
                "total_payable": total_payable,
                "checkout_data": checkout_data,
                "cart": cart.cart,
                "payment_error": (
                    "Unable to connect to Flutterwave. " "Please try again."
                ),
            },
        )

    # ---------------------------------------------------------
    # REDIRECT TO FLUTTERWAVE
    # ---------------------------------------------------------

    if response_data.get("status") == "success" and response_data.get("data", {}).get(
        "link"
    ):

        return redirect(response_data["data"]["link"])

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
            "delivery_duration": checkout_data.get("delivery_duration", ""),
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


def nowpayments_payment_view(request):

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

    delivery_fee = Decimal(str(checkout_data.get("delivery_fee", "0.00")))

    total_payable = cart_total + delivery_fee

    shipping_name = checkout_data.get(
        "shipping_name",
        "Standard Delivery",
    )

    shipping_method = checkout_data.get(
        "shipping_method",
        "standard",
    )

    # ---------------------------------------------------------
    # GET EXISTING ORDER FROM SESSION
    # ---------------------------------------------------------

    existing_order_id = request.session.get("pending_order_id")

    order = None

    if existing_order_id:

        order = Order.objects.filter(
            id=existing_order_id,
            status__in=["pending", "cancelled"],
        ).first()

    # ---------------------------------------------------------
    # CREATE ORDER IF ONE DOES NOT EXIST
    # ---------------------------------------------------------

    if not order:

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
            payment_method="nowpayments",
            status="pending",
        )

        # Create order items
        for item in cart_items:

            OrderItem.objects.create(
                order=order,
                product_type=item["type"],
                product_id=item["id"],
                product_name=item["name"],
                product_price=item["price"],
                quantity=item["quantity"],
            )

        # Remember order for payment retries
        request.session["pending_order_id"] = order.id
        request.session.modified = True

    else:

        # -----------------------------------------------------
        # REUSE EXISTING ORDER
        # -----------------------------------------------------

        order.name = checkout_data.get("name", "")
        order.email = checkout_data.get("email", "")
        order.phone = checkout_data.get("phone", "")
        order.address = checkout_data.get("address", "")
        order.city = checkout_data.get("city", "")
        order.state = checkout_data.get("state", "")

        order.total_price = total_payable
        order.delivery_method = shipping_name
        order.delivery_fee = delivery_fee
        order.payment_method = "nowpayments"
        order.status = "pending"

        order.save(
            update_fields=[
                "name",
                "email",
                "phone",
                "address",
                "city",
                "state",
                "total_price",
                "delivery_method",
                "delivery_fee",
                "payment_method",
                "status",
            ]
        )

    # ---------------------------------------------------------
    # NOWPAYMENTS IPN CALLBACK URL
    # ---------------------------------------------------------

    ipn_callback_url = request.build_absolute_uri(reverse("orders:nowpayments_ipn"))

    # ---------------------------------------------------------
    # PAYMENT SUCCESS / CANCEL URLS
    # ---------------------------------------------------------

    success_url = request.build_absolute_uri(
        reverse(
            "orders:nowpayments_success",
            kwargs={"order_id": order.id},
        )
    )

    cancel_url = request.build_absolute_uri(
        reverse(
            "orders:nowpayments_cancel",
            kwargs={"order_id": order.id},
        )
    )

    # ---------------------------------------------------------
    # NOWPAYMENTS INVOICE PAYLOAD
    # ---------------------------------------------------------

    payload = {
        "price_amount": float(total_payable),
        "price_currency": "NGN",
        "order_id": order.order_id,
        "order_description": (f"Xeloos Order {order.order_id}"),
        "ipn_callback_url": ipn_callback_url,
        "success_url": success_url,
        "cancel_url": cancel_url,
    }

    # ---------------------------------------------------------
    # SEND REQUEST TO NOWPAYMENTS
    # ---------------------------------------------------------

    try:

        response = requests.post(
            "https://api.nowpayments.io/v1/invoice",
            json=payload,
            headers={
                "x-api-key": settings.NOWPAYMENTS_API_KEY,
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        response_data = response.json()

        print("========== NOWPAYMENTS RESPONSE ==========")
        print("STATUS CODE:", response.status_code)
        print("RESPONSE:", response_data)
        print("ORDER:", order.order_id)
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
                    "",
                ),
                "delivery_fee": delivery_fee,
                "total_payable": total_payable,
                "checkout_data": checkout_data,
                "cart": cart.cart,
                "payment_error": (
                    "Unable to connect to NOWPayments. " "Please try again."
                ),
            },
        )

    # ---------------------------------------------------------
    # CHECK NOWPAYMENTS RESPONSE
    # ---------------------------------------------------------

    if response.status_code in [200, 201] and response_data.get("invoice_url"):

        # -----------------------------------------------------
        # SAVE NOWPAYMENTS DETAILS
        # -----------------------------------------------------

        order.nowpayments_invoice_id = response_data.get("id")

        order.nowpayments_invoice_url = response_data.get("invoice_url")

        order.save(
            update_fields=[
                "nowpayments_invoice_id",
                "nowpayments_invoice_url",
            ]
        )

        # -----------------------------------------------------
        # REDIRECT CUSTOMER TO NOWPAYMENTS
        # -----------------------------------------------------

        return redirect(response_data["invoice_url"])

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
                "",
            ),
            "delivery_fee": delivery_fee,
            "total_payable": total_payable,
            "checkout_data": checkout_data,
            "cart": cart.cart,
            "payment_error": response_data.get(
                "message",
                "Unable to initialize NOWPayments.",
            ),
        },
    )


def nowpayments_ipn(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405,
        )

    received_signature = request.headers.get("x-nowpayments-sig")

    if not received_signature:
        return JsonResponse(
            {"error": "Missing signature"},
            status=400,
        )

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=400,
        )

    # NOWPayments requires the payload to be sorted
    # before generating the HMAC signature.
    def sort_payload(data):
        if isinstance(data, dict):
            return {key: sort_payload(data[key]) for key in sorted(data)}

        if isinstance(data, list):
            return [sort_payload(item) for item in data]

        return data

    sorted_payload = sort_payload(payload)

    payload_string = json.dumps(
        sorted_payload,
        separators=(",", ":"),
    )

    expected_signature = hmac.new(
        settings.NOWPAYMENTS_IPN_SECRET.encode(),
        payload_string.encode(),
        hashlib.sha512,
    ).hexdigest()

    if not hmac.compare_digest(
        expected_signature,
        received_signature,
    ):
        return JsonResponse(
            {"error": "Invalid signature"},
            status=401,
        )

    order_id = payload.get("order_id")
    payment_id = payload.get("payment_id")
    payment_status = payload.get("payment_status")

    if not order_id:
        return JsonResponse(
            {"error": "Missing order_id"},
            status=400,
        )

    order = Order.objects.filter(
        order_id=order_id,
    ).first()

    if not order:
        return JsonResponse(
            {"error": "Order not found"},
            status=404,
        )

    # Idempotency:
    # Ignore duplicate notifications for an already-paid order.
    if order.status == "paid":
        return JsonResponse(
            {
                "success": True,
                "message": "Order already processed",
            }
        )

    # Store the NOWPayments payment ID when available.
    if payment_id:
        order.nowpayments_payment_id = str(payment_id)

    # Payment is only considered successful when NOWPayments
    # reports it as finished.
    if payment_status == "finished":

        price_amount = payload.get("price_amount")

        if price_amount is not None:
            try:
                received_amount = Decimal(str(price_amount))
            except Exception:
                return JsonResponse(
                    {"error": "Invalid payment amount"},
                    status=400,
                )

            if received_amount != order.total_price:
                return JsonResponse(
                    {"error": "Payment amount mismatch"},
                    status=400,
                )

        order.status = "paid"

        order.save(
            update_fields=[
                "nowpayments_payment_id",
                "status",
            ]
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Payment confirmed",
            }
        )

    # Save payment ID even when the payment is still processing.
    if payment_id:
        order.save(
            update_fields=[
                "nowpayments_payment_id",
            ]
        )

    # These statuses are not successful payments.
    if payment_status in [
        "failed",
        "expired",
        "refunded",
    ]:
        order.status = "cancelled"

        order.save(
            update_fields=[
                "nowpayments_payment_id",
                "status",
            ]
        )

    return JsonResponse(
        {
            "success": True,
            "message": "IPN received",
            "payment_status": payment_status,
        }
    )


def nowpayments_success_view(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
    )

    return render(
        request,
        "payment_confirm.html",
        {
            "order": order,
            "payment_method": "NOWPayments",
        },
    )


def nowpayments_cancel_view(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
    )

    if order.status != "paid":
        order.status = "cancelled"
        order.save(update_fields=["status"])

    return render(
        request,
        "checkout_review.html",
        {
            "cart_items": Cart(request).get_items(),
            "cart_total": Cart(request).get_total_price(),
            "shipping_name": order.delivery_method,
            "delivery_fee": order.delivery_fee,
            "total_payable": order.total_price,
            "checkout_data": request.session.get(
                "checkout_data",
                {},
            ),
            "cart": Cart(request).cart,
            "payment_error": (
                "The NOWPayments payment was cancelled. " "You can try again."
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

    if not tx_ref:

        return render(
            request,
            "payment_confirm.html",
            {
                "payment_failed": True,
                "message": (
                    "We could not identify this payment attempt. " "Please try again."
                ),
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

        # Payment was already processed.
        # Remove retry reference from session.
        request.session.pop("pending_order_id", None)
        request.session.modified = True

        return render(
            request,
            "payment_confirm.html",
            {
                "order": order,
                "payment_successful": True,
            },
        )

    # -----------------------------------------------------
    # HANDLE FLUTTERWAVE CANCELLATION
    # -----------------------------------------------------

    if status in ["cancelled", "failed"]:

        order.status = "cancelled"

        order.save(update_fields=["status"])

        # IMPORTANT:
        # Keep pending_order_id in the session.
        # This allows the customer to retry the same order.
        request.session.modified = True

        return render(
            request,
            "payment_confirm.html",
            {
                "order": order,
                "payment_failed": True,
                "message": (
                    "Payment was not completed. "
                    "You can try again using the same order."
                ),
            },
        )

    # -----------------------------------------------------
    # TRANSACTION ID REQUIRED FOR VERIFICATION
    # -----------------------------------------------------

    if not transaction_id:

        return render(
            request,
            "payment_confirm.html",
            {
                "order": order,
                "payment_failed": True,
                "message": (
                    "Payment verification could not be completed. " "Please try again."
                ),
            },
        )

    # -----------------------------------------------------
    # VERIFY TRANSACTION WITH FLUTTERWAVE
    # -----------------------------------------------------

    try:

        response = requests.get(
            f"https://api.flutterwave.com/v3/transactions/" f"{transaction_id}/verify",
            headers={
                "Authorization": (f"Bearer {settings.FLW_SECRET_KEY}"),
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

    # Transaction reference must belong to this order
    if verified_tx_ref != order.flutterwave_tx_ref:

        return render(
            request,
            "payment_confirm.html",
            {
                "order": order,
                "payment_failed": True,
                "message": ("Transaction reference mismatch."),
            },
        )

    # Currency must be NGN
    if verified_currency != expected_currency:

        return render(
            request,
            "payment_confirm.html",
            {
                "order": order,
                "payment_failed": True,
                "message": ("Payment currency mismatch."),
            },
        )

    # Flutterwave must report successful
    if verified_status != "successful":

        order.status = "cancelled"

        order.save(update_fields=["status"])

        return render(
            request,
            "payment_confirm.html",
            {
                "order": order,
                "payment_failed": True,
                "message": ("Payment was not successful. " "You can try again."),
            },
        )

    # Amount must match the Xeloos order
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

    # -----------------------------------------------------
    # CLEAR CHECKOUT SESSION
    # -----------------------------------------------------

    request.session.pop("checkout_data", None)

    # -----------------------------------------------------
    # CLEAR PENDING ORDER
    # -----------------------------------------------------
    #
    # This is important.
    #
    # Once payment succeeds, the order can no longer
    # be reused for another payment attempt.
    #

    request.session.pop("pending_order_id", None)

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
