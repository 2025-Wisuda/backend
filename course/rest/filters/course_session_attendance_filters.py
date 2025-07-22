"""Course Session Attendance Filters."""

import django_filters
from django.db.models import Q

from ...models import CourseSessionAttendanceModel


class CourseSessionAttendanceFilter(django_filters.FilterSet):
    """Filter for course session attendance records."""

    status = django_filters.CharFilter(field_name="status", lookup_expr="exact")
    manual_attendance_override = django_filters.BooleanFilter(
        field_name="manual_attendance_override", lookup_expr="exact"
    )

    class Meta:
        model = CourseSessionAttendanceModel
        fields = {
            "status": ["exact"],
            "manual_attendance_override": ["exact"],
        }
