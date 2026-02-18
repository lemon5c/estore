from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:variant_pk>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:item_pk>/", views.update_cart_item, name="update_cart_item"),
    path("request/", views.request_order, name="request_order"),
    path("my-orders/", views.my_orders, name="my_orders"),
    path("<int:pk>/", views.order_detail, name="order_detail"),
    path("<int:pk>/cancel/", views.cancel_order, name="cancel_order"),
]
