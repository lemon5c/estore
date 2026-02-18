from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    """
    Product review. Any registered user can review.
    If they provide a valid order ID that contains the product and belongs to
    them (and is Delivered), they get a 'Verified Purchase' badge.
    """
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars",
    )
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField()

    # Verified purchase: user provides an order ID
    claimed_order_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Order ID the user claims as proof of purchase",
    )
    is_verified_purchase = models.BooleanField(
        default=False,
        help_text="Set automatically when claimed_order_id is validated",
    )

    is_approved = models.BooleanField(
        default=True,
        help_text="Owner can hide inappropriate reviews",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ["-created_at"]
        # One review per user per product
        unique_together = [["product", "user"]]

    def __str__(self):
        stars = "★" * self.rating + "☆" * (5 - self.rating)
        return f"{stars} {self.product.name} by {self.user}"

    def save(self, *args, **kwargs):
        # Auto-verify if claimed_order_id matches a delivered order
        # containing this product, belonging to this user
        if self.claimed_order_id:
            self.is_verified_purchase = self._validate_order()
        else:
            self.is_verified_purchase = False
        super().save(*args, **kwargs)

    def _validate_order(self) -> bool:
        """
        Check that:
        1. The order exists and belongs to this user
        2. The order is in 'delivered' status
        3. The order contains this product
        """
        try:
            from orders.models import Order
            order = Order.objects.get(pk=self.claimed_order_id, user=self.user)
            if order.status != Order.STATUS_DELIVERED:
                return False
            # Check if any order item's variant belongs to this product
            return order.items.filter(variant__product=self.product).exists()
        except Exception:
            return False
