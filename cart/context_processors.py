from .cart import Cart

# Create context processor so cart works on all page
def cart(request):
    cart_instance = Cart(request)
    return {
        'cart': cart_instance,
        'cart_items': cart_instance.get_sims(),
        "cart_total": cart_instance.get_total_price()
    }
