import random
import string
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta


class UserManager(BaseUserManager):
    """Custom manager where phone is the unique identifier."""

    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Phone number is required")
        extra_fields.setdefault("is_active", True)
        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(phone, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model using phone number as the primary identifier.
    Username field is replaced by phone.
    """

    username = None  # Remove default username field
    phone = models.CharField(max_length=20, unique=True, verbose_name="Phone Number")
    full_name = models.CharField(max_length=150, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True, verbose_name="Delivery Address")
    preferred_otp_channel = models.CharField(
        max_length=10,
        choices=[("whatsapp", "WhatsApp"), ("sms", "SMS")],
        default="whatsapp",
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []  # No email required

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.full_name or 'User'} ({self.phone})"

    def get_full_name(self):
        return self.full_name or self.phone

    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else self.phone


def generate_otp():
    """Generate a 6-digit numeric OTP."""
    return "".join(random.choices(string.digits, k=6))


class OTPCode(models.Model):
    """
    One-time password for phone verification / login.
    """

    OTP_PURPOSE_REGISTER = "register"
    OTP_PURPOSE_LOGIN = "login"
    OTP_PURPOSE_RESET = "reset"

    PURPOSE_CHOICES = [
        (OTP_PURPOSE_REGISTER, "Registration"),
        (OTP_PURPOSE_LOGIN, "Login"),
        (OTP_PURPOSE_RESET, "Password Reset"),
    ]

    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=6, default=generate_otp)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default=OTP_PURPOSE_LOGIN)
    channel = models.CharField(
        max_length=10,
        choices=[("whatsapp", "WhatsApp"), ("sms", "SMS")],
        default="whatsapp",
    )
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = "OTP Code"
        verbose_name_plural = "OTP Codes"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            from django.conf import settings
            minutes = getattr(settings, "OTP_EXPIRY_MINUTES", 10)
            self.expires_at = timezone.now() + timedelta(minutes=minutes)
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP {self.code} for {self.phone} ({self.purpose})"
