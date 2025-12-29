
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

        # Set access_token cookie
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,  # Prevent JavaScript access (security)
            secure=False,   # False for localhost, True for production HTTPS
            samesite='Lax', # 'Lax' for same-site, 'None' requires secure=True
            max_age=60 * 60,  # 1 hour (match your JWT lifetime)
            path='/',       # Available across entire domain
            domain=None,    # None for localhost, set to your domain in production
        )

        # Set refresh_token cookie
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=7 * 24 * 60 * 60,  # 7 days
            path='/',
            domain=None,
        )

        # Return success message (remove tokens from response body for security)
        response.data = {
            'message': 'Login successful',
           
        }
        
        return response

class Logout(GenericAPIView):
    def post(self,request):
        response = Response({
            'status': 'success',
            'message': 'User Logged out'
        })
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
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
                refresh = RefreshToken(refresh_token)
                
                # Create new access token
                response = Response({
                    'message': 'Token refreshed successfully'
                }, status=status.HTTP_200_OK)

                response.set_cookie(
                    key='access_token',
                    value=str(refresh.access_token),
                    httponly=True,
                    secure=settings.DEBUG is False,
                    samesite='Strict',
                    max_age=60 * 15,  # 15 minutes
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

