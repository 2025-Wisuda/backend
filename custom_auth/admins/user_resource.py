"""
User Import/Export Resource.

Django-import-export resource for bulk user operations with role-based validation,
automatic username generation, and duplicate detection.
"""

from core.enums import UserGroup
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from import_export import fields, resources
from import_export.widgets import CharWidget
from shared.format.custom_xlsx_format import AutoFitXLSX

from ..models import CustomUserModel


class EmptyToNullCharWidget(CharWidget):
    """Custom widget to convert empty strings to None for nullable fields."""

    def clean(self, value, row=None, **kwargs):
        value = super().clean(value, row, **kwargs)
        if isinstance(value, str) and not value.strip():
            return None
        return value


# Field definitions for import/export operations
IMPORT_FIELDS = (
    "username",
    "first_name",
    "last_name",
    "email",
    "group",
    "student_number",
    "employee_number",
    "password",
)

EXPORT_FIELDS = (
    "username",
    "first_name",
    "last_name",
    "email",
    "group",
    "student_number",
    "employee_number",
    "date_joined",
    "last_login",
    "created_at",
    "updated_at",
)


class UserResource(resources.ModelResource):
    """
    Django-import-export resource for bulk user operations.

    Features:
    - Role-based validation (student vs staff requirements)
    - Automatic username generation with collision handling
    - Duplicate detection and password management
    - Excel export with professional formatting
    """

    # Field configuration
    IMPORT_FIELDS = IMPORT_FIELDS
    EXPORT_FIELDS = EXPORT_FIELDS

    # Custom field widgets for null handling
    student_number = fields.Field(
        column_name="student_number",
        attribute="student_number",
        widget=EmptyToNullCharWidget(),
    )
    employee_number = fields.Field(
        column_name="employee_number",
        attribute="employee_number",
        widget=EmptyToNullCharWidget(),
    )

    class Meta:
        """Resource configuration for user import/export operations."""

        model = CustomUserModel
        import_id_fields = []
        fields = IMPORT_FIELDS
        import_fields = IMPORT_FIELDS
        export_order = EXPORT_FIELDS
        export_format_types = [AutoFitXLSX]

    def get_export_headers(self, *args, **kwargs):
        """Format export headers for readability (e.g., 'first_name' -> 'First Name')."""
        headers = super().get_export_headers(*args, **kwargs)
        return [header.replace("_", " ").title() for header in headers]

    def import_obj(self, obj, data, dry_run, **kwargs):
        """
        Validate import data with role-based checks.

        Required: first_name, last_name, group
        Students: require student_number, no employee_number
        Staff: require employee_number, no student_number
        """
        first_name = str(data.get("first_name", "")).strip()
        last_name = str(data.get("last_name", "")).strip()
        group = str(data.get("group", "")).strip()
        student_number = str(data.get("student_number", "")).strip()
        employee_number = str(data.get("employee_number", "")).strip()

        errors = []

        # Required field validation
        if not first_name:
            errors.append(_("First Name is required"))
        if not last_name:
            errors.append(_("Last Name is required"))
        if not group:
            errors.append(_("Group is required"))

        # Group validation with enum checking
        valid_groups = [g.value for g in UserGroup]
        staff_groups = UserGroup.staff_groups()
        student_groups = UserGroup.student_groups()

        if group and group not in valid_groups:
            errors.append(
                _("Invalid group '%(group)s'. Valid groups: %(valid_groups)s")
                % {"group": group, "valid_groups": ", ".join(valid_groups)}
            )

        # Role-specific identifier validation
        if group in student_groups:
            if not student_number:
                errors.append(
                    _("Student Number is required for group '%(group)s'")
                    % {"group": group}
                )
            if employee_number:
                errors.append(
                    _("Employee Number should not be provided for group '%(group)s'")
                    % {"group": group}
                )
        elif group in staff_groups:
            if not employee_number:
                errors.append(
                    _("Employee Number is required for group '%(group)s'")
                    % {"group": group}
                )
            if student_number:
                errors.append(
                    _("Student Number should not be provided for group '%(group)s'")
                    % {"group": group}
                )

        if errors:
            raise ValidationError("; ".join(errors))

        # Handle password for bulk imports
        if "password" in data:
            obj._password_to_set = data["password"]

        return super().import_obj(obj, data, dry_run, **kwargs)

    def before_import_row(self, row, **kwargs):
        """
        Generate username and setup user data before import.

        Username format: {first_initial}.{last_name}{id_prefix}
        Handles collisions with incremental counters.
        """
        first_name = str(row.get("first_name", "")).strip()
        last_name = str(row.get("last_name", "")).strip()
        group = str(row.get("group", "")).strip()
        student_number = str(row.get("student_number", "")).strip()
        employee_number = str(row.get("employee_number", "")).strip()

        staff_groups = UserGroup.staff_groups()
        student_groups = UserGroup.student_groups()

        if group in staff_groups:
            row["student_number"] = None
        elif group in student_groups:
            row["employee_number"] = None

        if first_name and last_name:
            first_initial = first_name[0].lower()
            clean_last_name = slugify(last_name.lower().replace(" ", ""))

            id_number = student_number or employee_number
            if id_number and len(id_number) >= 2:
                id_prefix = id_number[:2]
                base_username = f"{first_initial}.{clean_last_name}{id_prefix}"
            else:
                base_username = f"{first_initial}.{clean_last_name}"

            username = base_username
            counter = 1

            while CustomUserModel.objects.filter(username=username).exists():
                if id_number and len(id_number) >= 2:
                    id_prefix = id_number[:2]
                    username = f"{first_initial}.{clean_last_name}{id_prefix}{counter}"
                else:
                    username = f"{first_initial}.{clean_last_name}{counter}"
                counter += 1

            row["username"] = username
            row["password"] = username

        if group in UserGroup.is_admin_staff_groups():
            row["is_staff"] = True
        else:
            row["is_staff"] = False

        row["is_active"] = True

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """
        Skip rows with validation errors or duplicate identifiers.

        Skips if: missing required fields, invalid group, missing role-specific
        identifiers, or duplicate student/employee numbers.
        """
        first_name = str(row.get("first_name", "")).strip()
        last_name = str(row.get("last_name", "")).strip()
        group = str(row.get("group", "")).strip()
        student_number = str(row.get("student_number", "")).strip()
        employee_number = str(row.get("employee_number", "")).strip()

        valid_groups = [g.value for g in UserGroup]
        staff_groups = UserGroup.staff_groups()
        student_groups = UserGroup.student_groups()

        if not first_name or not last_name or not group:
            return True
        if group not in valid_groups:
            return True
        if group in student_groups and not student_number:
            return True
        elif group in staff_groups and not employee_number:
            return True
        if (
            student_number
            and CustomUserModel.objects.filter(student_number=student_number).exists()
        ):
            return True
        if (
            employee_number
            and CustomUserModel.objects.filter(employee_number=employee_number).exists()
        ):
            return True
        return super().skip_row(instance, original, row, import_validation_errors)

    def after_save_instance(self, instance, row, **kwargs):
        """Hash and save password after successful import (non-dry runs only)."""
        if not kwargs.get("dry_run", False) and hasattr(instance, "_password_to_set"):
            instance.set_password(instance._password_to_set)
            instance.save()

    def dehydrate_group(self, user):
        """Export group field with null handling."""
        return user.group if user.group else ""

    def dehydrate_student_number(self, user):
        """Export student_number field with null handling."""
        return user.student_number if user.student_number else ""

    def dehydrate_employee_number(self, user):
        """Export employee_number field with null handling."""
        return user.employee_number if user.employee_number else ""

    def dehydrate_created_at(self, user):
        """Format created_at for export with i18n support."""
        if user.created_at:
            try:
                import locale

                locale.setlocale(locale.LC_TIME, "id_ID.utf8")
            except locale.Error:
                pass  # fallback: will format in English

            day = user.created_at.strftime("%d").lstrip("0")
            month_year = user.created_at.strftime("%B %Y")
            time = user.created_at.strftime("%H:%M")
            return f"{day} {month_year}, {time}"
        return ""

    def dehydrate_updated_at(self, user):
        """Format updated_at for export with i18n support."""
        if user.updated_at:
            try:
                import locale

                locale.setlocale(locale.LC_TIME, "id_ID.utf8")
            except locale.Error:
                pass  # fallback: will format in English

            day = user.updated_at.strftime("%d").lstrip("0")
            month_year = user.updated_at.strftime("%B %Y")
            time = user.updated_at.strftime("%H:%M")
            return f"{day} {month_year}, {time}"
        return ""

    def dehydrate_date_joined(self, user):
        """Format date_joined for export with i18n support."""
        if user.date_joined:
            try:
                import locale

                locale.setlocale(locale.LC_TIME, "id_ID.utf8")
            except locale.Error:
                pass  # fallback: will format in English

            day = user.date_joined.strftime("%d").lstrip("0")
            month_year = user.date_joined.strftime("%B %Y")
            return f"{day} {month_year}"
        return ""

    def dehydrate_last_login(self, user):
        """Format last_login for export with i18n support."""
        if user.last_login:
            try:
                import locale

                locale.setlocale(locale.LC_TIME, "id_ID.utf8")
            except locale.Error:
                pass  # fallback: will format in English

            day = user.last_login.strftime("%d").lstrip("0")
            month_year = user.last_login.strftime("%B %Y")
            time = user.last_login.strftime("%H:%M")
            return f"{day} {month_year}, {time}"
        return ""
