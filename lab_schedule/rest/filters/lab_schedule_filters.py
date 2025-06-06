"""
Filter classes for lab schedule API endpoints.

This module provides filterset classes for lab schedule aggregator views,
enabling filtering by various fields like source model, date, activity type, and creator.
"""

import django_filters
from django.db import models

from ...models import LabScheduleModel


class LabScheduleFilter(django_filters.FilterSet):
    """
    Filter class for lab schedule aggregator listings.

    Simple and focused filtering for:
    - activity_type: Filter by activity type (flexible search)
    - activity_detail: Filter by activity detail/description
    - schedule_date: Filter by specific date
    """

    activity_type = django_filters.CharFilter(
        lookup_expr="icontains",
        help_text="Filter by activity type (e.g., search 'semi' will find 'Seminar')",
    )

    schedule_date = django_filters.DateFilter(
        help_text="Filter by specific scheduled date (YYYY-MM-DD)"
    )

    class Meta:
        model = LabScheduleModel
        fields = [
            "activity_type",
            "schedule_date",
        ]
