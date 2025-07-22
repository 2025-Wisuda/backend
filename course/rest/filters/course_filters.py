"""Course API filtering with date range constraints."""

import django_filters

from ...models import CourseModel


class CourseFilter(django_filters.FilterSet):
    """Basic course filtering by date range."""

    start_date = django_filters.DateFilter(
        field_name="start_date",
        lookup_expr="gte",
        help_text="Filter courses starting from this date (YYYY-MM-DD)",
    )

    end_date = django_filters.DateFilter(
        field_name="end_date",
        lookup_expr="lte",
        help_text="Filter courses ending until this date (YYYY-MM-DD)",
    )

    class Meta:
        model = CourseModel
        fields = []
