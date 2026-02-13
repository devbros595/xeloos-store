from django.shortcuts import render, get_object_or_404
from .cart import Cart
from store.models import SIMCard
from django.http import JsonResponse
from django.template.loader import render_to_string
from .cart import Cart

# Create your views here.


def cart_summary_view(request):
    cart = Cart(request)
    cart_items = cart.get_sims()
    cart_total = cart.get_total_price()

    return render(
        request,
        "cart_summary.html",
        {"cart_items": cart_items, "cart_total": cart_total},
    )


def cart_add_view(request):
    # Get the cart instance from the session
    cart = Cart(request)

    # Check if the request is a POST request and the action is 'post'
    if request.method == "POST" and request.POST.get("action") == "post":
        try:
            # Get the sim_id from the request
            sim_id = request.POST.get("sim_id")
            if not sim_id:
                return JsonResponse({"error": "Missing sim_id"}, status=400)

            # Try to convert sim_id to an integer
            sim_id = int(sim_id)

            # Fetch the SIM card object from the database
            sim = get_object_or_404(SIMCard, id=sim_id)

            # Add the SIM card to the cart
            cart.add(sim=sim)

            # Get updated cart items
            cart_items = cart.get_sims()
            cart_total = cart.get_total_price()

            # Render the updated cart modal HTML
            html = render_to_string(
                "cart_summary.html",
                {"cart_items": cart_items, "cart_total": cart_total},
                request=request,
            )

            # Return a JSON response with the updated cart content and count
            return JsonResponse(
                {"html": html, "sim": sim.name, "cart_count": len(cart)}
            )

        except ValueError:
            # Handle case where sim_id isn't a valid integer
            return JsonResponse({"error": "Invalid sim_id"}, status=400)

    # Return error response if it's not a POST request or if the action is not 'post'
    return JsonResponse({"error": "Invalid request"}, status=400)


def cart_delete_view(request):
    cart = Cart(request)
    sim_id = request.POST.get("sim_id")
    if not sim_id:
        return JsonResponse({"error": "Missing sim_id"}, status=400)
    try:
        cart.delete(sim=sim_id)
        cart_items = cart.get_sims()
        cart_total = cart.get_total_price()
        html = render_to_string(
            "cart_summary.html",
            {"cart_items": cart_items, "cart_total": cart_total},
            request=request,
        )
        return JsonResponse({"html": html, "sim": sim_id, "cart_count": len(cart)})
    except ValueError:
        return JsonResponse({"error": "Invalid sim_id"}, status=400)


def cart_update_view(request):
    cart = Cart(request)
    if request.method == "POST" and request.POST.get("action") == "post":
        sim_id = request.POST.get("sim_id")
        quantity = request.POST.get("quantity")

        if not sim_id or not quantity:
            return JsonResponse({"error": "Missing data"}, status=400)

        try:
            sim_id = int(sim_id)
            quantity = int(quantity)

            if quantity < 1 or quantity > 5:
                return JsonResponse({"error": "Invalid quantity"}, status=400)

            cart.update(sim_id=sim_id, quantity=quantity)

            cart_items = cart.get_sims()
            cart_total = cart.get_total_price()
            html = render_to_string(
                "cart_summary.html",
                {
                    "cart_items": cart_items,
                    "cart_total": cart_total,
                },
                request=request,
            )
            return JsonResponse({"html": html, "cart_count": len(cart)})

        except ValueError:
            return JsonResponse({"error": "Invalid input"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)

