"""Admin interface exports for lab schedule management."""

from .admins.lab_schedule_admin import LabScheduleAdmin
from .admins.lab_schedule_dashboard_admin import LabScheduleDashboardAdmin

__all__ = [
    "LabScheduleAdmin",
    "LabScheduleDashboardAdmin",
]
