from django.urls import path
from .consumers import ShopConsumer

websocket_urlpatterns = [
    path('ws/shop/', ShopConsumer.as_asgi()),
]