"""
URL configuration for duty_schedule app.

Includes both REST API endpoints and WebSocket routing.
"""

from django.urls import include, path
from django.views.generic import TemplateView

app_name = "duty_schedule"

urlpatterns = [
    # OTP UI for testing
    path("otp/", TemplateView.as_view(template_name="duty_schedule_otp.html"), name="duty_otp_ui"),
    
    # REST API endpoints
    path("", include("duty_schedule.rest.urls")),
]
