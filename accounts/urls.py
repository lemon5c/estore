from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_step1, name="register_step1"),
    path("register/verify/", views.register_step2, name="register_step2"),
    path("register/complete/", views.register_step3, name="register_step3"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
]
