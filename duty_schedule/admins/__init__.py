"""
Duty Schedule Admin Module

Provides administrative interfaces for managing duty schedules and attendance records.

Features:
- Duty schedule management with bulk generation capabilities
- Duty attendance tracking and monitoring
- Dashboard for visualizing attendance analytics and statistics
- Role-based access control for different user groups

Key Components:
- DutyScheduleAdmin: Admin interface for duty schedule management
- DutyAttendanceAdmin: Admin interface for attendance records
- DutyAttendanceDashboardAdmin: Dashboard for attendance analytics
"""

from .duty_attendance_admin import DutyAttendanceAdmin
from .duty_attendance_dashboard_admin import DutyAttendanceDashboardAdmin
from .duty_schedule_admin import DutyScheduleAdmin

__all__ = [
    "DutyScheduleAdmin",
    "DutyAttendanceAdmin",
    "DutyAttendanceDashboardAdmin",
]
