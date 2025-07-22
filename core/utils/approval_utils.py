"""
Utilities for handling approval status transitions and business logic.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from core.enums import ApprovalStatus


class ApprovalStatusManager:
    """
    Manager class for handling approval status transitions and validations.
    """

    # Define valid status transitions
    VALID_TRANSITIONS: Dict[ApprovalStatus, List[ApprovalStatus]] = {
        ApprovalStatus.PENDING: [
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.CANCELLED,
        ],
        ApprovalStatus.APPROVED: [
            ApprovalStatus.IN_PROGRESS,
            ApprovalStatus.COMPLETED,
            ApprovalStatus.CANCELLED,
            ApprovalStatus.EXPIRED,
        ],
        ApprovalStatus.IN_PROGRESS: [
            ApprovalStatus.COMPLETED,
            ApprovalStatus.CANCELLED,
        ],
        # Final states - no transitions allowed
        ApprovalStatus.REJECTED: [],
        ApprovalStatus.CANCELLED: [],
        ApprovalStatus.COMPLETED: [],
        ApprovalStatus.EXPIRED: [],
    }

    @classmethod
    def can_transition_to(
        cls, current_status: ApprovalStatus, new_status: ApprovalStatus
    ) -> bool:
        """
        Check if a status transition is valid.

        Args:
            current_status: Current approval status
            new_status: Desired new status

        Returns:
            bool: True if transition is allowed
        """
        allowed_transitions = cls.VALID_TRANSITIONS.get(current_status, [])
        return new_status in allowed_transitions

    @classmethod
    def get_available_transitions(
        cls, current_status: ApprovalStatus
    ) -> List[ApprovalStatus]:
        """
        Get list of possible status transitions from current status.

        Args:
            current_status: Current approval status

        Returns:
            List of available status transitions
        """
        return cls.VALID_TRANSITIONS.get(current_status, [])

    @classmethod
    def is_expired(
        cls, scheduled_datetime: datetime, current_datetime: Optional[datetime] = None
    ) -> bool:
        """
        Check if a scheduled item should be marked as expired.

        Args:
            scheduled_datetime: The scheduled date and time
            current_datetime: Current datetime (defaults to now)

        Returns:
            bool: True if the item is expired
        """
        if current_datetime is None:
            current_datetime = datetime.now(timezone.utc)

        # Make sure both datetimes are timezone-aware
        if scheduled_datetime.tzinfo is None:
            scheduled_datetime = scheduled_datetime.replace(tzinfo=timezone.utc)
        if current_datetime.tzinfo is None:
            current_datetime = current_datetime.replace(tzinfo=timezone.utc)

        return current_datetime > scheduled_datetime

    @classmethod
    def should_auto_expire(
        cls, current_status: ApprovalStatus, scheduled_datetime: datetime
    ) -> bool:
        """
        Determine if an item should be automatically expired.

        Args:
            current_status: Current approval status
            scheduled_datetime: The scheduled date and time

        Returns:
            bool: True if should be auto-expired
        """
        # Only approved items that haven't started can be expired
        if current_status != ApprovalStatus.APPROVED:
            return False

        return cls.is_expired(scheduled_datetime)

    @classmethod
    def get_status_color(cls, status: ApprovalStatus) -> str:
        """
        Get CSS color class for status display.

        Args:
            status: Approval status

        Returns:
            str: CSS color class
        """
        color_mapping = {
            ApprovalStatus.PENDING: "warning",
            ApprovalStatus.APPROVED: "success",
            ApprovalStatus.REJECTED: "danger",
            ApprovalStatus.CANCELLED: "secondary",
            ApprovalStatus.COMPLETED: "primary",
            ApprovalStatus.EXPIRED: "dark",
            ApprovalStatus.IN_PROGRESS: "info",
        }
        return color_mapping.get(status, "secondary")

    @classmethod
    def get_status_icon(cls, status: ApprovalStatus) -> str:
        """
        Get icon class for status display.

        Args:
            status: Approval status

        Returns:
            str: Icon class name
        """
        icon_mapping = {
            ApprovalStatus.PENDING: "clock",
            ApprovalStatus.APPROVED: "check-circle",
            ApprovalStatus.REJECTED: "x-circle",
            ApprovalStatus.CANCELLED: "slash-circle",
            ApprovalStatus.COMPLETED: "check-square",
            ApprovalStatus.EXPIRED: "exclamation-triangle",
            ApprovalStatus.IN_PROGRESS: "play-circle",
        }
        return icon_mapping.get(status, "circle")


def auto_update_expired_schedules(
    schedules_queryset, datetime_field: str = "scheduled_date"
):
    """
    Automatically update expired schedules in a queryset.

    Args:
        schedules_queryset: Django queryset of schedule objects
        datetime_field: Name of the datetime field to check for expiration

    Returns:
        int: Number of schedules updated
    """
    from django.utils import timezone

    current_time = timezone.localtime()
    manager = ApprovalStatusManager()

    updated_count = 0

    for schedule in schedules_queryset.filter(
        schedule_approval_status=ApprovalStatus.APPROVED
    ):
        scheduled_datetime = getattr(schedule, datetime_field, None)

        if scheduled_datetime and manager.should_auto_expire(
            schedule.schedule_approval_status, scheduled_datetime
        ):
            schedule.schedule_approval_status = ApprovalStatus.EXPIRED
            schedule.save(update_fields=["schedule_approval_status"])
            updated_count += 1

    return updated_count
