from django.urls import include, path
from .device_urls import urlpatterns as device_urls
from .notification_urls import urlpatterns as notification_urls

app_name = "fcm_notifications"

urlpatterns = [
    path("", include((notification_urls, "notifications"))),
    path("", include((device_urls, "devices"))),
]
