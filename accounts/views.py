
from rest_framework_simplejwt.views import TokenObtainPairView


# class GoogleLogin(SocialLoginView):
#     adapter_class = GoogleOAuth2Adapter
#     callback_url = "http://localhost:3000" 
#     client_class = OAuth2Client

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        access_token = response.data.get('access')
        refresh_token = response.data.get('refresh')

        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=False,
            # samesite='None',
            max_age=10 * 60,
        )

        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=False,
            # samesite='None',
            max_age=7 * 24 * 60 * 60,
        )

        response.data = {'message': 'Login successful'}
        print(f"Response type: {type(response)}")
        print(f"Response cookies: {response.cookies}")
        print(f"Cookie keys: {list(response.cookies.keys())}")
        return response
