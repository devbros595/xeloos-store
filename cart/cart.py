from decimal import Decimal

from store.models import SIMCard, Product


class Cart:

    def __init__(self, request):
        self.session = request.session

        cart = self.session.get("cart")

        if not cart:
            cart = {}
            self.session["cart"] = cart

        self.cart = cart

        # Convert old SIM-only cart entries to the new format
        self._normalize_old_cart()

    # ---------------------------------------------------------
    # NORMALIZE OLD CART
    # ---------------------------------------------------------

    def _normalize_old_cart(self):
        changed = False

        for key, value in list(self.cart.items()):

            # Old format:
            # "1": {"quantity": 2}
            #
            # New format:
            # "sim_1": {
            #     "type": "sim",
            #     "id": 1,
            #     "quantity": 2,
            # }

            if str(key).isdigit():

                new_key = f"sim_{key}"

                self.cart[new_key] = {
                    "type": "sim",
                    "id": int(key),
                    "quantity": int(
                        value.get("quantity", 1)
                    ),
                }

                del self.cart[key]

                changed = True

        if changed:
            self.session.modified = True

    # ---------------------------------------------------------
    # CLEAR
    # ---------------------------------------------------------

    def clear(self):
        self.session["cart"] = {}
        self.cart = self.session["cart"]
        self.session.modified = True

    # ---------------------------------------------------------
    # CART COUNT
    # ---------------------------------------------------------

    def __len__(self):
        return sum(
            int(item.get("quantity", 1))
            for item in self.cart.values()
        )

    # ---------------------------------------------------------
    # ADD SIM
    # ---------------------------------------------------------

    def add_sim(self, sim, quantity=1):

        cart_id = f"sim_{sim.id}"

        if cart_id not in self.cart:

            self.cart[cart_id] = {
                "type": "sim",
                "id": sim.id,
                "quantity": min(quantity, 5),
            }

        else:

            current_quantity = int(
                self.cart[cart_id].get(
                    "quantity",
                    1,
                )
            )

            self.cart[cart_id]["quantity"] = min(
                current_quantity + quantity,
                5,
            )

        self.session.modified = True

    # ---------------------------------------------------------
    # OLD COMPATIBILITY
    # ---------------------------------------------------------

    def add(self, sim, quantity=1):
        self.add_sim(sim, quantity)

    # ---------------------------------------------------------
    # ADD DIGITAL PRODUCT
    # ---------------------------------------------------------

    def add_product(self, product, quantity=1):

        cart_id = f"product_{product.id}"

        if cart_id not in self.cart:

            self.cart[cart_id] = {
                "type": "product",
                "id": product.id,
                "quantity": min(quantity, 5),
            }

        else:

            current_quantity = int(
                self.cart[cart_id].get(
                    "quantity",
                    1,
                )
            )

            self.cart[cart_id]["quantity"] = min(
                current_quantity + quantity,
                5,
            )

        self.session.modified = True

    # ---------------------------------------------------------
    # GET ALL ITEMS
    # ---------------------------------------------------------

    def get_items(self):

        items = []

        for cart_id, cart_item in self.cart.items():

            item_type = cart_item.get("type")
            item_id = cart_item.get("id")

            try:
                quantity = int(
                    cart_item.get("quantity", 1)
                )
            except (ValueError, TypeError):
                quantity = 1

            # Keep quantity within allowed range
            quantity = max(1, min(quantity, 5))

            try:

                if item_type == "sim":

                    item = SIMCard.objects.get(
                        id=item_id
                    )

                elif item_type == "product":

                    item = Product.objects.get(
                        id=item_id,
                        is_active=True,
                    )

                else:
                    continue

            except (
                SIMCard.DoesNotExist,
                Product.DoesNotExist,
            ):
                continue

            total_price = (
                item.price * quantity
            )

            items.append(
                {
                    "cart_id": cart_id,
                    "type": item_type,
                    "id": item.id,
                    "item": item,
                    "name": item.name,
                    "price": item.price,
                    "quantity": quantity,
                    "total_price": total_price,
                }
            )

        return items

    # ---------------------------------------------------------
    # SIM COMPATIBILITY
    # ---------------------------------------------------------

    def get_sims(self):
        """
        Keeps existing SIM templates/views working.
        """

        sim_items = []

        for cart_item in self.get_items():

            if cart_item["type"] != "sim":
                continue

            sim_items.append(
                {
                    "sim": cart_item["item"],
                    "quantity": cart_item["quantity"],
                    "total_price": cart_item["total_price"],
                    "cart_id": cart_item["cart_id"],
                }
            )

        return sim_items

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------

    def update(
        self,
        cart_id=None,
        quantity=1,
        sim_id=None,
    ):

        # Support old calls using sim_id=
        if cart_id is None:
            cart_id = sim_id

        if cart_id is None:
            return

        cart_id = str(cart_id)

        # Support old numeric SIM IDs
        if cart_id not in self.cart:

            legacy_sim_key = f"sim_{cart_id}"

            if legacy_sim_key in self.cart:
                cart_id = legacy_sim_key

        if cart_id not in self.cart:
            return

        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            return

        if quantity > 5:
            quantity = 5

        if quantity > 0:

            self.cart[cart_id]["quantity"] = quantity

        else:

            self.delete(cart_id)

        self.session.modified = True

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    def delete(
        self,
        cart_id=None,
        sim=None,
    ):

        # Support old delete(sim=...)
        if cart_id is None:
            cart_id = sim

        if cart_id is None:
            return

        cart_id = str(cart_id)

        # New cart key
        if cart_id in self.cart:

            del self.cart[cart_id]
            self.session.modified = True

            return

        # Old numeric SIM ID
        legacy_sim_key = f"sim_{cart_id}"

        if legacy_sim_key in self.cart:

            del self.cart[legacy_sim_key]
            self.session.modified = True

    # ---------------------------------------------------------
    # TOTAL
    # ---------------------------------------------------------

    def get_total_price(self):

        total = Decimal("0.00")

        for cart_item in self.get_items():

            total += cart_item["total_price"]

        return total