from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from .models import Profile

class UsernameOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None

        try:
            # 1. Try to find the user by their standard Username
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 2. If username fails, try searching the Profile's phone_number
            try:
                profile = Profile.objects.get(phone_number=username)
                user = profile.user
            except (Profile.DoesNotExist, User.DoesNotExist):
                return None

        # 3. Check if the password is correct for the user we found
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None