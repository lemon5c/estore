from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, VariantType, VariantOption, ProductVariant, Discount


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "order", "is_active", "product_count")
    list_filter = ("is_active", "parent")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")

    def product_count(self, obj):
        return obj.products.filter(is_active=True).count()
    product_count.short_description = "Active Products"


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt_text", "is_primary", "order", "image_preview")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="60" />', obj.image.url)
        return "-"
    image_preview.short_description = "Preview"


class VariantTypeInline(admin.TabularInline):
    model = VariantType
    extra = 1
    fields = ("name", "order")


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("sku", "options", "price_override", "stock_qty", "is_active", "image")
    filter_horizontal = ("options",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "category", "base_price", "total_stock",
        "is_active", "is_featured", "created_at"
    )
    list_filter = ("is_active", "is_featured", "category")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-created_at",)
    inlines = [ProductImageInline, VariantTypeInline, ProductVariantInline]
    list_editable = ("is_active", "is_featured")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("category", "name", "slug", "description")}),
        ("Pricing", {"fields": ("base_price",)}),
        ("Visibility", {"fields": ("is_active", "is_featured")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def total_stock(self, obj):
        stock = obj.total_stock()
        if stock == 0:
            return format_html('<span style="color:red;font-weight:bold">0</span>')
        return stock
    total_stock.short_description = "Total Stock"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("__str__", "product", "sku", "price", "stock_qty", "is_active")
    list_filter = ("is_active", "product__category")
    search_fields = ("sku", "product__name")
    filter_horizontal = ("options",)
    list_editable = ("stock_qty", "is_active")


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = (
        "name", "discount_type", "value", "product", "category",
        "start_date", "end_date", "is_active", "is_currently_active"
    )
    list_filter = ("is_active", "discount_type")
    search_fields = ("name",)
    list_editable = ("is_active",)

    def is_currently_active(self, obj):
        active = obj.is_currently_active()
        color = "green" if active else "gray"
        label = "Live" if active else "Inactive"
        return format_html('<span style="color:{}">{}</span>', color, label)
    is_currently_active.short_description = "Live?"
