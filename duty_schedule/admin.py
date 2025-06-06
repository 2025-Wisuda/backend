"""Expose selected admin components for external use."""

from .admins.duty_schedule_admin import DutyScheduleAdmin

__all__ = [
    "DutyScheduleAdmin",
]
