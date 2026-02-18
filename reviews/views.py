from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Review
from catalog.models import Product


@login_required
@require_POST
def submit_review(request, product_slug):
    """Submit or update a review for a product."""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)

    rating = int(request.POST.get("rating", 0))
    title = request.POST.get("title", "").strip()
    body = request.POST.get("body", "").strip()
    claimed_order_id = request.POST.get("claimed_order_id", "").strip()

    if not body:
        messages.error(request, "Review body cannot be empty.")
        return redirect(product.get_absolute_url())

    if not (1 <= rating <= 5):
        messages.error(request, "Please select a rating between 1 and 5.")
        return redirect(product.get_absolute_url())

    # Parse claimed order ID
    order_id = None
    if claimed_order_id:
        try:
            order_id = int(claimed_order_id)
        except ValueError:
            messages.error(request, "Invalid order ID.")
            return redirect(product.get_absolute_url())

    review, created = Review.objects.update_or_create(
        product=product,
        user=request.user,
        defaults={
            "rating": rating,
            "title": title,
            "body": body,
            "claimed_order_id": order_id,
        },
    )

    if created:
        messages.success(request, "Your review has been submitted. Thank you!")
    else:
        messages.success(request, "Your review has been updated.")

    if review.is_verified_purchase:
        messages.info(request, "✓ Your review is marked as a Verified Purchase.")

    return redirect(product.get_absolute_url())


@login_required
@require_POST
def delete_review(request, product_slug):
    """Delete user's own review."""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    review = get_object_or_404(Review, product=product, user=request.user)
    review.delete()
    messages.success(request, "Your review has been removed.")
    return redirect(product.get_absolute_url())
