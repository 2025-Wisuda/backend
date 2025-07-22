"""
ASGI config for Laboratory Management System.

It exposes the ASGI callable as a module-level variable named ``application``.
Supports both HTTP and WebSocket protocols for face recognition communication.
"""

import os

import django
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")

django.setup()

# Import the assembled application from routing.py
from .routing import application  # noqa: E402  pylint: disable=wrong-import-position

# Get Django ASGI application early to ensure apps are loaded
django_asgi_app = get_asgi_application()

from course.routing import websocket_urlpatterns as course_ws

# Import WebSocket routing and JWT middleware after Django setup
from duty_schedule.routing import websocket_urlpatterns as duty_ws
from face_recognition_ws.routing import websocket_urlpatterns as fr_ws
from face_recognition_ws.service_consumer import FaceRecognitionServiceConsumer
from guest_visit.routing import websocket_urlpatterns as guest_visit_ws
from shared.middleware.jwt_websocket_middleware import JWTAuthMiddleware

# Combine WS routes
websocket_routes = course_ws + duty_ws + fr_ws + guest_visit_ws

# Configure protocol router for HTTP and WebSocket with JWT authentication
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddleware(URLRouter(websocket_routes)),
        # Background consumer for face-recognition requests (no separate runworker needed)
        "channel": ChannelNameRouter(
            {
                "fr_requests": FaceRecognitionServiceConsumer.as_asgi(),
            }
        ),
    }
)
