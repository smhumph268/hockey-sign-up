from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q


class CustomAuthenticationBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        MyUserModel = get_user_model()

        # Check if the given credentials match the username or email field
        try:
            user = MyUserModel.objects.get(
                Q(username__iexact=username) |
                Q(email__iexact=username)
            )
        except MyUserModel.DoesNotExist:
            return None

        # Check the password
        if user.check_password(password):
            return user

    def get_user(self, user_id):
        MyUserModel = get_user_model()

        try:
            return MyUserModel.objects.get(pk=user_id)
        except MyUserModel.DoesNotExist:
            return None
