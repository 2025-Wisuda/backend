"""
FCM Notifications Views - Only ViewSets
"""

from .device_views import DeviceViewSet
from .notification_views import NotificationLogViewSet

__all__ = [
    "NotificationLogViewSet",
    "DeviceViewSet",
]
