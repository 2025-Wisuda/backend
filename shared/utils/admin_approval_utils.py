"""
Django Admin Approval Utility Functions

This module provides utility functions for Django admin approval operations including
bulk actions, message generation, and reusable admin action factories for
the Teaching Assistant Laboratory Management System.

The utilities support the system's approval pattern using the ApprovalMixin,
providing consistent admin interface functionality across all models that
require approval workflow.

Features:
- Bulk approval/rejection operations with automatic message generation
- Permission-controlled admin actions (staff-only restrictions)
- Internationalized messages with proper pluralization
- Reusable action factories for consistent admin interfaces
- Integration with Django's ApprovalMixin pattern
- Error handling for unauthorized operations and validation errors

Design Principles:
- Consistency: Same patterns across all admin interfaces
- Security: Permission checks for sensitive operations
- Usability: Clear messaging and proper pluralization
- Reusability: Factory functions for common admin actions
- Internationalization: Full i18n support for multi-language systems

Integration:
- Works seamlessly with ApprovalMixin's approve() and reject() methods
- Compatible with Django admin action system
- Follows Django best practices for admin customization
- Supports permission-based operation restrictions
"""

from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from core.enums import ApprovalStatus


class AdminApprovalUtils:
    """
    Utility class for Django admin approval operations.

    Provides methods for bulk approval operations, message generation,
    and common admin functionality for approval workflows.
    """

    @staticmethod
    def generate_message(count, model_name, action_type):
        """Generate internationalized message for admin approval actions."""
        if action_type == "approve":
            return (
                ngettext(
                    f"%d {model_name} was successfully approved.",
                    f"%d {model_name}s were successfully approved.",
                    count,
                )
                % count
            )
        else:  # reject
            return (
                ngettext(
                    f"%d {model_name} was successfully rejected.",
                    f"%d {model_name}s were successfully rejected.",
                    count,
                )
                % count
            )

    @staticmethod
    def bulk_update_approval_status(queryset, action_type, user, action_name=None):
        """
        Bulk update approval status for a queryset using ApprovalMixin methods.

        Args:
            queryset: Django queryset to update
            action_type: Either "approve" or "reject"
            user: User performing the action
            action_name: Optional name for the action (used in messages)

        Returns:
            Number of updated records
        """
        updated = 0

        # Only process items that are in PENDING status
        pending_queryset = queryset.filter(
            **{f"{queryset.model.APPROVAL_STATUS_FIELD}": ApprovalStatus.PENDING.value}
        )

        for item in pending_queryset:
            try:
                if action_type == "approve":
                    item.approve(approved_by=user)
                elif action_type == "reject":
                    item.reject(rejected_by=user)

                item.save()
                updated += 1
            except Exception:
                continue

        return updated


def bulk_update_approval_status(queryset, action_type, user, action_name=None):
    """
    Bulk update approval status for a queryset using ApprovalMixin methods.

    Args:
        queryset: Django queryset to update
        action_type: Either "approve" or "reject"
        user: User performing the action
        action_name: Optional name for the action (used in messages)

    Returns:
        Number of updated records
    """
    updated = 0

    # Only process items that are in PENDING status
    pending_queryset = queryset.filter(
        **{f"{queryset.model.APPROVAL_STATUS_FIELD}": ApprovalStatus.PENDING.value}
    )

    for item in pending_queryset:
        try:
            if action_type == "approve":
                item.approve(approved_by=user)
            elif action_type == "reject":
                item.reject(rejected_by=user)

            item.save()
            updated += 1
        except Exception:
            # Skip items that fail validation or have other issues
            continue

    return updated


def get_bulk_approval_message(count, action_type="approve", model_name="item"):
    """
    Generate bulk approval action success message with proper pluralization.

    Args:
        count: Number of updated items
        action_type: Either "approve" or "reject"
        model_name: Name of the model (singular form)

    Returns:
        Localized message string
    """
    if action_type == "approve":
        return (
            ngettext(
                f"%d {model_name} was successfully approved.",
                f"%d {model_name}s were successfully approved.",
                count,
            )
            % count
        )
    else:  # reject
        return (
            ngettext(
                f"%d {model_name} was successfully rejected.",
                f"%d {model_name}s were successfully rejected.",
                count,
            )
            % count
        )


def create_approve_action(model_name="item", staff_only=True, verbose_name=None):
    """
    Create a reusable approve action for Django admin.

    This factory function generates a Django admin action that can approve
    multiple items at once using the ApprovalMixin pattern. The action
    respects permission levels and provides proper user feedback.

    Args:
        model_name (str): Name of the model in singular form, lowercase.
                         Used for message generation (e.g., "schedule", "request")
        staff_only (bool): Whether this action requires staff permissions.
                          If True, only staff users can execute this action
        verbose_name (str, optional): Human-readable name for the action description.
                                     If not provided, uses model_name

    Returns:
        function: Django admin action function that can be added to ModelAdmin.actions

    Action Behavior:
        - Checks staff permission if staff_only=True
        - Calls approve() method on selected items that are in PENDING status
        - Shows success message with count of updated items
        - Shows error message if permission denied

    Generated Action Properties:
        - short_description: Localized action description for admin interface
        - Function name: approve_items (for debugging and introspection)

    Usage:
        class ScheduleAdmin(admin.ModelAdmin):
            actions = [
                create_approve_action("schedule", verbose_name="selected schedules"),
                create_approve_action("request", staff_only=True, verbose_name="selected requests")
            ]

    Example Messages:
        - Success: "1 schedule was successfully approved." / "5 schedules were successfully approved."
        - Error: "Only staff members can perform this action."

    Security:
        - Permission checking prevents unauthorized access
        - Only processes items in PENDING status
        - Proper error messaging for transparency
        - Audit trail maintained through ApprovalMixin fields
    """

    def approve_items(modeladmin, request, queryset):
        if staff_only and not request.user.is_staff:
            modeladmin.message_user(
                request,
                _("Only staff members can perform this action."),
                level=messages.ERROR,
            )
            return

        updated = bulk_update_approval_status(queryset, "approve", request.user)
        message = get_bulk_approval_message(
            updated, action_type="approve", model_name=model_name
        )
        modeladmin.message_user(request, message)

    approve_items.short_description = verbose_name or _(
        f"Approve selected {model_name}s"
    )
    return approve_items


def create_reject_action(model_name="item", staff_only=True, verbose_name=None):
    """
    Create a reusable reject action for Django admin.

    This factory function generates a Django admin action that can reject
    multiple items at once using the ApprovalMixin pattern. The action
    respects permission levels and provides proper user feedback with
    security considerations.

    Args:
        model_name (str): Name of the model in singular form, lowercase.
                         Used for message generation (e.g., "schedule", "request")
        staff_only (bool): Whether this action requires staff permissions.
                          Recommended True for approval operations
        verbose_name (str, optional): Human-readable name for the action description.
                                     If not provided, uses model_name

    Returns:
        function: Django admin action function that can be added to ModelAdmin.actions

    Action Behavior:
        - Checks staff permission if staff_only=True
        - Calls reject() method on selected items that are in PENDING status
        - Shows success message with count of updated items
        - Shows error message if permission denied

    Generated Action Properties:
        - short_description: Localized action description for admin interface
        - Function name: reject_items (for debugging and introspection)

    Usage:
        class ScheduleAdmin(admin.ModelAdmin):
            actions = [
                create_reject_action("schedule", staff_only=True, verbose_name="selected schedules"),
                create_reject_action("request", verbose_name="selected requests")
            ]

    Example Messages:
        - Success: "1 schedule was successfully rejected." / "3 schedules were successfully rejected."
        - Error: "Only staff members can perform this action."

    Security Considerations:
        - Staff restriction prevents unauthorized rejections
        - Permission checking with clear error messaging
        - Only processes items in PENDING status
        - Maintains audit trail through ApprovalMixin timestamp and user fields

    Note:
        For sensitive models (schedules, requests, etc.), always set staff_only=True
        to prevent accidental rejections by non-staff members.
    """

    def reject_items(modeladmin, request, queryset):
        if staff_only and not request.user.is_staff:
            modeladmin.message_user(
                request,
                _("Only staff members can perform this action."),
                level=messages.ERROR,
            )
            return

        updated = bulk_update_approval_status(queryset, "reject", request.user)
        message = get_bulk_approval_message(
            updated, action_type="reject", model_name=model_name
        )
        modeladmin.message_user(request, message)

    reject_items.short_description = verbose_name or _(f"Reject selected {model_name}s")
    return reject_items
