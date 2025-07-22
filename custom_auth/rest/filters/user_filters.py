"""
User Filters

Django-filters configuration for user list filtering in REST API.
Provides group-based filtering with enum validation.
"""

import django_filters
from django.contrib.auth import get_user_model

from core.enums import UserGroup

User = get_user_model()


class UserFilter(django_filters.FilterSet):
    """
    FilterSet for user queryset filtering.

    Filters:
    - group: Filter users by their assigned user group (enum-validated) - supports single selection
    - groups: Filter users by multiple user groups (enum-validated) - supports multiple selection
    """

    group = django_filters.ChoiceFilter(
        field_name="group",
        choices=UserGroup.choices(),
        help_text="Filter by single user group",
    )
    
    groups = django_filters.MultipleChoiceFilter(
        field_name="group",
        choices=UserGroup.choices(),
        help_text="Filter by multiple user groups (comma-separated)",
    )

    class Meta:
        model = User
        fields = ["group", "groups"]
