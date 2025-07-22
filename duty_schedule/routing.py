"""
WebSocket URL routing for duty_schedule app.
"""

import json

from django.urls import path

from .consumers import DutyAttendanceConsumer


websocket_urlpatterns = [
    path("ws/duty-attendance/", DutyAttendanceConsumer.as_asgi()),
] 