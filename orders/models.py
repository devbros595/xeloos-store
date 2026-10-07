from django.db import models
import uuid
from django.conf import settings


class Order(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending Payment"),
        ("paid", "Payment Received"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("flutterwave", "Flutterwave"),
        ("nowpayments", "NOWPayments"),
    ]

    order_id = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    name = models.CharField(max_length=100)

    email = models.EmailField(max_length=100)

    phone = models.CharField(max_length=100)

    address = models.TextField(max_length=100)

    city = models.CharField(max_length=100)

    state = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    # ---------------------------------------------
    # ORDER TOTAL
    # ---------------------------------------------

    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    # ---------------------------------------------
    # DELIVERY
    # ---------------------------------------------

    delivery_method = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )

    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    # ---------------------------------------------
    # PAYMENT
    # ---------------------------------------------

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        default="",
    )

    flutterwave_tx_ref = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
    )

    flutterwave_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    nowpayments_invoice_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    nowpayments_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    nowpayments_invoice_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
    )

    fez_order_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    fez_tracking_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    fez_status = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )

    # ---------------------------------------------
    # STATUS
    # ---------------------------------------------

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    def save(self, *args, **kwargs):

        if not self.order_id:
            self.order_id = uuid.uuid4().hex[:10].upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_id}"


class OrderItem(models.Model):

    PRODUCT_TYPE_CHOICES = [
        ("sim", "Physical SIM"),
        ("product", "Digital Product"),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
    )

    product_id = models.PositiveIntegerField()

    product_name = models.CharField(max_length=200)

    product_price = models.DecimalField(max_digits=10, decimal_places=2)

    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product_name} " f"x {self.quantity}"
