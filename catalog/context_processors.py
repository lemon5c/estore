from .models import Category


def nav_categories(request):
    """Inject top-level categories into every template context."""
    categories = Category.objects.filter(is_active=True, parent=None).order_by("order", "name")
    return {"nav_categories": categories}
