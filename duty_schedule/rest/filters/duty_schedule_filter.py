"""
Filter classes for duty schedule API endpoints.

This module provides filterset classes for duty schedule views,
enabling filtering by date ranges, assistant, and schedule type.
"""

import django_filters
from django.contrib.auth import get_user_model

from core.enums import DaysEnum

from ...models import DutyScheduleModel

User = get_user_model()


class DutyScheduleFilter(django_filters.FilterSet):
    """Filter set for duty schedule endpoints.
    Provides filtering capabilities for duty schedules based on duty days using Indonesian day names.
    """

    duty_days = django_filters.MultipleChoiceFilter(
        field_name="duty_days",
        choices=DaysEnum.choices(),
        help_text="Filter by duty days. Available options: Senin, Selasa, Rabu, Kamis, Jumat, Sabtu, Minggu and common patterns",
    )

    class Meta:
        model = DutyScheduleModel
        fields = ["duty_days"]
