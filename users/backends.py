from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class EmailVerifiedBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user if user.is_email_verified else None
        except User.DoesNotExist:
            return None