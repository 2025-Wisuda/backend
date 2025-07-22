"""
User Export Form

Django form for user data export with customizable field selection and filtering.
Extends base export functionality with user-specific filters and field choices.
"""

from django.utils.translation import gettext_lazy as _

from shared.export import BaseExportForm, ModelSpecificExportFormMixin

from ..user_resource import UserResource


class UserExportForm(BaseExportForm, ModelSpecificExportFormMixin):
    """
    Form for user data export with role-based filtering.

    Features:
    - Predefined field choices from UserResource
    - Default field selection for common exports
    - User group filtering with enum validation
    - Custom filter summary generation
    """

    FIELD_CHOICES = [
        (field, _(field.replace("_", " ").title()))
        for field in UserResource.EXPORT_FIELDS
    ]

    DEFAULT_FIELDS = [
        "username",
        "first_name",
        "last_name",
        "email",
        "group",
        "date_joined",
    ]

    def _setup_custom_fields(self):
        """
        Setup user-specific filter fields.

        Adds user group filter with enum choices for consistent validation.
        """
        super()._setup_custom_fields()

        from core.enums import UserGroup

        GROUP_CHOICES = [] + [(group.value, group.value) for group in UserGroup]

        self.add_choice_filter("group", GROUP_CHOICES, label=_("User Group"))

    def _clean_custom(self, cleaned_data):

        return cleaned_data

    def _get_custom_filter_summary(self, data):
        """
        Generate human-readable summary of applied filters.

        Returns list of filter descriptions for display in export interface.
        """
        summary = []

        group_filter = data.get("group")
        if group_filter and group_filter != "all_groups":
            summary.append(f"Group: {group_filter}")
        elif group_filter == "all_groups":
            summary.append("Group: All User Groups")

        return summary
