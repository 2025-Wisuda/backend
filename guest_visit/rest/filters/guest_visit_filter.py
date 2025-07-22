"""
Filters for Guest Visit API endpoints.

Provides filtering capabilities for guest visit list views
with search and date-based filtering.
"""

import django_filters
from django.db import models

from ...models import GuestVisitModel


class GuestVisitFilter(django_filters.FilterSet):
    """
    Filter set for guest visit list view.
    
    Provides filtering by date and search capabilities.
    """
    
    date = django_filters.DateFilter(
        field_name="date",
        help_text="Filter by specific visit date (YYYY-MM-DD format)"
    )
    
    class Meta:
        model = GuestVisitModel
        fields = [
            "date",
        ]
