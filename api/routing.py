"""
Main WebSocket routing configuration for Django Channels.

Includes all app-specific WebSocket routes with JWT authentication.
"""

from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter

# websocket patterns from features
from course.routing import websocket_urlpatterns as course_ws
from django.core.asgi import get_asgi_application
from duty_schedule.routing import websocket_urlpatterns as duty_ws
from face_recognition_ws.routing import websocket_urlpatterns as fr_ws
from face_recognition_ws.service_consumer import FaceRecognitionServiceConsumer
from guest_visit.routing import websocket_urlpatterns as guest_visit_ws
from shared.middleware.jwt_websocket_middleware import JWTAuthMiddleware

# Merge WS urls
websocket_urlpatterns = course_ws + duty_ws + fr_ws + guest_visit_ws

# Final root application
application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
        "channel": ChannelNameRouter(
            {
                "fr_requests": FaceRecognitionServiceConsumer.as_asgi(),
            }
        ),
    }
)
