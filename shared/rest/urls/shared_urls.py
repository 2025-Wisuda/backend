"""
Shared REST API URLs.

Common URLs that are shared across multiple apps.
"""

from django.urls import path

from ..views.shared_views import get_current_otp

# COMMENTED OUT IMPORTS TO PREVENT FRAUD - NO MANUAL OTP GENERATION/RESET
# from ..views.shared_views import generate_new_otp, get_otp_status

urlpatterns = [
    # OTP Management endpoints - Only auto-display, no manual controls
    path("otp/current/", get_current_otp, name="get_current_otp"),
    # COMMENTED OUT TO PREVENT FRAUD - NO MANUAL OTP GENERATION/RESET
    # path("otp/generate/", generate_new_otp, name="generate_new_otp"),
    # path("otp/status/", get_otp_status, name="get_otp_status"),
] 