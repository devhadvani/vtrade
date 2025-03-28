from django.urls import path, include
from .views import (
    home
)
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.views import UserDetailsView

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter


urlpatterns = [
    path("", home),
    path("auth/user/", UserDetailsView.as_view(), name="user-details"),
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),
]