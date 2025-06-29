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
    
    Provides filtering by date range, visitor name, and purpose
    with case-insensitive search capabilities.
    """
    
    visit_date = django_filters.DateFilter(
        field_name="date",
        help_text="Filter by specific visit date (YYYY-MM-DD format)"
    )
    
    visit_date_from = django_filters.DateFilter(
        field_name="date",
        lookup_expr="gte",
        help_text="Filter visits from this date onwards"
    )
    
    visit_date_to = django_filters.DateFilter(
        field_name="date", 
        lookup_expr="lte",
        help_text="Filter visits up to this date"
    )
    
    visitor_name = django_filters.CharFilter(
        method="filter_visitor_name",
        help_text="Search by visitor name (case-insensitive)"
    )
    
    purpose = django_filters.CharFilter(
        field_name="purpose",
        lookup_expr="icontains",
        help_text="Search by visit purpose (case-insensitive)"
    )
    
    class Meta:
        model = GuestVisitModel
        fields = [
            "visit_date",
            "visit_date_from", 
            "visit_date_to",
            "visitor_name",
            "purpose",
        ]
        
    def filter_visitor_name(self, queryset, name, value):
        """
        Filter by visitor name from either manual entry or user reference.
        """
        if not value:
            return queryset
            
        return queryset.filter(
            models.Q(name__icontains=value) |
            models.Q(visitor__first_name__icontains=value) |
            models.Q(visitor__last_name__icontains=value) |
            models.Q(visitor__username__icontains=value)
        )
