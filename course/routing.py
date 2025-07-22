"""
WebSocket routing for Course module.
"""

from django.urls import path

from .consumers import CourseSessionAttendanceConsumer

websocket_urlpatterns = [
    path("ws/course-session-attendance/", CourseSessionAttendanceConsumer.as_asgi()),
] 