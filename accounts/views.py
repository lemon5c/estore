from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .models import OTPCode
from .forms import (
    RegistrationStep1Form,
    OTPVerifyForm,
    RegistrationStep3Form,
    LoginForm,
    ProfileForm,
)
from .otp_service import send_otp

User = get_user_model()


# ─── Registration (3-step) ────────────────────────────────────────────────────

def register_step1(request):
    """Step 1: Enter phone + pick OTP channel."""
    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        form = RegistrationStep1Form(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["phone"]
            channel = form.cleaned_data["otp_channel"]

            # Create OTP
            otp = OTPCode.objects.create(
                phone=phone,
                purpose=OTPCode.OTP_PURPOSE_REGISTER,
                channel=channel,
            )
            send_otp(phone, otp.code, channel)

            # Store in session for next step
            request.session["reg_phone"] = phone
            request.session["reg_channel"] = channel

            messages.info(
                request,
                f"Verification code sent to {phone} via {channel.title()}.",
            )
            return redirect("accounts:register_step2")
    else:
        form = RegistrationStep1Form()

    return render(request, "accounts/register_step1.html", {"form": form})


def register_step2(request):
    """Step 2: Verify OTP."""
    phone = request.session.get("reg_phone")
    if not phone:
        return redirect("accounts:register_step1")

    if request.method == "POST":
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            otp = (
                OTPCode.objects.filter(
                    phone=phone,
                    code=code,
                    purpose=OTPCode.OTP_PURPOSE_REGISTER,
                    is_used=False,
                )
                .order_by("-created_at")
                .first()
            )

            if otp and otp.is_valid():
                otp.is_used = True
                otp.save()
                request.session["reg_verified"] = True
                return redirect("accounts:register_step3")
            else:
                form.add_error("code", "Invalid or expired code. Please try again.")
    else:
        form = OTPVerifyForm()

    return render(request, "accounts/register_step2.html", {"form": form, "phone": phone})


def register_step3(request):
    """Step 3: Set name, city, address, password."""
    phone = request.session.get("reg_phone")
    if not phone or not request.session.get("reg_verified"):
        return redirect("accounts:register_step1")

    if request.method == "POST":
        form = RegistrationStep3Form(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                phone=phone,
                password=form.cleaned_data["password1"],
                full_name=form.cleaned_data["full_name"],
                city=form.cleaned_data.get("city", ""),
                address=form.cleaned_data.get("address", ""),
                preferred_otp_channel=request.session.get("reg_channel", "whatsapp"),
            )
            # Clean up session
            for key in ("reg_phone", "reg_channel", "reg_verified"):
                request.session.pop(key, None)

            login(request, user, backend="accounts.backends.PhoneBackend")
            messages.success(request, f"Welcome, {user.get_short_name()}! Your account is ready.")
            return redirect("/")
    else:
        form = RegistrationStep3Form()

    return render(request, "accounts/register_step3.html", {"form": form})


# ─── Login / Logout ───────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["phone"]
            password = form.cleaned_data["password"]
            user = authenticate(request, phone=phone, password=password)
            if user:
                login(request, user)
                next_url = request.GET.get("next", "/")
                return redirect(next_url)
            else:
                form.add_error(None, "Invalid phone number or password.")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/")


# ─── Profile ──────────────────────────────────────────────────────────────────

@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            if request.htmx:
                return render(request, "accounts/_profile_form.html", {"form": form, "saved": True})
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})
