from store.models import SIMCard


class Cart:
    def __init__(self, request):
        self.session = request.session

        # Get current session key if it exists
        cart = self.session.get("cart")

        # If the user is new, no session key! Create one!
        if not cart:
            cart = self.session["cart"] = {}

        # Make sure cart is available on all pages
        self.cart = self.session["cart"]

    def clear(self):
        self.session["cart"] = {}
        self.session.modified = True

    def __len__(self):
        return sum(item.get("quantity", 1) for item in self.cart.values())

    def add(self, sim, quantity=1):
        sim_id = str(sim.id)
        if sim_id not in self.cart:
            self.cart[sim_id] = {"quantity": quantity}
        else:
            self.cart[sim_id]["quantity"] += quantity
        self.session.modified = True

    def update(self, sim_id, quantity):
        sim_id = str(sim_id)
        if sim_id in self.cart:
            if quantity > 0:
                self.cart[sim_id]["quantity"] = quantity
            else:
                self.delete(sim_id)
            self.session.modified = True

    def get_sims(self):
        sim_ids = self.cart.keys()
        sims = SIMCard.objects.filter(id__in=sim_ids)
        sim_list = []
        for sim in sims:
            sim_id = str(sim.id)
            quantity = self.cart[str(sim.id)].get("quantity", 1)
            sim.cart_quantity = quantity
            total_price = float(sim.price) * quantity
            sim.line_total = float(sim.price) * quantity
            sim_list.append(
                {
                    "sim": sim,
                    "quantity": quantity,
                    "total_price": total_price,
                }
            )

        return sim_list

    def delete(self, sim):
        sim_id = str(sim)
        if sim_id in self.cart:
            del self.cart[sim_id]
            self.session.modified = True

    def get_total_price(self):
        total = 0
        for sim_id, item in self.cart.items():
            try:
                sim = SIMCard.objects.get(id=sim_id)
                total += sim.price * int(item.get("quantity", 1))
            except SIMCard.DoesNotExist:
                continue
        return total
