from django.urls import path
from . import views

urlpatterns = [
    path('google-login/', views.GoogleLogin.as_view(), name='google-login'),
]