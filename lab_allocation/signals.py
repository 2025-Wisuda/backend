import logging

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import LabAllocationModel

logger = logging.getLogger("infrastructure.lab_allocation")


@receiver(post_save, sender=LabAllocationModel)
def lab_allocation_saved(sender, instance, created, **kwargs):
    """
    Handle LabAllocation save event - synchronize with LabSchedule aggregator.

    This signal will:
    1. Create or update the corresponding LabSchedule entry for conflict detection.
    2. Skip synchronization if the allocation is a bulk allocation (handled separately).
    3. Trigger conflict detection across all booking types.
    """

    def sync_to_schedule():
        try:
            from lab_schedule.models import LabScheduleModel

            action = "created" if created else "updated"

            if hasattr(instance, "end_date") and hasattr(instance, "days"):
                if instance.end_date and instance.days:
                    logger.debug(
                        f"Bulk allocation {action}: {instance.type} - skipping sync"
                    )
                    return

            logger.info(f"Single allocation {action}: {instance.type}")
            LabScheduleModel.sync_from_allocation(instance)
            logger.debug(
                f"LabAllocation signal: {instance.id} {action} at {timezone.localtime()}"
            )

        except Exception as e:
            logger.exception(f"Error during lab_allocation_saved signal: {e}")

    transaction.on_commit(sync_to_schedule)


@receiver(post_delete, sender=LabAllocationModel)
def lab_allocation_deleted(sender, instance, **kwargs):
    """
    Handle LabAllocation deletion event - synchronize removal from LabSchedule aggregator.

    Note: For soft delete, this signal might not be triggered.
    Removal should be handled explicitly by updating 'is_active' in sync_from_allocation.
    """

    def remove_from_schedule():
        try:
            from lab_schedule.models import LabScheduleModel

            logger.info(f"Allocation deleted: {instance.type}")
            LabScheduleModel.remove_allocation(instance.pk)
            logger.debug(
                f"LabAllocation deletion signal: {instance.id} deleted at {timezone.localtime()}"
            )

        except Exception as e:
            logger.exception(f"Error during lab_allocation_deleted signal: {e}")

    transaction.on_commit(remove_from_schedule)


def sync_bulk_allocation_to_schedule(allocation_instance, action):
    """
    Synchronize bulk allocation with LabSchedule aggregator.

    Args:
        allocation_instance: LabAllocationModel instance.
        action: 'created' or 'updated'.

    Note:
        This function is called for each individual schedule generated from bulk allocation.
    """
    try:
        from lab_schedule.models import LabScheduleModel

        logger.info(f"Bulk allocation sync {action}: {allocation_instance.type}")
        LabScheduleModel.sync_from_allocation(allocation_instance)
        logger.debug(
            f"Bulk allocation synced: {allocation_instance.id} {action} at {timezone.localtime()}"
        )

    except Exception as e:
        logger.exception(f"Error during bulk allocation sync: {e}")
        raise  # Re-raise for proper error handling
