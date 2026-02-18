from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Category, Product, ProductVariant, Discount
from orders.models import Order
from reviews.models import Review


def homepage(request):
    """
    Amazon-style homepage with:
    - Latest Products
    - Active Discounts
    - Browse Categories
    - Best Sellers (featured products)
    """
    now = timezone.now()

    latest_products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images", "variants")
        .order_by("-created_at")[:12]
    )

    # Products with an active discount
    active_discount_ids = Discount.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now,
        product__isnull=False,
    ).values_list("product_id", flat=True)

    discounted_products = (
        Product.objects.filter(is_active=True, pk__in=active_discount_ids)
        .select_related("category")
        .prefetch_related("images", "variants", "discounts")[:12]
    )

    categories = Category.objects.filter(is_active=True, parent=None).order_by("order", "name")

    best_sellers = (
        Product.objects.filter(is_active=True, is_featured=True)
        .select_related("category")
        .prefetch_related("images", "variants")[:12]
    )

    return render(
        request,
        "catalog/homepage.html",
        {
            "latest_products": latest_products,
            "discounted_products": discounted_products,
            "categories": categories,
            "best_sellers": best_sellers,
        },
    )


def category_detail(request, slug):
    """List all active products in a category."""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = (
        Product.objects.filter(category=category, is_active=True)
        .prefetch_related("images", "variants")
        .order_by("-created_at")
    )

    # Include subcategory products
    subcategories = category.children.filter(is_active=True)

    return render(
        request,
        "catalog/category.html",
        {
            "category": category,
            "products": products,
            "subcategories": subcategories,
        },
    )


def product_detail(request, slug):
    """
    Single product page with:
    - Images
    - Variant selector (HTMX-powered stock check)
    - Add to cart
    - Reviews section
    """
    product = get_object_or_404(
        Product.objects.prefetch_related(
            "images",
            "variants__options__variant_type",
            "variant_types__options",
            "discounts",
            "reviews__user",
        ).select_related("category"),
        slug=slug,
        is_active=True,
    )

    variants = product.variants.filter(is_active=True)
    variant_types = product.variant_types.prefetch_related("options").all()

    # Reviews
    reviews = product.reviews.filter(is_approved=True).select_related("user").order_by("-created_at")
    review_count = reviews.count()
    avg_rating = None
    if review_count:
        avg_rating = round(sum(r.rating for r in reviews) / review_count, 1)

    # Check if current user has already reviewed
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()

    # Active order count for limit check
    active_order_count = 0
    if request.user.is_authenticated:
        active_order_count = Order.active_count_for_user(request.user)

    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "variants": variants,
            "variant_types": variant_types,
            "reviews": reviews,
            "review_count": review_count,
            "avg_rating": avg_rating,
            "user_review": user_review,
            "active_order_count": active_order_count,
            "max_active_orders": 5,
        },
    )


def variant_stock_check(request, variant_pk):
    """
    HTMX endpoint: returns stock info for a selected variant.
    Called when user selects options on product page.
    """
    variant = get_object_or_404(ProductVariant, pk=variant_pk, is_active=True)
    return render(
        request,
        "catalog/_variant_stock.html",
        {
            "variant": variant,
            "in_stock": variant.is_in_stock(),
        },
    )
