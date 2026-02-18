from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class PhoneBackend(ModelBackend):
    """
    Authenticate using phone number + password.
    """

    def authenticate(self, request, phone=None, password=None, **kwargs):
        # Also support 'username' kwarg for compatibility with some Django internals
        if phone is None:
            phone = kwargs.get("username")
        if phone is None or password is None:
            return None
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
