from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string

from .cart import Cart
from store.models import SIMCard, Product


def render_cart_response(request, cart):
    """
    Render the cart HTML and return common cart data.
    """
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

    return html, cart_total


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
    """
    Add an existing physical SIM card to the cart.
    """

    if request.method != "POST" or request.POST.get("action") != "post":
        return JsonResponse({"error": "Invalid request"}, status=400)

    cart = Cart(request)

    sim_id = request.POST.get("sim_id")

    if not sim_id:
        return JsonResponse({"error": "Missing sim_id"}, status=400)

    try:
        sim_id = int(sim_id)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid sim_id"}, status=400)

    sim = get_object_or_404(SIMCard, id=sim_id)

    cart.add_sim(sim)

    html, cart_total = render_cart_response(request, cart)

    return JsonResponse(
        {
            "html": html,
            "sim": sim.name,
            "cart_count": len(cart),
            "cart_total": str(cart_total),
        }
    )


def product_add_view(request):
    """
    Add one of the new generic Xeloos products to the cart.
    """

    if request.method != "POST" or request.POST.get("action") != "post":
        return JsonResponse({"error": "Invalid request"}, status=400)

    cart = Cart(request)

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

    cart.add_product(product)

    html, cart_total = render_cart_response(request, cart)

    return JsonResponse(
        {
            "html": html,
            "product": product.name,
            "cart_count": len(cart),
            "cart_total": str(cart_total),
        }
    )


def cart_delete_view(request):
    """
    Remove either a SIM or generic Product from the cart.
    """

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    cart = Cart(request)

    cart_id = request.POST.get("cart_id")

    # Backwards compatibility with your existing JS
    if not cart_id:
        cart_id = request.POST.get("sim_id")

    if not cart_id:
        return JsonResponse({"error": "Missing cart_id"}, status=400)

    cart.delete(cart_id)

    html, cart_total = render_cart_response(request, cart)

    return JsonResponse(
        {
            "html": html,
            "cart_id": cart_id,
            "cart_count": len(cart),
            "cart_total": str(cart_total),
        }
    )


def cart_update_view(request):
    """
    Update quantity for either a SIM or generic Product.
    """

    if request.method != "POST" or request.POST.get("action") != "post":
        return JsonResponse({"error": "Invalid request"}, status=400)

    cart = Cart(request)

    cart_id = request.POST.get("cart_id")

    # Backwards compatibility with existing JS
    if not cart_id:
        cart_id = request.POST.get("sim_id")

    quantity = request.POST.get("quantity")

    if not cart_id or not quantity:
        return JsonResponse({"error": "Missing data"}, status=400)

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid quantity"}, status=400)

    if quantity < 1 or quantity > 5:
        return JsonResponse(
            {"error": "Quantity must be between 1 and 5"},
            status=400,
        )

    cart.update(
        cart_id=cart_id,
        quantity=quantity,
    )

    html, cart_total = render_cart_response(request, cart)

    return JsonResponse(
        {
            "html": html,
            "cart_count": len(cart),
            "cart_total": str(cart_total),
        }
    )