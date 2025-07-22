"""
FCM Notifications Signals

Handles automatic FCM device management.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from fcm_notifications.models import FCMDeviceModel


@receiver(post_save, sender=FCMDeviceModel)
def enforce_single_token_policy(sender, instance, created, **kwargs):
    """
    Enforce single token policy when a new device is registered.
    Only one device can be active per token.
    """
    if created and instance.is_active:
        # Deactivate other devices with same token
        FCMDeviceModel.objects.filter(
            registration_token=instance.registration_token, is_active=True
        ).exclude(id=instance.id).update(is_active=False)
