"""
FCM Notifications URLs - Clean endpoints only
"""

from django.urls import include, path

# Import clean notification URLs
from .rest.urls.notification_urls import urlpatterns as notification_urls

# Import device management URLs
from .rest.urls.device_urls import urlpatterns as device_urls

app_name = "fcm_notifications"

urlpatterns = [
    # Clean notification endpoints (mobile needs)
    path("", include((notification_urls, "notifications"))),
    # Device management endpoints
    path("", include((device_urls, "devices"))),
]
