"""
Signal handlers for RoomBookingModel.
Handles synchronization with LabSchedule aggregator for booking approval status.

Soft deletes are handled by marking aggregator entries inactive.
"""

import logging

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from core import ApprovalStatus

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
                instance.booking_approval_status == ApprovalStatus.APPROVED.value
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
                    f"RoomBooking {instance.id} status {instance.booking_approval_status} or inactive - marking inactive in aggregator"
                )
                LabScheduleModel.remove_room_booking(instance.pk)

        except Exception as e:
            logger.exception(f"Error during room_booking_saved signal: {e}")

    transaction.on_commit(sync_if_approved)


@receiver(post_delete, sender=RoomBookingModel)
def room_booking_deleted(sender, instance, **kwargs):
    """
    Handle RoomBooking deletion event - soft remove from LabSchedule aggregator.

    Note:
        This only marks the aggregator entry as inactive, it does not physically delete it.
    """

    def remove_from_schedule():
        try:
            from lab_schedule.models import LabScheduleModel

            logger.info(
                f"RoomBooking deleted: {instance.id}, marking inactive in aggregator"
            )
            LabScheduleModel.remove_room_booking(instance.pk)
            logger.debug(
                f"RoomBooking deletion signal: {instance.id} deleted at {timezone.now()}"
            )

        except Exception as e:
            logger.exception(f"Error during room_booking_deleted signal: {e}")

    transaction.on_commit(remove_from_schedule)
