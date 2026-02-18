from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Cart(models.Model):
    """
    Persistent cart tied to a logged-in user.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user}"

    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def total_price(self):
        return sum(item.subtotal() for item in self.items.select_related("variant__product"))

    def is_empty(self):
        return not self.items.exists()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["cart", "variant"]]

    def subtotal(self):
        return self.variant.effective_price() * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.variant} in {self.cart}"


class Order(models.Model):
    """
    An order placed by a customer via "Request Order".
    """

    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_PAYMENT_RECEIVED = "payment_received"
    STATUS_PACKING = "packing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_DECLINED = "declined"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_PAYMENT_RECEIVED, "Payment Received"),
        (STATUS_PACKING, "Packing"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_DECLINED, "Declined"),
    ]

    # Statuses where the customer can no longer cancel
    LOCKED_STATUSES = {
        STATUS_PROCESSING,
        STATUS_PAYMENT_RECEIVED,
        STATUS_PACKING,
        STATUS_SHIPPED,
        STATUS_DELIVERED,
        STATUS_DECLINED,
    }

    # Statuses that count towards the "active orders" limit
    ACTIVE_STATUSES = {
        STATUS_PENDING,
        STATUS_PROCESSING,
        STATUS_PAYMENT_RECEIVED,
        STATUS_PACKING,
        STATUS_SHIPPED,
    }

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    notes = models.TextField(blank=True, help_text="Customer notes for the order")
    delivery_address = models.TextField(
        blank=True,
        help_text="Snapshot of delivery address at order time",
    )
    whatsapp_notified = models.BooleanField(
        default=False,
        help_text="Whether owner was notified via WhatsApp",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} — {self.user} [{self.get_status_display()}]"

    def total_price(self):
        return sum(item.subtotal() for item in self.items.all())

    def can_customer_cancel(self):
        return self.status == self.STATUS_PENDING

    def is_active(self):
        return self.status in self.ACTIVE_STATUSES

    @classmethod
    def active_count_for_user(cls, user):
        return cls.objects.filter(user=user, status__in=cls.ACTIVE_STATUSES).count()

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("orders:order_detail", kwargs={"pk": self.pk})


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField()
    price_at_order = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Effective price at the time of order (after discount)",
    )

    def subtotal(self):
        return self.price_at_order * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.variant} (Order #{self.order_id})"


class OrderStatusHistory(models.Model):
    """
    Audit trail for every status change on an order.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history")
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="status_changes",
    )
    note = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status History"
        ordering = ["timestamp"]

    def __str__(self):
        return f"Order #{self.order_id} → {self.status} at {self.timestamp:%Y-%m-%d %H:%M}"


class PackingPhoto(models.Model):
    """
    Photo uploaded by owner before wrapping, for customer confirmation.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="packing_photos")
    image = models.ImageField(upload_to="packing/")
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="packing_photos_uploaded",
    )

    class Meta:
        verbose_name = "Packing Photo"
        verbose_name_plural = "Packing Photos"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"Packing photo for Order #{self.order_id}"
