from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string

from store.models import SIMCard, Product
from .cart import Cart


# =========================
# CART SUMMARY
# =========================

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


# =========================
# ADD PHYSICAL SIM TO CART
# =========================

def cart_add_view(request):
    if request.method != "POST" or request.POST.get("action") != "post":
        return JsonResponse(
            {"error": "Invalid request"},
            status=400,
        )

    sim_id = request.POST.get("sim_id")

    if not sim_id:
        return JsonResponse(
            {"error": "Missing sim_id"},
            status=400,
        )

    try:
        sim_id = int(sim_id)
    except (ValueError, TypeError):
        return JsonResponse(
            {"error": "Invalid sim_id"},
            status=400,
        )

    sim = get_object_or_404(SIMCard, id=sim_id)

    cart = Cart(request)
    cart.add_sim(sim)

    return _cart_response(
        request,
        cart,
        item_name=sim.name,
    )


# =========================
# ADD DIGITAL PRODUCT
# =========================

def product_cart_add_view(request):
    if request.method != "POST" or request.POST.get("action") != "post":
        return JsonResponse(
            {"error": "Invalid request"},
            status=400,
        )

    product_id = request.POST.get("product_id")

    if not product_id:
        return JsonResponse(
            {"error": "Missing product_id"},
            status=400,
        )

    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        return JsonResponse(
            {"error": "Invalid product_id"},
            status=400,
        )

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True,
    )

    cart = Cart(request)
    cart.add_product(product)

    return _cart_response(
        request,
        cart,
        item_name=product.name,
    )


# =========================
# DELETE ITEM FROM CART
# =========================

def cart_delete_view(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Invalid request"},
            status=400,
        )

    cart_id = request.POST.get("cart_id")

    # Backwards compatibility with your old JS
    if not cart_id:
        sim_id = request.POST.get("sim_id")

        if sim_id:
            cart_id = f"sim_{sim_id}"

    if not cart_id:
        return JsonResponse(
            {"error": "Missing cart_id"},
            status=400,
        )

    cart = Cart(request)
    cart.delete(cart_id)

    return _cart_response(request, cart)


# =========================
# UPDATE CART QUANTITY
# =========================

def cart_update_view(request):
    if request.method != "POST" or request.POST.get("action") != "post":
        return JsonResponse(
            {"error": "Invalid request"},
            status=400,
        )

    cart_id = request.POST.get("cart_id")

    # Backwards compatibility
    if not cart_id:
        sim_id = request.POST.get("sim_id")

        if sim_id:
            cart_id = f"sim_{sim_id}"

    quantity = request.POST.get("quantity")

    if not cart_id or not quantity:
        return JsonResponse(
            {"error": "Missing data"},
            status=400,
        )

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return JsonResponse(
            {"error": "Invalid quantity"},
            status=400,
        )

    if quantity < 1 or quantity > 5:
        return JsonResponse(
            {"error": "Quantity must be between 1 and 5"},
            status=400,
        )

    cart = Cart(request)
    cart.update(cart_id, quantity)

    return _cart_response(request, cart)


# =========================
# HELPER
# =========================

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