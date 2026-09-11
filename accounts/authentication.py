# accounts/authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Try to get token from cookie
        access_token = request.COOKIES.get('access_token')

        if not access_token:
            return None

        # Validate the token - return None (not 500) on expired/invalid
        try:
            validated_token = self.get_validated_token(access_token)
        except InvalidToken:
            return None
        try:
            return self.get_user(validated_token), validated_token
        except Exception:
            return None