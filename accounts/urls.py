from django.urls import path
from . import views

urlpatterns = [
    # path('google-login/', views.GoogleLogin.as_view(), name='google-login'),
    path('jwt/create/', views.CustomTokenObtainPairView.as_view()),
    path('jwt/refresh/', views.RefreshTokenView.as_view()),
    path('logout/', views.Logout.as_view()),
]