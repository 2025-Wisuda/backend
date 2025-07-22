"""
Filters for duty attendance API endpoints.

Provides filtering capabilities for duty attendance queries with mobile-optimized
filters for common use cases like date ranges, status filtering, and user-specific queries.
"""

from datetime import date, timedelta

import django_filters
from django.db import models
from django.utils import timezone

from core.enums.attendance_status_enum import AttendanceStatus
from core.enums.days_enum import DaysEnum

from ...models.duty_attendance_model import DutyAttendanceModel


class DutyAttendanceFilter(django_filters.FilterSet):
    """
    Filter set for duty attendance endpoints.

    Provides mobile-friendly filtering options for attendance queries
    with optimized field selection for common mobile app use cases.
    """

    status = django_filters.MultipleChoiceFilter(
        field_name="status",
        choices=AttendanceStatus.choices(),
        help_text="Filter by attendance status",
    )
    date = django_filters.DateFilter(
        field_name="date",
        lookup_expr="exact",
        help_text="Filter by specific duty date (YYYY-MM-DD format)",
    )

    class Meta:
        model = DutyAttendanceModel
        fields = [
            "status",
            "date",
        ]
