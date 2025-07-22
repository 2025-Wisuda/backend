"""
Lab Schedule Models Module.

Models for centralized laboratory scheduling and conflict detection.

Components:
    LabScheduleModel: Core aggregator model for all lab time slots
    LabScheduleDashboardModel: Analytics and dashboard statistics model
"""

from .lab_schedule_dashboard_model import LabScheduleDashboardModel
from .lab_schedule_model import LabScheduleModel

__all__ = ["LabScheduleModel", "LabScheduleDashboardModel"]
