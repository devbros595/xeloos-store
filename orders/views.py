from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string

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


def checkout_shipping_info_view(request):
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

        return redirect("orders:shipping_method")

    initial_data = request.session.get("checkout_data", {})

    return render(request, "checkout.html", {"initial_data": initial_data})


def shipping_method_view(request):

    checkout_data = request.session.get("checkout_data", {})

    if request.method == "POST":

        shipping_method = request.POST.get("shipping_method")

        if not shipping_method:

            return render(
                request,
                "shipping_method.html",
                {"error": "Please select a shipping method."},
            )

        checkout_data["shipping_method"] = shipping_method

        request.session["checkout_data"] = checkout_data
        request.session.modified = True

        return redirect("orders:payment_info")

    return render(request, "shipping_method.html")


def payment_info_view(request):

    payment_reference = str(uuid.uuid4()).replace("-", "").upper()[:10]

    return render(request, "payment.html", {"payment_reference": payment_reference})


def review_order_view(request):

    checkout_data = request.session.get("checkout_data")

    cart = Cart(request)

    cart_items = cart.get_items()
    cart_total = cart.get_total_price()

    if not checkout_data or not cart_items:
        return redirect("orders:cart-summary")

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

    cart_items = cart.get_items()
    cart_total = cart.get_total_price()

    checkout_data = request.session.get("checkout_data")

    if not checkout_data or not cart_items:
        return redirect("orders:cart-summary")

    order = Order.objects.create(
        order_id=generate_order_id(),
        name=checkout_data.get("name", ""),
        email=checkout_data.get("email", ""),
        phone=checkout_data.get("phone", ""),
        address=checkout_data.get("address", ""),
        city=checkout_data.get("city", ""),
        state=checkout_data.get("state", ""),
        total_price=cart_total,
    )

    # -----------------------------------------------------
    # CREATE ORDER ITEMS
    # -----------------------------------------------------

    for item in cart_items:

        OrderItem.objects.create(
            order=order,
            product_type=item["type"],
            product_id=item["id"],
            product_name=item["name"],
            product_price=item["price"],
            quantity=item["quantity"],
        )

    # -----------------------------------------------------
    # CLEAR CART
    # -----------------------------------------------------

    cart.clear()

    if "checkout_data" in request.session:
        del request.session["checkout_data"]

    request.session.modified = True

    return redirect("orders:payment_confirm", order_id=order.id)


def payment_confirm_view(request, order_id):

    order = get_object_or_404(Order, id=order_id)

    return render(request, "payment_confirm.html", {"order": order})
