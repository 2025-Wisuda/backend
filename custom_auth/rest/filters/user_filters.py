"""
Django filters for user-related API endpoints.

Provides simple filtering capabilities for user ViewSet using django-filter.
"""

import django_filters
from django.contrib.auth import get_user_model

from core.enums import UserGroup

User = get_user_model()


class UserFilter(django_filters.FilterSet):
    """
    Simple filter set for User model.

    Provides basic filtering by group only.
    Search functionality is handled by DRF SearchFilter.
    """

    group = django_filters.ChoiceFilter(
        field_name="group",
        choices=UserGroup.choices(),
        help_text="Filter by user group",
    )

    class Meta:
        model = User
        fields = ["group"]
