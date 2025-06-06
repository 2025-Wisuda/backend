"""
Django Admin Utility Functions

This module provides utility functions for Django admin operations including
bulk actions, message generation, and reusable admin action factories for
the Teaching Assistant Laboratory Management System.

The utilities support the system's soft delete pattern using the is_active field
from BaseModel, providing consistent admin interface functionality across all
models in the system.

Features:
- Bulk operations with automatic message generation
- Permission-controlled admin actions (superuser restrictions)
- Internationalized messages with proper pluralization
- Reusable action factories for consistent admin interfaces
- Integration with Django's soft delete pattern
- Error handling for unauthorized operations

Design Principles:
- Consistency: Same patterns across all admin interfaces
- Security: Permission checks for sensitive operations
- Usability: Clear messaging and proper pluralization
- Reusability: Factory functions for common admin actions
- Internationalization: Full i18n support for multi-language systems

Integration:
- Works seamlessly with BaseModel's is_active field
- Compatible with Django admin action system
- Follows Django best practices for admin customization
- Supports permission-based operation restrictions
"""

from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils.translation import ngettext


class AdminActiveDeactiveUtils:
    """
    Utility class for Django admin operations.

    Provides methods for bulk operations, message generation,
    and common admin functionality.
    """

    @staticmethod
    def generate_message(count, model_name, action_type):
        """Generate internationalized message for admin actions."""
        if action_type == "activate":
            return (
                ngettext(
                    f"%d {model_name} was successfully activated.",
                    f"%d {model_name}s were successfully activated.",
                    count,
                )
                % count
            )
        else:
            return (
                ngettext(
                    f"%d {model_name} was successfully deactivated.",
                    f"%d {model_name}s were successfully deactivated.",
                    count,
                )
                % count
            )

    @staticmethod
    def bulk_update_is_active(queryset, is_active=True, action_name=None):
        """Bulk update is_active field for a queryset."""
        count = queryset.update(is_active=is_active)
        return count


def bulk_update_is_active(queryset, is_active=True, action_name=None):
    """
    Bulk update is_active field for a queryset.

    Args:
        queryset: Django queryset to update
        is_active: Boolean value to set
        action_name: Optional name for the action (used in messages)

    Returns:
        Number of updated records
    """
    updated = queryset.update(is_active=is_active)
    return updated


def get_bulk_action_message(count, is_active=True, model_name="item"):
    """
    Generate bulk action success message with proper pluralization.

    Args:
        count: Number of updated items
        is_active: Whether items were activated or deactivated
        model_name: Name of the model (singular form)

    Returns:
        Localized message string
    """
    if is_active:
        return (
            ngettext(
                f"%d {model_name} was successfully activated.",
                f"%d {model_name}s were successfully activated.",
                count,
            )
            % count
        )
    else:
        return (
            ngettext(
                f"%d {model_name} was successfully deactivated.",
                f"%d {model_name}s were successfully deactivated.",
                count,
            )
            % count
        )


def create_activate_action(model_name="item", superuser_only=False, verbose_name=None):
    """
    Create a reusable activate action for Django admin.

    This factory function generates a Django admin action that can activate
    (restore) multiple items at once using the soft delete pattern. The action
    respects permission levels and provides proper user feedback.

    Args:
        model_name (str): Name of the model in singular form, lowercase.
                         Used for message generation (e.g., "user", "course")
        superuser_only (bool): Whether this action requires superuser permissions.
                              If True, only superusers can execute this action
        verbose_name (str, optional): Human-readable name for the action description.
                                     If not provided, uses model_name

    Returns:
        function: Django admin action function that can be added to ModelAdmin.actions

    Action Behavior:
        - Checks superuser permission if superuser_only=True
        - Updates is_active=True for selected items (soft delete restoration)
        - Shows success message with count of updated items
        - Shows error message if permission denied

    Generated Action Properties:
        - short_description: Localized action description for admin interface
        - Function name: activate_items (for debugging and introspection)

    Usage:
        class UserAdmin(admin.ModelAdmin):
            actions = [
                create_activate_action("user", verbose_name="selected users"),
                create_activate_action("course", superuser_only=True, verbose_name="selected courses")
            ]

    Example Messages:
        - Success: "1 user was successfully activated." / "5 users were successfully activated."
        - Error: "Only superusers can perform this action."

    Security:
        - Permission checking prevents unauthorized access
        - Proper error messaging for transparency
        - Audit trail maintained through BaseModel fields
    """

    def activate_items(modeladmin, request, queryset):
        if superuser_only and not request.user.is_superuser:
            modeladmin.message_user(
                request,
                _("Only superusers can perform this action."),
                level=messages.ERROR,
            )
            return

        updated = bulk_update_is_active(queryset, is_active=True)
        message = get_bulk_action_message(
            updated, is_active=True, model_name=model_name
        )
        modeladmin.message_user(request, message)

    activate_items.short_description = verbose_name or _(
        f"Activate selected {model_name}s"
    )
    return activate_items


def create_deactivate_action(
    model_name="item", superuser_only=False, verbose_name=None
):
    """
    Create a reusable deactivate action for Django admin.

    This factory function generates a Django admin action that can deactivate
    (soft delete) multiple items at once. The action respects permission levels
    and provides proper user feedback with security considerations.

    Args:
        model_name (str): Name of the model in singular form, lowercase.
                         Used for message generation (e.g., "user", "course")
        superuser_only (bool): Whether this action requires superuser permissions.
                              Recommended True for sensitive operations
        verbose_name (str, optional): Human-readable name for the action description.
                                     If not provided, uses model_name

    Returns:
        function: Django admin action function that can be added to ModelAdmin.actions

    Action Behavior:
        - Checks superuser permission if superuser_only=True
        - Updates is_active=False for selected items (soft delete)
        - Shows success message with count of updated items
        - Shows error message if permission denied

    Generated Action Properties:
        - short_description: Localized action description for admin interface
        - Function name: deactivate_items (for debugging and introspection)

    Usage:
        class UserAdmin(admin.ModelAdmin):
            actions = [
                create_deactivate_action("user", superuser_only=True, verbose_name="selected users"),
                create_deactivate_action("session", verbose_name="selected sessions")
            ]

    Example Messages:
        - Success: "1 user was successfully deactivated." / "3 users were successfully deactivated."
        - Error: "Only superusers can perform this action."

    Security Considerations:
        - Soft delete preserves data integrity and audit trail
        - Superuser restriction prevents accidental data loss
        - Permission checking with clear error messaging
        - Maintains referential integrity (unlike hard delete)

    Note:
        For sensitive models (users, courses, etc.), always set superuser_only=True
        to prevent accidental deactivation by staff members.
    """

    def deactivate_items(modeladmin, request, queryset):
        if superuser_only and not request.user.is_superuser:
            modeladmin.message_user(
                request,
                _("Only superusers can perform this action."),
                level=messages.ERROR,
            )
            return

        updated = bulk_update_is_active(queryset, is_active=False)
        message = get_bulk_action_message(
            updated, is_active=False, model_name=model_name
        )
        modeladmin.message_user(request, message)

    deactivate_items.short_description = verbose_name or _(
        f"Deactivate selected {model_name}s"
    )
    return deactivate_items
