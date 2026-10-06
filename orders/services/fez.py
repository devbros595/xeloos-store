import requests

from django.conf import settings

# =========================================================
# FEZ AUTHENTICATION
# =========================================================


def authenticate_fez():
    """
    Authenticate with Fez and return:

        auth_token
        secret_key

    Fez requires an authenticated session before an order
    can be created.
    """

    url = f"{settings.FEZ_API_URL.rstrip('/')}/user/authenticate"

    payload = {
        "user_id": settings.FEZ_USER_ID,
        "password": settings.FEZ_PASSWORD,
    }

    headers = {
        "Content-Type": "application/json",
    }

    try:

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30,
        )

        try:
            response_data = response.json()

        except ValueError:

            print("FEZ AUTH ERROR: Invalid JSON response")

            print(
                "FEZ AUTH STATUS CODE:",
                response.status_code,
            )

            print(
                "FEZ AUTH RAW RESPONSE:",
                response.text,
            )

            return None, None

    except requests.RequestException as exc:

        print(
            "FEZ AUTH REQUEST ERROR:",
            exc,
        )

        return None, None

    # =====================================================
    # DEBUG AUTH RESPONSE
    # =====================================================

    print("========== FEZ AUTH RESPONSE ==========")

    print(
        "STATUS CODE:",
        response.status_code,
    )

    print(
        "RESPONSE:",
        response_data,
    )

    print("========================================")

    # =====================================================
    # HANDLE AUTH FAILURE
    # =====================================================

    if response.status_code not in [200, 201]:

        print(
            "FEZ AUTHENTICATION FAILED:",
            response_data,
        )

        return None, None

    if response_data.get("status") != "Success":

        print(
            "FEZ AUTHENTICATION FAILED:",
            response_data,
        )

        return None, None

    # =====================================================
    # EXTRACT AUTH DETAILS
    # =====================================================

    auth_details = response_data.get("authDetails", {})

    org_details = response_data.get("orgDetails", {})

    auth_token = auth_details.get("authToken")

    secret_key = org_details.get("secret-key")

    if not auth_token:

        print("FEZ AUTH ERROR: authToken missing from response")

        return None, None

    if not secret_key:

        print("FEZ AUTH ERROR: organization secret-key missing from response")

        return None, None

    return auth_token, secret_key


# =========================================================
# CREATE FEZ DELIVERY
# =========================================================


def create_fez_delivery(order):
    """
    Create a Fez delivery for a paid Xeloos order.

    Fez is only called after payment has been successfully
    confirmed.

    Returns:
        True  -> delivery created / already exists / not required
        False -> delivery creation failed
    """

    # =========================================================
    # SAFETY CHECKS
    # =========================================================

    # Never create a delivery before payment.
    if order.status != "paid":
        return False

    # Prevent duplicate Fez deliveries.
    if order.fez_order_id:
        return True

    # Digital-only orders do not require Fez delivery.
    if order.delivery_method == "Digital Delivery":

        order.fez_status = "not_required"

        order.save(update_fields=["fez_status"])

        return True

    # =========================================================
    # BUILD ITEM DESCRIPTION
    # =========================================================

    items = order.items.all()

    item_descriptions = []

    for item in items:

        item_descriptions.append(f"{item.product_name} x {item.quantity}")

    item_description = ", ".join(item_descriptions)

    # =========================================================
    # VALUE OF PHYSICAL ITEMS
    # =========================================================

    # total_price includes:
    #
    #   products + Xeloos delivery fee
    #
    # Fez's valueOfItem should represent the value
    # of the items being delivered, not your delivery fee.

    value_of_items = order.total_price - order.delivery_fee

    # =========================================================
    # FEZ REQUEST BODY
    # =========================================================

    payload = [
        {
            "recipientAddress": order.address,
            "recipientState": order.state,
            "recipientName": order.name,
            "recipientPhone": order.phone,
            "recipientEmail": order.email,
            # Unique Xeloos delivery reference
            "uniqueID": order.order_id,
            # Batch reference
            "BatchID": f"XEELOOS-{order.order_id}",
            "itemDescription": item_description,
            # Value of physical goods
            "valueOfItem": str(value_of_items),
            # Fez requires an integer KG value
            "weight": 1,
            # Customer already paid Xeloos
            "isItemCod": False,
            "fragile": False,
        }
    ]

    # =========================================================
    # AUTHENTICATE WITH FEZ
    # =========================================================

    auth_token, secret_key = authenticate_fez()

    if not auth_token or not secret_key:

        order.fez_status = "failed"

        order.save(update_fields=["fez_status"])

        return False

    # =========================================================
    # FEZ API
    # =========================================================

    url = f"{settings.FEZ_API_URL.rstrip('/')}/order"

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "secret-key": secret_key,
        "Content-Type": "application/json",
    }

    # Mark as processing before calling Fez.
    order.fez_status = "processing"

    order.save(update_fields=["fez_status"])

    # =========================================================
    # SEND REQUEST
    # =========================================================

    try:

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30,
        )

        try:
            response_data = response.json()

        except ValueError:

            print("FEZ ERROR: Invalid JSON response")

            print(
                "FEZ STATUS CODE:",
                response.status_code,
            )

            print(
                "FEZ RAW RESPONSE:",
                response.text,
            )

            order.fez_status = "failed"

            order.save(update_fields=["fez_status"])

            return False

    except requests.RequestException as exc:

        print(
            "FEZ DELIVERY REQUEST ERROR:",
            exc,
        )

        order.fez_status = "failed"

        order.save(update_fields=["fez_status"])

        return False

    # =========================================================
    # DEBUG RESPONSE
    # =========================================================

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

    print("===========================================")

    # =========================================================
    # HANDLE SUCCESS
    # =========================================================

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

    # =========================================================
    # FEZ CREATION FAILED
    # =========================================================

    print(
        "FEZ DELIVERY CREATION FAILED:",
        response_data,
    )

    order.fez_status = "failed"

    order.save(update_fields=["fez_status"])

    return False


# =========================================================
# DELETE / CANCEL FEZ DELIVERY
# =========================================================


def cancel_fez_delivery(order):
    """
    Delete/cancel an existing Fez delivery for a Xeloos order.

    Fez endpoint:
        DELETE /order

    Fez expects the Fez order number in the request body.

    Returns:
        True  -> delivery successfully deleted
        False -> deletion failed / no Fez order exists
    """

    # =========================================================
    # SAFETY CHECK
    # =========================================================

    # There is nothing to cancel if Fez never created
    # a delivery for this Xeloos order.
    if not order.fez_order_id:
        print(
            "FEZ CANCEL: No Fez order exists for:",
            order.order_id,
        )

        return False

    # =========================================================
    # AUTHENTICATE WITH FEZ
    # =========================================================

    auth_token, secret_key = authenticate_fez()

    if not auth_token or not secret_key:

        print("FEZ CANCEL: Authentication failed.")

        return False

    # =========================================================
    # FEZ API
    # =========================================================

    url = f"{settings.FEZ_API_URL.rstrip('/')}/order"

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "secret-key": secret_key,
        "Content-Type": "application/json",
    }

    payload = {
        "orderNo": str(order.fez_order_id),
    }

    # =========================================================
    # SEND DELETE REQUEST
    # =========================================================

    try:

        response = requests.delete(
            url,
            json=payload,
            headers=headers,
            timeout=30,
        )

        try:
            response_data = response.json()

        except ValueError:

            print("FEZ CANCEL ERROR: Invalid JSON response")

            print(
                "FEZ CANCEL STATUS CODE:",
                response.status_code,
            )

            print(
                "FEZ CANCEL RAW RESPONSE:",
                response.text,
            )

            return False

    except requests.RequestException as exc:

        print(
            "FEZ CANCEL REQUEST ERROR:",
            exc,
        )

        return False

    # =========================================================
    # DEBUG RESPONSE
    # =========================================================

    print("========== FEZ CANCEL RESPONSE ==========")

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
        "FEZ ORDER:",
        order.fez_order_id,
    )

    print("==========================================")

    # =========================================================
    # HANDLE SUCCESS
    # =========================================================

    if response.status_code == 200 and response_data.get("status") == "Success":

        order.fez_status = "cancelled"

        order.save(update_fields=["fez_status"])

        print(
            "FEZ DELIVERY SUCCESSFULLY CANCELLED:",
            order.fez_order_id,
        )

        return True

    # =========================================================
    # FEZ CANCELLATION FAILED
    # =========================================================

    print(
        "FEZ DELIVERY CANCELLATION FAILED:",
        response_data,
    )

    return False

# =========================================================
# TRACK FEZ DELIVERY
# =========================================================

def track_fez_delivery(order):
    """
    Fetch the current Fez delivery status for a Xeloos order.

    Fez endpoint:
        GET /order/track/{orderNumber}

    Returns:
        response_data -> Fez response dictionary
        None          -> request failed
    """

    # =========================================================
    # SAFETY CHECK
    # =========================================================

    if not order.fez_order_id:

        print(
            "FEZ TRACKING: No Fez order exists for:",
            order.order_id,
        )

        return None

    # =========================================================
    # AUTHENTICATE WITH FEZ
    # =========================================================

    auth_token, secret_key = authenticate_fez()

    if not auth_token or not secret_key:

        print(
            "FEZ TRACKING: Authentication failed."
        )

        return None

    # =========================================================
    # FEZ API
    # =========================================================

    url = (
        f"{settings.FEZ_API_URL.rstrip('/')}"
        f"/order/track/{order.fez_order_id}"
    )

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "secret-key": secret_key,
        "Content-Type": "application/json",
    }

    # =========================================================
    # SEND REQUEST
    # =========================================================

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )

        try:
            response_data = response.json()

        except ValueError:

            print(
                "FEZ TRACKING ERROR: Invalid JSON response"
            )

            print(
                "FEZ TRACKING STATUS CODE:",
                response.status_code,
            )

            print(
                "FEZ TRACKING RAW RESPONSE:",
                response.text,
            )

            return None

    except requests.RequestException as exc:

        print(
            "FEZ TRACKING REQUEST ERROR:",
            exc,
        )

        return None

    # =========================================================
    # DEBUG RESPONSE
    # =========================================================

    print(
        "========== FEZ TRACKING RESPONSE =========="
    )

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
        "FEZ ORDER:",
        order.fez_order_id,
    )

    print(
        "============================================"
    )

    # =========================================================
    # HANDLE FAILURE
    # =========================================================

    if (
        response.status_code != 200
        or response_data.get("status") != "Success"
    ):

        print(
            "FEZ TRACKING FAILED:",
            response_data,
        )

        return None

    # =========================================================
    # GET ORDER INFORMATION
    # =========================================================

    fez_order = response_data.get(
        "order",
        {}
    )

    current_status = fez_order.get(
        "orderStatus"
    )

    # =========================================================
    # UPDATE XEELOOS FEZ STATUS
    # =========================================================

    if current_status:

        order.fez_status = current_status

        order.save(
            update_fields=["fez_status"]
        )

    return response_data