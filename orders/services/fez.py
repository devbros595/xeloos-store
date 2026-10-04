import requests

from django.conf import settings


def create_fez_delivery(order):
    """
    Create a Fez delivery for a paid Xeloos order.

    Fez delivery is only created for orders that require
    physical delivery.

    Returns:
        True  -> Fez delivery created successfully
        False -> Fez delivery was not created
    """

    # --------------------------------------------------
    # SAFETY CHECKS
    # --------------------------------------------------

    if order.status != "paid":
        return False

    # Prevent duplicate Fez deliveries.
    if order.fez_order_id:
        return True

    # eSIM / digital-only orders should never reach Fez.
    if order.delivery_method == "Digital Delivery":
        order.fez_status = "not_required"

        order.save(update_fields=["fez_status"])

        return True

    # --------------------------------------------------
    # BUILD ITEM DESCRIPTION
    # --------------------------------------------------

    items = order.items.all()

    item_descriptions = []

    for item in items:
        item_descriptions.append(f"{item.product_name} x {item.quantity}")

    item_description = ", ".join(item_descriptions)

    # --------------------------------------------------
    # FEZ PAYLOAD
    # --------------------------------------------------

    payload = [
        {
            "recipientAddress": order.address,
            "recipientState": order.state,
            "recipientName": order.name,
            "recipientPhone": order.phone,
            "recipientEmail": order.email,
            # Unique Xeloos reference.
            "uniqueID": order.order_id,
            # Groups this delivery request.
            "BatchID": f"XEELOOS-{order.order_id}",
            "itemDescription": item_description,
            # Value of the physical goods.
            "valueOfItem": str(order.total_price - order.delivery_fee),
            # Fez expects weight as an integer in KG.
            # We can make this configurable later if needed.
            "weight": 1,
            # Customer has already paid Xeloos.
            "isItemCod": False,
            "fragile": False,
        }
    ]

    # --------------------------------------------------
    # FEZ API
    # --------------------------------------------------

    url = f"{settings.FEZ_API_URL.rstrip('/')}" "/order"

    headers = {
        "Authorization": (f"Bearer {settings.FEZ_API_KEY}"),
        "secret-key": settings.FEZ_SECRET_KEY,
        "Content-Type": "application/json",
    }

    try:

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30,
        )

        response_data = response.json()

        print("========== FEZ DELIVERY RESPONSE ==========")
        print(
            "STATUS CODE:",
            response.status_code,
        )
        print(
            "RESPONSE:",
            response_data,
        )
        print(
            "XEELOOS ORDER:",
            order.order_id,
        )
        print(
            "===========================================",
        )

    except requests.RequestException as exc:

        print(
            "FEZ DELIVERY REQUEST ERROR:",
            exc,
        )

        order.fez_status = "failed"

        order.save(update_fields=["fez_status"])

        return False

    except ValueError:

        print("FEZ DELIVERY ERROR: " "Invalid JSON response")

        order.fez_status = "failed"

        order.save(update_fields=["fez_status"])

        return False

    # --------------------------------------------------
    # HANDLE FEZ RESPONSE
    # --------------------------------------------------

    if response.status_code in [200, 201] and response_data.get("status") == "Success":

        order_numbers = response_data.get("orderNos", {})

        fez_order_id = order_numbers.get(order.order_id)

        if fez_order_id:

            order.fez_order_id = str(fez_order_id)

            order.fez_status = "created"

            order.save(
                update_fields=[
                    "fez_order_id",
                    "fez_status",
                ]
            )

            return True

    # --------------------------------------------------
    # FEZ CREATION FAILED
    # --------------------------------------------------

    order.fez_status = "failed"

    order.save(update_fields=["fez_status"])

    return False
