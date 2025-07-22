"""
FCM Device Model

Stores FCM registration tokens for user devices.
"""

from core import BaseModel
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class FCMDeviceModel(BaseModel):
    """
    Model to store FCM device registration tokens.

    Each user can have multiple devices (phone, tablet, etc.)
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fcm_devices",
        verbose_name=_("User"),
        help_text=_("User who owns this device"),
    )

    registration_token = models.CharField(
        max_length=255,
        unique=False,
        verbose_name=_("Registration Token"),
        help_text=_("FCM registration token for this device"),
    )

    device_type = models.CharField(
        max_length=20,
        choices=[
            ("android", _("Android")),
            ("ios", _("iOS")),
            ("web", _("Web")),
        ],
        default="android",
        verbose_name=_("Device Type"),
        help_text=_("Type of device (Android, iOS, Web)"),
    )

    device_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Device Name"),
        help_text=_("Optional device name (e.g., 'iPhone 13', 'Samsung Galaxy')"),
    )

    last_used = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last Used"),
        help_text=_("When this token was last updated"),
    )

    class Meta:
        db_table = "fcm_devices"
        ordering = ["-last_used"]
        verbose_name = _("FCM Device")
        verbose_name_plural = _("FCM Devices")

        constraints = [
            models.UniqueConstraint(
                fields=["user", "registration_token"], name="unique_user_token"
            ),
        ]

        indexes = [
            models.Index(fields=["user", "is_active"]),
            # Index on registration_token removed due to MySQL TEXT field limitations
        ]

    def __str__(self):
        device_info = self.device_name or f"{self.device_type.title()} Device"
        return f"{self.user.username} - {device_info}"

    @classmethod
    def register_device(cls, user, token, device_type="android", device_name=None):
        """
        Register or update FCM device token for a user.

        Policy: 1 token = 1 active device
        When new token is registered, old token is deactivated.

        Args:
            user: User instance
            token: FCM registration token
            device_type: Type of device ('android', 'ios', 'web')
            device_name: Optional device name

        Returns:
            FCMDeviceModel instance
        """
        # Deactivate any existing device with this token
        cls.objects.filter(registration_token=token).update(is_active=False)

        # Create or update the device for this user
        device, created = cls.objects.update_or_create(
            user=user,
            registration_token=token,
            defaults={
                "device_type": device_type,
                "device_name": device_name,
                "is_active": True,
            },
        )
        device.is_active = True
        device.save(update_fields=["is_active"])
        return device

    @classmethod
    def get_user_active_devices(cls, user):
        """
        Get all active devices for a user.

        Args:
            user: User instance

        Returns:
            QuerySet of active FCMDeviceModel instances
        """
        return cls.objects.filter(user=user, is_active=True)

    @classmethod
    def get_active_tokens_for_user(cls, user):
        """
        Get list of active FCM tokens for a user.

        Args:
            user: User instance

        Returns:
            List of registration tokens
        """
        return list(
            cls.get_user_active_devices(user).values_list(
                "registration_token", flat=True
            )
        )

    def deactivate(self):
        """Deactivate this device (soft delete)"""
        self.is_active = False
        self.save(update_fields=["is_active"])

    def activate(self):
        """Activate this device"""
        self.is_active = True
        self.save(update_fields=["is_active"])
