from django.urls import path, include
from .views import (
    home,
    FyersAuthView,
    FyersCallbackView,
    StockPriceAPIView
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

     path('fyers/auth/', FyersAuthView.as_view(), name='fyers_auth'),
    path('callback/', FyersCallbackView.as_view(), name='fyers_callback'),
    
    # API routes (for users)
    path('api/stocks/', StockPriceAPIView.as_view(), name='stock_prices'),
    path('api/stocks/<str:symbol>/', StockPriceAPIView.as_view(), name='stock_price_detail'),
]