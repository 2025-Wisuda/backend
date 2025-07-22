from django.urls import path

from .consumers import FaceRecognitionConsumer

websocket_urlpatterns = [
    path("ws/face-recognition/", FaceRecognitionConsumer.as_asgi()),
] 