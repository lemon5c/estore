from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path("category/<slug:slug>/", views.category_detail, name="category"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("variant/<int:variant_pk>/stock/", views.variant_stock_check, name="variant_stock"),
]
