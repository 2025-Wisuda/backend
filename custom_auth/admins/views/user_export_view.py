"""
User Export View

Django admin view for user data export with filtering and customization.
Extends base export functionality with user-specific logic and security controls.
"""

from shared.export import BaseExportView

from ...models import CustomUserModel
from ..forms.user_export_form import UserExportForm
from ..user_resource import UserResource


class UserExportView(BaseExportView):
    """
    Export view for user data with role-based filtering and security controls.

    Features:
    - Excludes superusers from export by default
    - Group-based filtering with enum validation
    - Custom filename generation with filter indicators
    - Laboratory employee permission checking
    """

    model = CustomUserModel
    resource_class = UserResource
    form_class = UserExportForm
    template_name = "admin/custom_auth/customusermodel/export_form.html"

    permission_check_method = "_has_lab_employee_permission"
    export_filename_prefix = "users"

    def _get_base_queryset(self, request):
        """
        Get base queryset excluding superusers.

        Security measure to prevent export of admin accounts.
        """
        queryset = super()._get_base_queryset(request)
        return queryset.filter(is_superuser=False)

    def _apply_custom_filters(self, queryset, filters):
        """
        Apply user-specific filters to the export queryset.

        Filters by user group with support for 'all_groups' option.
        """
        group_filter = filters.get("group")
        if group_filter and group_filter != "all_groups":
            queryset = queryset.filter(group=group_filter)

        return queryset

    def _get_custom_filename_parts(self, filters):
        parts = []

        group_filter = filters.get("group")
        if group_filter and group_filter != "all_groups":
            parts.append(f'group_{group_filter.lower().replace(" ", "_")}')
        elif group_filter == "all_groups":
            parts.append("all_groups")

        return parts

    def _get_custom_filter_info(self, filters):
        filter_info = []

        group_filter = filters.get("group")
        if group_filter and group_filter != "all_groups":
            filter_info.append(f"group {group_filter}")
        elif group_filter == "all_groups":
            filter_info.append("all user groups")

        return filter_info

    def _customize_resource_for_export(self, resource, form_data):

        selected_fields = form_data.get("selected_fields", [])

        if selected_fields:
            field_mapping = dict(self.form_class.FIELD_CHOICES)

            original_export_order = resource._meta.export_order
            filtered_export_order = tuple(
                field for field in original_export_order if field in selected_fields
            )

            resource._meta.export_order = filtered_export_order

            resource._meta.fields = tuple(
                field for field in resource._meta.fields if field in selected_fields
            )

            import logging

            logger = logging.getLogger(__name__)
            logger.info(f"Export fields customized: {', '.join(selected_fields)}")

        return resource
