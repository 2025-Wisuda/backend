"""
Filter classes for lab schedule API endpoints.

This module provides filterset classes for lab schedule aggregator views,
enabling filtering by various fields like source model, date, activity type, and creator.
"""

import django_filters
from django.db import models

from ...models import LabScheduleModel


class LabScheduleFilter(django_filters.FilterSet):
    """Filter set for lab schedule aggregator listings."""

    type = django_filters.CharFilter(
        lookup_expr="icontains",
        help_text="Filter by activity type (e.g., search 'semi' will find 'Seminar')",
    )

    date = django_filters.DateFilter(
        help_text="Filter by specific scheduled date (YYYY-MM-DD)"
    )

    class Meta:
        model = LabScheduleModel
        fields = [
            "type",
            "date",
        ]
