from django.contrib import admin
from django.utils.html import format_html
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "product", "user_phone", "star_rating", "is_verified_purchase",
        "is_approved", "created_at",
    )
    list_filter = ("is_verified_purchase", "is_approved", "rating")
    search_fields = ("product__name", "user__phone", "user__full_name", "body")
    readonly_fields = ("is_verified_purchase", "created_at", "updated_at")
    list_editable = ("is_approved",)
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Review",
            {"fields": ("product", "user", "rating", "title", "body")},
        ),
        (
            "Verification",
            {"fields": ("claimed_order_id", "is_verified_purchase")},
        ),
        (
            "Moderation",
            {"fields": ("is_approved",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def user_phone(self, obj):
        return obj.user.phone
    user_phone.short_description = "Customer Phone"
    user_phone.admin_order_field = "user__phone"

    def star_rating(self, obj):
        stars = "★" * obj.rating + "☆" * (5 - obj.rating)
        return format_html('<span style="color:#f59e0b;font-size:16px">{}</span>', stars)
    star_rating.short_description = "Rating"
    star_rating.admin_order_field = "rating"

    actions = ["approve_reviews", "hide_reviews"]

    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} review(s) approved.")
    approve_reviews.short_description = "Approve selected reviews"

    def hide_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} review(s) hidden.")
    hide_reviews.short_description = "Hide selected reviews"
