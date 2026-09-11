
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken, TokenError
from rest_framework import status
from django.conf import settings
from rest_framework.permissions import AllowAny

import logging

# Set up logger
logger = logging.getLogger(__name__)

# class GoogleLogin(SocialLoginView):
#     adapter_class = GoogleOAuth2Adapter
#     callback_url = "http://localhost:3000" 
#     client_class = OAuth2Client

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # Extract tokens from response
        access_token = response.data.get('access')
        refresh_token = response.data.get('refresh')

        # Set access_token cookie (60min to match SIMPLE_JWT ACCESS_TOKEN_LIFETIME)
        is_secure = settings.DEBUG is False
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,  # Prevent JavaScript access (security)
            secure=is_secure,
            samesite='Lax',
            max_age=60 * 60,  # 1 hour (match your JWT lifetime)
            path='/',       # Available across entire domain
        )

        # Set refresh_token cookie
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=is_secure,
            samesite='Lax',
            max_age=7 * 24 * 60 * 60,  # 7 days
            path='/',
        )

        # Return success message (remove tokens from response body for security)
        response.data = {
            'message': 'Login successful',
           
        }
        
        return response

class Logout(GenericAPIView):
    def post(self,request):
        # Blacklist refresh token if present so it can't be reused
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass
        response = Response({
            'status': 'success',
            'message': 'User Logged out'
        })
        is_secure = settings.DEBUG is False
        response.delete_cookie("access_token", path='/', samesite='Lax')
        response.delete_cookie("refresh_token", path='/', samesite='Lax')
        # Ensure secure flag matches on production so browsers actually clear
        if is_secure:
            response.delete_cookie("access_token", path='/', samesite='Lax', secure=True)
            response.delete_cookie("refresh_token", path='/', samesite='Lax', secure=True)
        return response


class RefreshTokenView(GenericAPIView):
    """View to refresh access token using refresh token from cookie"""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')

            if not refresh_token:
                return Response({
                    'error': 'Refresh token not found',
                    'message': 'Please login again'
                }, status=status.HTTP_401_UNAUTHORIZED)

            try:
                old_refresh = RefreshToken(refresh_token)

                # Rotate refresh token to match ROTATE_REFRESH_TOKENS=True:
                # derive a new access token, issue a fresh refresh token,
                # then blacklist the old refresh.
                access_token = str(old_refresh.access_token)
                try:
                    # Issue a new refresh token for the same user
                    from django.contrib.auth import get_user_model
                    user = get_user_model().objects.get(id=old_refresh['user_id'])
                    new_refresh_token = str(RefreshToken.for_user(user))
                    old_refresh.blacklist()
                except Exception:
                    # If blacklisting/rotation fails, still allow access refresh
                    # (old refresh remains valid until expiry)
                    new_refresh_token = None

                # Create new access token
                response = Response({
                    'message': 'Token refreshed successfully'
                }, status=status.HTTP_200_OK)

                is_secure = settings.DEBUG is False
                response.set_cookie(
                    key='access_token',
                    value=access_token,
                    httponly=True,
                    secure=is_secure,
                    samesite='Lax',
                    max_age=60 * 60,  # 60 minutes to match ACCESS_TOKEN_LIFETIME
                    path='/'
                )
                if new_refresh_token:
                    response.set_cookie(
                        key='refresh_token',
                        value=new_refresh_token,
                        httponly=True,
                        secure=is_secure,
                        samesite='Lax',
                        max_age=7 * 24 * 60 * 60,  # 7 days to match REFRESH_TOKEN_LIFETIME
                        path='/'
                    )

                return response

            except TokenError as e:
                logger.warning(f"Invalid refresh token: {str(e)}")
                return Response({
                    'error': 'Invalid or expired refresh token',
                    'message': 'Please login again'
                }, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return Response({
                'error': 'An error occurred while refreshing token',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

