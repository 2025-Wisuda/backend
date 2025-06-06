"""Expose selected admin components for external use."""

from .admins.admin_config import LabScheduleManagementAdminConfig
from .admins.lab_schedule_admin import LabScheduleAdmin
from .admins.lab_schedule_dashboard_admin import LabScheduleDashboardAdmin  # noqa

LabScheduleManagementAdminConfig.configure_admin()

__all__ = [
    "LabScheduleAdmin",
    "LabScheduleDashboardAdmin",
]
