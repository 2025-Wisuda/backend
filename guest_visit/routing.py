"""
WebSocket routing for guest visit face recognition.
"""

from django.urls import path

from .consumers import GuestVisitConsumer

websocket_urlpatterns = [
    path("ws/guest-visit/", GuestVisitConsumer.as_asgi()),
]
