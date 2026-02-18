from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory, PackingPhoto


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("variant", "quantity", "price_at_order", "subtotal_display")
    can_delete = False

    def subtotal_display(self, obj):
        return f"{obj.subtotal():.2f} LYD"
    subtotal_display.short_description = "Subtotal"


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("status", "changed_by", "note", "timestamp")
    can_delete = False
    ordering = ("timestamp",)


class PackingPhotoInline(admin.TabularInline):
    model = PackingPhoto
    extra = 1
    fields = ("image", "caption", "photo_preview", "uploaded_at")
    readonly_fields = ("photo_preview", "uploaded_at")

    def photo_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="100" />', obj.image.url)
        return "-"
    photo_preview.short_description = "Preview"


# Status transition map: current → allowed next statuses (for owner)
STATUS_TRANSITIONS = {
    Order.STATUS_PENDING: [Order.STATUS_PROCESSING, Order.STATUS_DECLINED],
    Order.STATUS_PROCESSING: [Order.STATUS_PAYMENT_RECEIVED, Order.STATUS_DECLINED],
    Order.STATUS_PAYMENT_RECEIVED: [Order.STATUS_PACKING],
    Order.STATUS_PACKING: [Order.STATUS_SHIPPED],
    Order.STATUS_SHIPPED: [Order.STATUS_DELIVERED],
    Order.STATUS_DELIVERED: [],
    Order.STATUS_DECLINED: [],
}

STATUS_COLORS = {
    Order.STATUS_PENDING: "#f59e0b",       # amber
    Order.STATUS_PROCESSING: "#3b82f6",    # blue
    Order.STATUS_PAYMENT_RECEIVED: "#8b5cf6",  # purple
    Order.STATUS_PACKING: "#ec4899",       # pink
    Order.STATUS_SHIPPED: "#06b6d4",       # cyan
    Order.STATUS_DELIVERED: "#10b981",     # green
    Order.STATUS_DECLINED: "#ef4444",      # red
}


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number", "user_info", "status_badge", "total_price_display",
        "whatsapp_notified", "created_at",
    )
    list_filter = ("status", "whatsapp_notified", "created_at")
    search_fields = ("user__phone", "user__full_name", "pk")
    readonly_fields = (
        "user", "created_at", "updated_at", "total_price_display",
        "whatsapp_notified", "status_action_buttons",
    )
    ordering = ("-created_at",)
    inlines = [OrderItemInline, PackingPhotoInline, OrderStatusHistoryInline]

    fieldsets = (
        (
            "Order Info",
            {
                "fields": (
                    "user", "status", "status_action_buttons",
                    "delivery_address", "notes", "total_price_display",
                )
            },
        ),
        (
            "Notifications",
            {"fields": ("whatsapp_notified",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:order_pk>/change-status/<str:new_status>/",
                self.admin_site.admin_view(self.change_status_view),
                name="orders_order_change_status",
            ),
        ]
        return custom_urls + urls

    def change_status_view(self, request, order_pk, new_status):
        order = get_object_or_404(Order, pk=order_pk)
        allowed = STATUS_TRANSITIONS.get(order.status, [])

        if new_status not in allowed:
            messages.error(
                request,
                f"Cannot transition order #{order_pk} from '{order.get_status_display()}' "
                f"to '{new_status}'.",
            )
        else:
            old_status = order.status
            order.status = new_status
            order.save()
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                changed_by=request.user,
                note=f"Status changed from {old_status} to {new_status} by admin.",
            )
            messages.success(
                request,
                f"Order #{order_pk} status updated to '{order.get_status_display()}'.",
            )

        return redirect(
            reverse("admin:orders_order_change", kwargs={"object_id": order_pk})
        )

    def status_action_buttons(self, obj):
        if not obj.pk:
            return "-"
        allowed = STATUS_TRANSITIONS.get(obj.status, [])
        if not allowed:
            return format_html('<em style="color:gray">No further transitions available</em>')

        buttons = []
        status_labels = dict(Order.STATUS_CHOICES)
        for next_status in allowed:
            url = reverse(
                "admin:orders_order_change_status",
                kwargs={"order_pk": obj.pk, "new_status": next_status},
            )
            color = STATUS_COLORS.get(next_status, "#6b7280")
            label = status_labels.get(next_status, next_status)
            buttons.append(
                format_html(
                    '<a href="{}" style="'
                    'display:inline-block;margin:2px 4px;padding:6px 14px;'
                    'background:{};color:white;border-radius:4px;'
                    'text-decoration:none;font-size:13px;font-weight:bold;">'
                    '→ {}</a>',
                    url, color, label,
                )
            )
        return format_html("".join(str(b) for b in buttons))

    status_action_buttons.short_description = "Change Status"

    def order_number(self, obj):
        return format_html("<strong>#{}</strong>", obj.pk)
    order_number.short_description = "Order"
    order_number.admin_order_field = "pk"

    def user_info(self, obj):
        return format_html(
            "{}<br><small>{}</small>",
            obj.user.get_full_name(),
            obj.user.phone,
        )
    user_info.short_description = "Customer"
    user_info.admin_order_field = "user__full_name"

    def status_badge(self, obj):
        color = STATUS_COLORS.get(obj.status, "#6b7280")
        return format_html(
            '<span style="'
            'background:{};color:white;padding:3px 10px;'
            'border-radius:12px;font-size:12px;font-weight:bold;">'
            "{}</span>",
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    def total_price_display(self, obj):
        if obj.pk:
            return f"{obj.total_price():.2f} LYD"
        return "-"
    total_price_display.short_description = "Total"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "total_items", "total_price_display", "updated_at")
    search_fields = ("user__phone", "user__full_name")
    readonly_fields = ("created_at", "updated_at")

    def total_price_display(self, obj):
        return f"{obj.total_price():.2f} LYD"
    total_price_display.short_description = "Cart Total"
