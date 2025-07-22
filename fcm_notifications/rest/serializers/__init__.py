"""
FCM Notifications Serializers - Clean serializers only
"""

from .fcm_device_serializer import (
    FCMDeviceSerializer,
    RegisterDeviceResponseSerializer,
    SendTestNotificationResponseSerializer,
)
from .notification_log_serializer import (
    NotificationLogListSerializer,
    NotificationMarkAllAsReadResponseSerializer,
    NotificationMarkAsReadResponseSerializer,
    NotificationUnreadCountResponseSerializer,
)

__all__ = [
    "NotificationLogListSerializer",
    "FCMDeviceSerializer",
    "NotificationMarkAsReadResponseSerializer",
    "NotificationMarkAllAsReadResponseSerializer",
    "NotificationUnreadCountResponseSerializer",
    "RegisterDeviceResponseSerializer",
    "SendTestNotificationResponseSerializer",
]
