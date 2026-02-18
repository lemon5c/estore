from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    order = models.PositiveIntegerField(default=0, help_text="Display order on homepage")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("catalog:category", kwargs={"slug": self.slug})

    def active_product_count(self):
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Default price. Variants can override this.",
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(
        default=False,
        help_text="Show in Best Sellers section on homepage",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})

    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

    def active_discount(self):
        """Return the best active discount for this product."""
        now = timezone.now()
        # Check product-specific discounts first, then category discounts
        discount = (
            Discount.objects.filter(
                product=self,
                is_active=True,
                start_date__lte=now,
                end_date__gte=now,
            )
            .order_by("-value")
            .first()
        )
        if not discount:
            discount = (
                Discount.objects.filter(
                    category=self.category,
                    is_active=True,
                    start_date__lte=now,
                    end_date__gte=now,
                )
                .order_by("-value")
                .first()
            )
        return discount

    def discounted_price(self, base=None):
        """Return price after discount, or None if no discount."""
        discount = self.active_discount()
        if not discount:
            return None
        price = base or self.base_price
        return discount.apply(price)

    def total_stock(self):
        return sum(v.stock_qty for v in self.variants.filter(is_active=True))


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-is_primary", "order"]

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class VariantType(models.Model):
    """
    A dimension along which a product varies.
    e.g., "Color", "Size", "Material"
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variant_types",
    )
    name = models.CharField(max_length=50, help_text='e.g. "Color", "Size"')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        unique_together = [["product", "name"]]

    def __str__(self):
        return f"{self.product.name} → {self.name}"


class VariantOption(models.Model):
    """
    A specific value for a VariantType.
    e.g., "Red", "XL", "Cotton"
    """
    variant_type = models.ForeignKey(
        VariantType,
        on_delete=models.CASCADE,
        related_name="options",
    )
    value = models.CharField(max_length=100, help_text='e.g. "Red", "XL"')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "value"]
        unique_together = [["variant_type", "value"]]

    def __str__(self):
        return f"{self.variant_type.name}: {self.value}"


class ProductVariant(models.Model):
    """
    A specific purchasable combination of variant options.
    e.g., Color=Red + Size=XL
    Stock is tracked per variant.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    options = models.ManyToManyField(
        VariantOption,
        blank=True,
        related_name="variants",
        help_text="Select one option per variant type",
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        help_text="Leave blank to auto-generate",
    )
    price_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Leave blank to use product base price",
    )
    stock_qty = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(
        upload_to="variants/",
        null=True,
        blank=True,
        help_text="Optional variant-specific image",
    )

    class Meta:
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"

    def save(self, *args, **kwargs):
        if not self.sku:
            import uuid
            self.sku = f"{self.product.slug}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def price(self):
        """Return effective price (override or base price)."""
        return self.price_override if self.price_override is not None else self.product.base_price

    def discounted_price(self):
        return self.product.discounted_price(base=self.price())

    def effective_price(self):
        """Final price after any discount."""
        d = self.discounted_price()
        return d if d is not None else self.price()

    def options_display(self):
        """e.g. 'Color: Red, Size: XL'"""
        return ", ".join(
            f"{opt.variant_type.name}: {opt.value}"
            for opt in self.options.select_related("variant_type").all()
        )

    def is_in_stock(self):
        return self.stock_qty > 0

    def __str__(self):
        opts = self.options_display()
        return f"{self.product.name} — {opts or 'Default'} (Stock: {self.stock_qty})"


class Discount(models.Model):
    """
    A discount that can apply to a specific product or a whole category.
    """
    DISCOUNT_TYPE_PERCENT = "percent"
    DISCOUNT_TYPE_FIXED = "fixed"

    TYPE_CHOICES = [
        (DISCOUNT_TYPE_PERCENT, "Percentage (%)"),
        (DISCOUNT_TYPE_FIXED, "Fixed Amount (LYD)"),
    ]

    name = models.CharField(max_length=100, help_text="Internal label, e.g. 'Summer Sale'")
    discount_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=DISCOUNT_TYPE_PERCENT)
    value = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Percentage (0-100) or fixed LYD amount",
    )
    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="discounts",
        help_text="Leave blank for category-wide discount",
    )
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="discounts",
        help_text="Leave blank for product-specific discount",
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Discount"
        verbose_name_plural = "Discounts"
        ordering = ["-start_date"]

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.product and not self.category:
            raise ValidationError("Discount must be linked to a product or a category.")
        if self.product and self.category:
            raise ValidationError("Discount cannot be linked to both a product and a category.")

    def apply(self, price):
        """Return discounted price."""
        from decimal import Decimal
        if self.discount_type == self.DISCOUNT_TYPE_PERCENT:
            return round(price * (1 - self.value / Decimal("100")), 2)
        else:
            return max(Decimal("0"), price - self.value)

    def is_currently_active(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

    def __str__(self):
        target = self.product or self.category
        return f"{self.name} ({self.value}{'%' if self.discount_type == 'percent' else ' LYD'}) → {target}"
