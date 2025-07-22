"""API schemas for lab schedule aggregator endpoints."""

from .lab_schedule_schema import (
    lab_schedule_availability_schema,
    lab_schedule_detail_schema,
    lab_schedule_list_schema,
    lab_schedule_my_schedules_schema,
)

__all__ = [
    "lab_schedule_detail_schema",
    "lab_schedule_list_schema",
    "lab_schedule_availability_schema",
    "lab_schedule_my_schedules_schema",
]
