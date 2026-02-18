from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

User = get_user_model()

phone_validator = RegexValidator(
    regex=r"^\+?[0-9]{7,15}$",
    message="Enter a valid phone number (e.g. +218912345678)",
)


class RegistrationStep1Form(forms.Form):
    """Step 1: Enter phone number + choose OTP channel."""
    phone = forms.CharField(
        max_length=20,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            "placeholder": "+218 91 234 5678",
            "class": "input-field",
            "autofocus": True,
        }),
        label="Phone Number",
    )
    otp_channel = forms.ChoiceField(
        choices=[("whatsapp", "WhatsApp"), ("sms", "SMS")],
        initial="whatsapp",
        widget=forms.RadioSelect(attrs={"class": "radio-field"}),
        label="Send verification via",
    )

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("This phone number is already registered.")
        return phone


class OTPVerifyForm(forms.Form):
    """Step 2: Enter the OTP code."""
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            "placeholder": "000000",
            "class": "input-field otp-input",
            "inputmode": "numeric",
            "autocomplete": "one-time-code",
            "autofocus": True,
        }),
        label="Verification Code",
    )


class RegistrationStep3Form(forms.Form):
    """Step 3: Set password + personal info."""
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Your full name", "class": "input-field"}),
        label="Full Name",
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. Tripoli", "class": "input-field"}),
        label="City",
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "placeholder": "Delivery address (optional, can add later)",
            "class": "input-field",
            "rows": 3,
        }),
        label="Delivery Address",
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password", "class": "input-field"}),
        label="Password",
        min_length=8,
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password", "class": "input-field"}),
        label="Confirm Password",
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class LoginForm(forms.Form):
    """Login with phone + password."""
    phone = forms.CharField(
        max_length=20,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            "placeholder": "+218 91 234 5678",
            "class": "input-field",
            "autofocus": True,
        }),
        label="Phone Number",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password", "class": "input-field"}),
        label="Password",
    )


class ProfileForm(forms.ModelForm):
    """Update profile info."""
    class Meta:
        model = User
        fields = ("full_name", "city", "address", "preferred_otp_channel")
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "input-field"}),
            "city": forms.TextInput(attrs={"class": "input-field"}),
            "address": forms.Textarea(attrs={"class": "input-field", "rows": 3}),
            "preferred_otp_channel": forms.RadioSelect(),
        }
