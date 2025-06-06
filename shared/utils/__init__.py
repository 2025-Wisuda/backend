"""
Shared Utilities Module

This module provides utility functions for Django admin operations and common tasks
throughout the Teaching Assistant Laboratory Management System.

Components:
- Admin Utils: Django admin bulk operations and action generators

Features:
- Bulk activation/deactivation operations with soft delete support
- Reusable Django admin actions with permission control
- Internationalized success messages with proper pluralization
- Superuser-only operation restrictions for sensitive actions
- Consistent messaging patterns across admin interfaces

Usage:
    from shared.utils import (
        bulk_update_is_active,
        get_bulk_action_message,
        create_activate_action,
        create_deactivate_action
    )

    # In Django admin
    class UserAdmin(admin.ModelAdmin):
        actions = [
            create_activate_action("user", verbose_name="selected users"),
            create_deactivate_action("user", superuser_only=True, verbose_name="selected users")
        ]

    # Direct bulk operations
    updated_count = bulk_update_is_active(queryset, is_active=True)
    message = get_bulk_action_message(updated_count, is_active=True, model_name="course")

Admin Action Features:
- Automatic permission checking for superuser-only actions
- Localized success messages with proper pluralization
- Integration with Django's soft delete pattern (is_active field)
- Consistent action naming and description patterns
- Error handling for unauthorized operations

Integration:
- Compatible with BaseModel soft delete pattern
- Supports all Django admin interfaces
- Follows Django internationalization best practices
- Consistent with system-wide response patterns
"""

from .admin_active_deactive_utils import (
    bulk_update_is_active,
    create_activate_action,
    create_deactivate_action,
)
from .admin_approval_utils import (
    bulk_update_approval_status,
    create_approve_action,
    create_reject_action,
    get_bulk_approval_message,
)
from .availability_time_utils import (
    calculate_available_slots,
    format_available_slots_for_api,
)
from .permission_config_utils import (
    admin_assistant_or_higher,
    admin_lab_head_only,
    admin_laboratory_employee_only,
    admin_laboratory_head_only,
    admin_laboratory_staff_only,
    admin_laboratory_technician_only,
    admin_lecturer_or_higher,
    admin_owner_only,
    admin_owner_or_laboratory_head,
    admin_owner_or_laboratory_staff,
    admin_owner_or_technician,
    admin_require_can_manage_target_user,
    admin_require_groups,
    admin_require_hierarchy_level,
    admin_require_owner_or_groups,
    admin_student_or_higher,
    admin_technician_or_higher,
    assistant_or_higher,
    can_manage_user,
    disable_admin_strict_mode,
    disable_owner_protection,
    disable_staff_bypass,
    enable_admin_strict_mode,
    enable_owner_protection,
    enable_staff_bypass,
    get_manageable_users_queryset,
    get_permission_status,
    get_user_hierarchy_level,
    has_group_permission,
    has_higher_hierarchy,
    has_higher_or_equal_hierarchy,
    is_owner_or_has_permission,
    lab_head_only,
    laboratory_assistant_only,
    laboratory_head_only,
    laboratory_staff_only,
    laboratory_technician_only,
    lecturer_only,
    lecturer_or_higher,
    owner_only,
    owner_or_laboratory_head,
    owner_or_laboratory_staff,
    owner_or_teaching_staff,
    require_can_manage_target_user,
    require_groups,
    require_hierarchy_level,
    require_owner_or_groups,
    student_only,
    student_or_higher,
    teaching_staff_only,
    technician_or_higher,
)

__all__ = [
    # Soft delete utilities
    "create_activate_action",
    "create_deactivate_action",
    "bulk_update_is_active",
    "get_bulk_active_message",
    # Schedule utilities
    "bulk_update_approval_status",
    "create_approve_action",
    "create_reject_action",
    "get_bulk_approval_message",
    # Permission system
    "PermissionConfigUtils",
    "has_group_permission",
    "is_owner_or_has_permission",
    "require_groups",
    "require_owner_or_groups",
    "admin_require_groups",
    "admin_require_owner_or_groups",
    # API convenience decorators
    "laboratory_head_only",
    "laboratory_technician_only",
    "laboratory_assistant_only",
    "student_only",
    "lecturer_only",
    "laboratory_staff_only",
    "teaching_staff_only",
    "owner_only",
    "owner_or_laboratory_head",
    "owner_or_laboratory_staff",
    "owner_or_teaching_staff",
    # Admin convenience decorators
    "admin_laboratory_head_only",
    "admin_laboratory_staff_only",
    "admin_owner_only",
    "admin_owner_or_laboratory_head",
    "admin_owner_or_laboratory_staff",
    "admin_laboratory_employee_only",
    "admin_laboratory_technician_only",
    "admin_owner_or_technician",
    # Hierarchy-based admin decorators
    "admin_lab_head_only",
    "admin_technician_or_higher",
    "admin_assistant_or_higher",
    "admin_student_or_higher",
    "admin_lecturer_or_higher",
    "admin_require_hierarchy_level",
    "admin_require_can_manage_target_user",
    # Hierarchy-based API decorators
    "lab_head_only",
    "technician_or_higher",
    "assistant_or_higher",
    "student_or_higher",
    "lecturer_or_higher",
    "require_hierarchy_level",
    "require_can_manage_target_user",
    # Hierarchy utility functions
    "get_user_hierarchy_level",
    "has_higher_or_equal_hierarchy",
    "has_higher_hierarchy",
    "can_manage_user",
    "get_manageable_users_queryset",
    # Configuration utilities
    "enable_staff_bypass",
    "disable_staff_bypass",
    "enable_admin_strict_mode",
    "disable_admin_strict_mode",
    "enable_owner_protection",
    "disable_owner_protection",
    "get_permission_status",
    # Avaibility time generator utils
    "format_available_slots_for_api",
    "calculate_available_slots",
]
