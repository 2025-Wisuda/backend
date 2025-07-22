"""
Lab Schedule Admin Module

Provides administrative interfaces for managing and viewing aggregated lab schedules.

Features:
- Read-only view of aggregated lab schedules from various sources.
- Export functionality for schedule data, restricted to authorized personnel.
- Dashboard for visualizing lab schedule analytics and statistics.
- Centralized resource definitions for consistent data handling in exports.

Key Components:
- LabScheduleAdmin: Admin interface for the LabScheduleModel, providing a read-only view and export capabilities.
- LabScheduleDashboardAdmin: Admin interface for the LabScheduleDashboardModel, rendering a dashboard with schedule analytics.
- LabScheduleResource: ImportExport resource for LabScheduleModel, focused on export-only functionality.
- LabScheduleExportView: Custom view to handle advanced filtering and field selection for exports.

Architecture:
- Primarily read-only: Data is aggregated from other modules (LabAllocation, CourseSession, RoomBooking).
- Export-focused: Provides tools to extract schedule data with filtering.
- Dashboard integration: Offers a visual overview of scheduling data directly in the admin panel.
- EXPORT_FIELDS defined in LabScheduleResource serve as the single source of truth for exportable fields.
"""

from .lab_schedule_admin import LabScheduleAdmin
from .lab_schedule_dashboard_admin import LabScheduleDashboardAdmin
from .lab_schedule_resource import LabScheduleResource

__all__ = [
    "LabScheduleAdmin",
    "LabScheduleDashboardAdmin",
    "LabScheduleResource",
]
