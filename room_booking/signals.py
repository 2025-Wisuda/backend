"""
Signal handlers for RoomBookingModel.
Handles synchronization with LabSchedule aggregator for booking approval status.

Soft deletes are handled by marking aggregator entries inactive.
"""

import logging

from core import ApprovalStatus
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import RoomBookingModel

logger = logging.getLogger("application.room_booking")


@receiver(post_save, sender=RoomBookingModel)
def room_booking_saved(sender, instance, created, **kwargs):
    """
    Handle RoomBooking save event - synchronize with LabSchedule aggregator.

    This signal will:
    1. Sync the RoomBooking to LabSchedule only if status is APPROVED and is_active is True.
    2. If status is not APPROVED or is_active is False, soft remove (set is_active=False) in aggregator.
    """

    def sync_if_approved():
        try:
            from lab_schedule.models import LabScheduleModel

            if (
                instance.approval_status == ApprovalStatus.APPROVED.value
                and instance.is_active
            ):
                action = "created" if created else "updated"
                logger.info(
                    f"RoomBooking {action}: {instance.id} ({instance.booking_type}) with APPROVED status"
                )
                LabScheduleModel.sync_from_room_booking(instance)
                logger.debug(
                    f"RoomBooking signal: {instance.id} {action} at {timezone.now()}"
                )
            else:
                logger.info(
                    f"RoomBooking {instance.id} status {instance.approval_status} or inactive - marking inactive in aggregator"
                )
                LabScheduleModel.remove_room_booking(instance.pk)

        except Exception as e:
            logger.exception(f"Error during room_booking_saved signal: {e}")

    transaction.on_commit(sync_if_approved)


@receiver(post_save, sender=RoomBookingModel)
def room_booking_notification_signal(sender, instance, created, **kwargs):
    """
    Handle RoomBooking notification events.

    This signal will:
    1. Send notification to technicians when new booking is created
    2. Send notification to booker when booking is approved/rejected
    """

    def send_notifications():
        try:
            from core.enums import NotificationTypeEnum
            from fcm_notifications.services.fcm_service_v2 import FCMService

            fcm_service = FCMService()

            if created:
                # New booking created - notify technicians
                logger.info(
                    f"RoomBooking created: {instance.id} - sending notification to technicians"
                )
                fcm_service.send_room_booking_notification(
                    booking=instance,
                    notification_type=NotificationTypeEnum.ROOM_BOOKING_CREATED.value,
                )

            # Check for approval status changes - more reliable than update_fields
            update_fields = kwargs.get("update_fields") or []
            approval_status_changed = "approval_status" in update_fields

            # If update_fields is not available, check if this is an update (not create)
            # and if approval status is APPROVED or REJECTED (indicating recent approval/rejection)
            if not created and not approval_status_changed:
                # Check if this looks like an approval/rejection based on status and timestamp
                if (
                    instance.approval_status
                    in [ApprovalStatus.APPROVED.value, ApprovalStatus.REJECTED.value]
                    and instance.approval_timestamp
                    and instance.approved_by_user
                ):
                    # This is likely an approval/rejection - send notification
                    approval_status_changed = True
                    logger.info(
                        f"Detected approval status change for booking {instance.id} (status: {instance.approval_status})"
                    )

            if approval_status_changed:
                # Approval status changed - notify booker
                if instance.approval_status == ApprovalStatus.APPROVED.value:
                    logger.info(
                        f"RoomBooking approved: {instance.id} - sending notification to booker"
                    )
                    logger.info(
                        f"[DEBUG] Calling send_room_booking_notification for APPROVED booking {instance.id}"
                    )
                    result = fcm_service.send_room_booking_notification(
                        booking=instance,
                        notification_type=NotificationTypeEnum.ROOM_BOOKING_APPROVED.value,
                    )
                    logger.info(
                        f"[DEBUG] send_room_booking_notification result (APPROVED): {result}"
                    )

                elif instance.approval_status == ApprovalStatus.REJECTED.value:
                    logger.info(
                        f"RoomBooking rejected: {instance.id} - sending notification to booker"
                    )
                    logger.info(
                        f"[DEBUG] Calling send_room_booking_notification for REJECTED booking {instance.id}"
                    )
                    result = fcm_service.send_room_booking_notification(
                        booking=instance,
                        notification_type=NotificationTypeEnum.ROOM_BOOKING_REJECTED.value,
                    )
                    logger.info(
                        f"[DEBUG] send_room_booking_notification result (REJECTED): {result}"
                    )

        except Exception as e:
            logger.exception(f"Error during room_booking_notification_signal: {e}")

    transaction.on_commit(send_notifications)


@receiver(post_delete, sender=RoomBookingModel)
def room_booking_deleted(sender, instance, **kwargs):
    """
    Handle RoomBooking delete event - remove from LabSchedule aggregator.
    """

    def remove_from_aggregator():
        try:
            from lab_schedule.models import LabScheduleModel

            logger.info(
                f"RoomBooking deleted: {instance.id} - removing from aggregator"
            )
            LabScheduleModel.remove_room_booking(instance.pk)

        except Exception as e:
            logger.exception(f"Error during room_booking_deleted signal: {e}")

    transaction.on_commit(remove_from_aggregator)
