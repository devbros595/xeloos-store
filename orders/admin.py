from django.contrib import admin
from .models import Order, OrderItem


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
    )

    # -----------------------------------------------------
    # FILTERS
    # -----------------------------------------------------

    list_filter = (
        "status",
        "payment_method",
        "delivery_method",
        "created_at",
    )

    # -----------------------------------------------------
    # DEFAULT SORTING
    # -----------------------------------------------------

    ordering = (
        "-created_at",
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
