# accounts/authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Try to get token from cookie
        access_token = request.COOKIES.get('access_token')
        
        if access_token is None:
            return None
        
        # Validate the token
        validated_token = self.get_validated_token(access_token)
        return self.get_user(validated_token), validated_token