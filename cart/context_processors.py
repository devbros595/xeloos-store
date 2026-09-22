from .cart import Cart


def cart(request):
    cart_instance = Cart(request)

    return {
        "cart": cart_instance,
        "cart_items": cart_instance.get_items(),
        "cart_total": cart_instance.get_total_price(),
        "cart_count": len(cart_instance),
    }