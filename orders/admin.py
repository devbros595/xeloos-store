from django.contrib import admin, messages

from .models import Order, OrderItem
from .services.fez import (
    cancel_fez_delivery,
    track_fez_delivery,
)


# =========================================================
# ORDER ITEMS INLINE
# =========================================================

class OrderItemInline(admin.TabularInline):

    model = OrderItem

    extra = 0

    can_delete = False

    fields = (
        "product_type",
        "product_id",
        "product_name",
        "product_price",
        "quantity",
    )

    readonly_fields = (
        "product_type",
        "product_id",
        "product_name",
        "product_price",
        "quantity",
    )


# =========================================================
# ORDER ADMIN
# =========================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    # -----------------------------------------------------
    # LIST DISPLAY
    # -----------------------------------------------------

    list_display = (
        "order_id",
        "name",
        "email",
        "total_price",
        "delivery_method",
        "delivery_fee",
        "payment_method",
        "status",
        "fez_status",
        "fez_order_id",
        "created_at",
    )

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    search_fields = (
        "order_id",
        "name",
        "email",
        "phone",
        "flutterwave_tx_ref",
        "flutterwave_transaction_id",
        "nowpayments_invoice_id",
        "nowpayments_payment_id",
        "fez_order_id",
    )

    # -----------------------------------------------------
    # FILTERS
    # -----------------------------------------------------

    list_filter = (
        "status",
        "payment_method",
        "delivery_method",
        "fez_status",
        "created_at",
    )

    # -----------------------------------------------------
    # DEFAULT SORTING
    # -----------------------------------------------------

    ordering = (
        "-created_at",
    )

    # -----------------------------------------------------
    # ACTIONS
    # -----------------------------------------------------

    actions = (
        "refresh_selected_fez_status",
        "cancel_selected_fez_deliveries",
    )

    # -----------------------------------------------------
    # READ-ONLY FIELDS
    # -----------------------------------------------------

    readonly_fields = (
        "order_id",
        "name",
        "email",
        "phone",
        "address",
        "city",
        "state",
        "created_at",
        "total_price",
        "delivery_method",
        "delivery_fee",
        "payment_method",
        "flutterwave_tx_ref",
        "flutterwave_transaction_id",
        "status",
        "nowpayments_invoice_id",
        "nowpayments_payment_id",
        "nowpayments_invoice_url",
        "fez_order_id",
        "fez_status",
    )

    # -----------------------------------------------------
    # INLINE ORDER ITEMS
    # -----------------------------------------------------

    inlines = (
        OrderItemInline,
    )

    # -----------------------------------------------------
    # FIELD ORGANIZATION
    # -----------------------------------------------------

    fieldsets = (

        (
            "Order Information",
            {
                "fields": (
                    "order_id",
                    "created_at",
                    "status",
                ),
            },
        ),

        (
            "Customer",
            {
                "fields": (
                    "name",
                    "email",
                    "phone",
                    "address",
                    "city",
                    "state",
                ),
            },
        ),

        (
            "Order Total",
            {
                "fields": (
                    "total_price",
                ),
            },
        ),

        (
            "Delivery",
            {
                "fields": (
                    "delivery_method",
                    "delivery_fee",
                ),
            },
        ),

        (
            "FEZ Delivery",
            {
                "fields": (
                    "fez_order_id",
                    "fez_status",
                ),
            },
        ),

        (
            "Payment",
            {
                "fields": (
                    "payment_method",
                    "flutterwave_tx_ref",
                    "flutterwave_transaction_id",
                    "nowpayments_invoice_id",
                    "nowpayments_payment_id",
                    "nowpayments_invoice_url",
                ),
            },
        ),
    )

    # -----------------------------------------------------
    # CANCEL FEZ DELIVERIES
    # -----------------------------------------------------

    @admin.action(
        description="Cancel selected FEZ deliveries"
    )

    def refresh_selected_fez_status(
        self,
        request,
        queryset,
    ):

        success_count = 0
        failed_count = 0
        skipped_count = 0

        for order in queryset:

            # -------------------------------------------------
            # No FEZ delivery
            # -------------------------------------------------

            if not order.fez_order_id:

                skipped_count += 1

                self.message_user(
                    request,
                    (
                        f"Order {order.order_id} "
                        "has no FEZ delivery."
                    ),
                    level=messages.WARNING,
                )

                continue

            # -------------------------------------------------
            # Cancelled delivery
            # -------------------------------------------------

            if order.fez_status == "cancelled":

                skipped_count += 1

                self.message_user(
                    request,
                    (
                        f"FEZ delivery for "
                        f"{order.order_id} is cancelled."
                    ),
                    level=messages.WARNING,
                )

                continue

            # -------------------------------------------------
            # Fetch FEZ status
            # -------------------------------------------------

            response_data = track_fez_delivery(order)

            if response_data:

                fez_order = response_data.get(
                    "order",
                    {}
                )

                current_status = fez_order.get(
                    "orderStatus",
                    "Unknown",
                )

                success_count += 1

                self.message_user(
                    request,
                    (
                        f"Order {order.order_id}: "
                        f"FEZ status is now "
                        f"'{current_status}'."
                    ),
                    level=messages.SUCCESS,
                )

            else:

                failed_count += 1

                self.message_user(
                    request,
                    (
                        f"Could not retrieve FEZ status "
                        f"for {order.order_id}."
                    ),
                    level=messages.ERROR,
                )

        # -----------------------------------------------------
        # Summary
        # -----------------------------------------------------

        if success_count:

            self.message_user(
                request,
                (
                    f"{success_count} FEZ "
                    f"{'delivery' if success_count == 1 else 'deliveries'} "
                    "successfully refreshed."
                ),
                level=messages.SUCCESS,
            )

        if failed_count:

            self.message_user(
                request,
                (
                    f"{failed_count} FEZ status "
                    f"{'request' if failed_count == 1 else 'requests'} "
                    "failed."
                ),
                level=messages.ERROR,
            )

        if skipped_count:

            self.message_user(
                request,
                (
                    f"{skipped_count} order "
                    f"{'was' if skipped_count == 1 else 'were'} "
                    "skipped."
                ),
                level=messages.WARNING,
            )

    def cancel_selected_fez_deliveries(
        self,
        request,
        queryset,
    ):

        success_count = 0
        failed_count = 0
        skipped_count = 0

        for order in queryset:

            # -------------------------------------------------
            # No FEZ delivery
            # -------------------------------------------------

            if not order.fez_order_id:

                skipped_count += 1

                self.message_user(
                    request,
                    (
                        f"Order {order.order_id} "
                        "has no FEZ delivery."
                    ),
                    level=messages.WARNING,
                )

                continue

            # -------------------------------------------------
            # Already cancelled
            # -------------------------------------------------

            if order.fez_status == "cancelled":

                skipped_count += 1

                self.message_user(
                    request,
                    (
                        f"FEZ delivery for "
                        f"{order.order_id} is already cancelled."
                    ),
                    level=messages.WARNING,
                )

                continue

            # -------------------------------------------------
            # Attempt cancellation
            # -------------------------------------------------

            success = cancel_fez_delivery(order)

            if success:

                success_count += 1

            else:

                failed_count += 1

        # -----------------------------------------------------
        # Summary
        # -----------------------------------------------------

        if success_count:

            self.message_user(
                request,
                (
                    f"{success_count} FEZ delivery "
                    f"{'was' if success_count == 1 else 'were'} "
                    "successfully cancelled."
                ),
                level=messages.SUCCESS,
            )

        if failed_count:

            self.message_user(
                request,
                (
                    f"{failed_count} FEZ delivery "
                    f"{'cancellation' if failed_count == 1 else 'cancellations'} "
                    "failed."
                ),
                level=messages.ERROR,
            )

        if skipped_count:

            self.message_user(
                request,
                (
                    f"{skipped_count} order "
                    f"{'was' if skipped_count == 1 else 'were'} "
                    "skipped."
                ),
                level=messages.WARNING,
            )


# =========================================================
# ORDER ITEM ADMIN
# =========================================================

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "order",
        "product_name",
        "product_type",
        "product_price",
        "quantity",
    )

    search_fields = (
        "order__order_id",
        "product_name",
    )

    list_filter = (
        "product_type",
    )

    ordering = (
        "-order__created_at",
    )

    readonly_fields = (
        "order",
        "product_type",
        "product_id",
        "product_name",
        "product_price",
        "quantity",
    )