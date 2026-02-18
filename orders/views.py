from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.conf import settings

from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory
from catalog.models import ProductVariant


def _get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


# ─── Cart ─────────────────────────────────────────────────────────────────────

@login_required
def cart_view(request):
    cart = _get_or_create_cart(request.user)
    active_order_count = Order.active_count_for_user(request.user)
    max_orders = getattr(settings, "MAX_ACTIVE_ORDERS", 5)
    at_limit = active_order_count >= max_orders

    return render(
        request,
        "orders/cart.html",
        {
            "cart": cart,
            "active_order_count": active_order_count,
            "at_limit": at_limit,
            "max_orders": max_orders,
        },
    )


@login_required
@require_POST
def add_to_cart(request, variant_pk):
    variant = get_object_or_404(ProductVariant, pk=variant_pk, is_active=True)

    if not variant.is_in_stock():
        messages.error(request, "Sorry, this item is out of stock.")
        if request.htmx:
            return HttpResponse(
                '<span class="text-red-600 font-semibold">Out of stock</span>',
                content_type="text/html",
            )
        return redirect(variant.product.get_absolute_url())

    cart = _get_or_create_cart(request.user)
    quantity = int(request.POST.get("quantity", 1))
    quantity = max(1, min(quantity, variant.stock_qty))

    item, created = CartItem.objects.get_or_create(cart=cart, variant=variant)
    if not created:
        new_qty = min(item.quantity + quantity, variant.stock_qty)
        item.quantity = new_qty
        item.save()
    else:
        item.quantity = quantity
        item.save()

    messages.success(request, f"Added {variant.product.name} to your cart.")

    if request.htmx:
        cart.refresh_from_db()
        return render(request, "orders/_cart_count.html", {"cart": cart})

    return redirect("orders:cart")


@login_required
@require_POST
def update_cart_item(request, item_pk):
    item = get_object_or_404(CartItem, pk=item_pk, cart__user=request.user)
    action = request.POST.get("action")

    if action == "increase":
        if item.quantity < item.variant.stock_qty:
            item.quantity += 1
            item.save()
    elif action == "decrease":
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
            if request.htmx:
                cart = _get_or_create_cart(request.user)
                return render(request, "orders/_cart_items.html", {"cart": cart})
    elif action == "remove":
        item.delete()
        if request.htmx:
            cart = _get_or_create_cart(request.user)
            return render(request, "orders/_cart_items.html", {"cart": cart})

    if request.htmx:
        cart = _get_or_create_cart(request.user)
        return render(request, "orders/_cart_items.html", {"cart": cart})

    return redirect("orders:cart")


# ─── Checkout / Request Order ──────────────────────────────────────────────────

@login_required
def request_order(request):
    """
    Convert cart to an Order.
    Enforces the 5-active-orders limit.
    Sends WhatsApp notification to owner.
    """
    cart = _get_or_create_cart(request.user)

    if cart.is_empty():
        messages.error(request, "Your cart is empty.")
        return redirect("orders:cart")

    active_count = Order.active_count_for_user(request.user)
    max_orders = getattr(settings, "MAX_ACTIVE_ORDERS", 5)

    if active_count >= max_orders:
        messages.warning(
            request,
            f"You have {active_count} active orders. "
            f"Please wait for them to complete before placing a new order.",
        )
        return redirect("orders:cart")

    if request.method == "POST":
        notes = request.POST.get("notes", "")

        # Validate stock one more time
        stock_errors = []
        for item in cart.items.select_related("variant__product"):
            if item.quantity > item.variant.stock_qty:
                stock_errors.append(
                    f"{item.variant.product.name}: only {item.variant.stock_qty} left in stock."
                )

        if stock_errors:
            for err in stock_errors:
                messages.error(request, err)
            return redirect("orders:cart")

        # Create the order
        order = Order.objects.create(
            user=request.user,
            status=Order.STATUS_PENDING,
            notes=notes,
            delivery_address=request.user.address,
        )

        # Move cart items to order items + deduct stock
        for item in cart.items.select_related("variant__product"):
            OrderItem.objects.create(
                order=order,
                variant=item.variant,
                quantity=item.quantity,
                price_at_order=item.variant.effective_price(),
            )
            # Deduct stock
            item.variant.stock_qty -= item.quantity
            item.variant.save(update_fields=["stock_qty"])

        # Log initial status
        OrderStatusHistory.objects.create(
            order=order,
            status=Order.STATUS_PENDING,
            changed_by=request.user,
            note="Order placed by customer.",
        )

        # Clear cart
        cart.items.all().delete()

        # Notify owner via WhatsApp
        try:
            from accounts.otp_service import notify_owner_new_order
            notified = notify_owner_new_order(order)
            if notified:
                order.whatsapp_notified = True
                order.save(update_fields=["whatsapp_notified"])
        except Exception:
            pass  # Notification failure should not block the order

        messages.success(
            request,
            f"Order #{order.pk} placed successfully! "
            "The owner will contact you shortly.",
        )
        return redirect("orders:order_detail", pk=order.pk)

    # GET: show confirmation page
    return render(
        request,
        "orders/request_order.html",
        {
            "cart": cart,
            "active_count": active_count,
            "max_orders": max_orders,
        },
    )


# ─── Order Detail / Tracking ───────────────────────────────────────────────────

@login_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items__variant__product",
            "items__variant__options__variant_type",
            "history",
            "packing_photos",
        ),
        pk=pk,
        user=request.user,
    )
    return render(request, "orders/order_detail.html", {"order": order})


@login_required
def my_orders(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__variant__product")
        .order_by("-created_at")
    )
    return render(request, "orders/my_orders.html", {"orders": orders})


@login_required
@require_POST
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)

    if not order.can_customer_cancel():
        messages.error(
            request,
            "This order can no longer be cancelled. "
            "Please contact the store owner.",
        )
        return redirect("orders:order_detail", pk=pk)

    # Restore stock
    for item in order.items.select_related("variant"):
        item.variant.stock_qty += item.quantity
        item.variant.save(update_fields=["stock_qty"])

    old_status = order.status
    order.status = Order.STATUS_DECLINED
    order.save()

    OrderStatusHistory.objects.create(
        order=order,
        status=Order.STATUS_DECLINED,
        changed_by=request.user,
        note="Order cancelled by customer.",
    )

    messages.success(request, f"Order #{pk} has been cancelled.")
    return redirect("orders:my_orders")
