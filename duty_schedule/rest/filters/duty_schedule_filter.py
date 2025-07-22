"""
Filter classes for duty schedule API endpoints.

This module provides filterset classes for duty schedule views,
enabling filtering by date ranges, assistant, and schedule type.
"""

import django_filters
from core.enums import DaysEnum
from django.contrib.auth import get_user_model
from django.db import models

from ...models import DutyScheduleModel

User = get_user_model()


class DutyScheduleFilter(django_filters.FilterSet):
    """Filter set for duty schedule endpoints.
    Provides filtering capabilities for duty schedules based on duty days using weekday index (ISO 8601).
    """

    days = django_filters.NumberFilter(
        method='filter_by_weekday',
        help_text="Filter by weekday index (0=Monday, 1=Tuesday, ..., 6=Sunday) according to ISO 8601",
    )

    def filter_by_weekday(self, queryset, name, value):
        """
        Filter by weekday index (0=Monday, 6=Sunday) according to ISO 8601.
        
        Args:
            queryset: The queryset to filter
            name: Field name (not used)
            value: Weekday index (0-6)
            
        Returns:
            Filtered queryset
        """
        if value is None or value < 0 or value > 6:
            return queryset
            
        # Map weekday index to Indonesian day names
        weekday_to_day = {
            0: "Senin",    # Monday
            1: "Selasa",   # Tuesday  
            2: "Rabu",     # Wednesday
            3: "Kamis",    # Thursday
            4: "Jumat",    # Friday
            5: "Sabtu",    # Saturday
            6: "Minggu",   # Sunday
        }
        
        target_day = weekday_to_day.get(value)
        if target_day:
            return queryset.filter(days__icontains=target_day)
        
        return queryset

    class Meta:
        model = DutyScheduleModel
        fields = ["days"]
