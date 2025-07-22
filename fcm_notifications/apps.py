"""
FCM Notifications App Configuration
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FcmNotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fcm_notifications"
    verbose_name = _("FCM Notifications")

    def ready(self):
        """Import signals when app is ready"""
        import fcm_notifications.signals  # noqa
