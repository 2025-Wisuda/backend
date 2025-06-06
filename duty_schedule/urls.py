"""
URL configuration for duty_schedule app.

Includes both REST API endpoints and WebSocket routing.
"""

from django.urls import include, path

app_name = "duty_schedule"

urlpatterns = [
    path("", include("duty_schedule.rest.urls")),
]
