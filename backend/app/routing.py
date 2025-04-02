from django.urls import path
from app.consumers import StockPriceConsumer

websocket_urlpatterns = [
    path('ws/stocks/', StockPriceConsumer.as_asgi()),
]
