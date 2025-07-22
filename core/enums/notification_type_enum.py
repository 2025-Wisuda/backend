"""
Notification Type Enum

Defines all possible notification types in the lab management system.
Each type has specific triggers and message formats.
"""

from enum import Enum


class NotificationTypeEnum(Enum):
    """
    Enum for all notification types in the lab management system.

    Room Booking Notifications:
    - ROOM_BOOKING_CREATED: New room booking created (notify technicians)
    - ROOM_BOOKING_APPROVED: Booking approved (notify booker)
    - ROOM_BOOKING_REJECTED: Booking rejected (notify booker)

    Lab Schedule Notifications (covers all activities):
    - LAB_SCHEDULE_START: 15 minutes before any lab activity starts
    - LAB_SCHEDULE_END: 15 minutes before any lab activity ends

    Duty Schedule Notifications:
    - DUTY_SCHEDULE_START: 15 minutes before duty starts
    - DUTY_SCHEDULE_END: 15 minutes before duty ends
    """

    # Room Booking Notifications
    ROOM_BOOKING_CREATED = "room_booking_created"
    ROOM_BOOKING_APPROVED = "room_booking_approved"
    ROOM_BOOKING_REJECTED = "room_booking_rejected"

    # Lab Schedule Notifications
    LAB_SCHEDULE_START = "lab_schedule_start"
    LAB_SCHEDULE_END = "lab_schedule_end"

    # Duty Schedule Notifications
    DUTY_SCHEDULE_START = "duty_schedule_start"
    DUTY_SCHEDULE_END = "duty_schedule_end"

    @classmethod
    def choices(cls):
        """Return choices for Django model fields."""
        return [(member.value, member.name) for member in cls]

    @classmethod
    def values(cls):
        """Return list of values."""
        return [member.value for member in cls]

    @classmethod
    def names(cls):
        """Return list of names."""
        return [member.name for member in cls]

    @classmethod
    def get_room_booking_types(cls):
        """Get room booking notification types."""
        return [
            cls.ROOM_BOOKING_CREATED.value,
            cls.ROOM_BOOKING_APPROVED.value,
            cls.ROOM_BOOKING_REJECTED.value,
        ]

    @classmethod
    def get_schedule_types(cls):
        """Get schedule notification types."""
        return [
            cls.LAB_SCHEDULE_START.value,
            cls.LAB_SCHEDULE_END.value,
            cls.DUTY_SCHEDULE_START.value,
            cls.DUTY_SCHEDULE_END.value,
        ]

    @classmethod
    def get_start_notification_types(cls):
        """Get start notification types."""
        return [
            cls.LAB_SCHEDULE_START.value,
            cls.DUTY_SCHEDULE_START.value,
        ]

    @classmethod
    def get_end_notification_types(cls):
        """Get end notification types."""
        return [
            cls.LAB_SCHEDULE_END.value,
            cls.DUTY_SCHEDULE_END.value,
        ]
