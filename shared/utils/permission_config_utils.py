"""
Permission configuration and utilities for API and Django admin.
Edit configurations here to control permission behavior across the application.
"""

from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.enums.user_group_enum import UserGroup
from shared.presenter import ResponsePresenter


class PermissionConfigUtils:
    """
    Global permission configuration settings.

    STAFF_BYPASS_ENABLED:
    - True: Staff members (is_staff=True) can bypass group restrictions
    - False: Strict group-based permissions, no bypass for staff

    ADMIN_STRICT_MODE:
    - True: Admin users cannot edit data belonging to other users (owner protection)
    - False: Admin users can edit all data regardless of ownership

    OWNER_PROTECTION_ENABLED:
    - True: Users can only edit/delete their own data
    - False: Disable owner protection checks

    Hierarchy system: lower number = higher authority
    GROUP_HIERARCHY:
    - Defines the authority level of each user group
    - Lower numbers indicate higher authority
    """

    STAFF_BYPASS_ENABLED = False
    ADMIN_STRICT_MODE = False  # Set True for strict admin mode
    OWNER_PROTECTION_ENABLED = True  # Set False to disable owner checks

    # Hierarchy system: lower number = higher authority
    GROUP_HIERARCHY = {
        UserGroup.LABORATORY_HEAD: 1,  # Laboratory Head (highest)
        UserGroup.LABORATORY_TECHNICIAN: 2,  # Laboratory Technician
        UserGroup.LABORATORY_ASSISTANT: 3,  # Laboratory Assistant
        UserGroup.STUDENT: 4,  # Student
        UserGroup.LECTURER: 5,  # Lecturer (lowest)
    }


def has_group_permission(user, required_groups):
    """
    Check if user has permission based on required groups.

    Args:
        user: Django user instance
        required_groups: UserGroup enum or list of UserGroup enums

    Returns:
        bool: True if user has permission
    """
    # Superuser always has permission
    if user.is_superuser:
        return True

    # Convert single group to list for consistent processing
    if not isinstance(required_groups, list):
        required_groups = [required_groups]

    # Staff bypass check - allows staff to access if bypass is enabled
    if PermissionConfigUtils.STAFF_BYPASS_ENABLED and user.is_staff:
        return True

    # Normal group-based permission check
    user_group = getattr(user, "group", None)
    allowed_group_values = [group.value for group in required_groups]

    return user_group in allowed_group_values


def is_owner_or_has_permission(user, object_instance, required_groups=None):
    """
    Check if user is owner of object OR has required group permissions.

    Args:
        user: Django user instance
        object_instance: Model instance with 'user' or 'created_by' field
        required_groups: UserGroup enum or list of UserGroup enums (optional)

    Returns:
        bool: True if user is owner or has required permissions
    """
    # Superuser always has permission
    if user.is_superuser:
        return True

    # Skip owner protection if disabled
    if not PermissionConfigUtils.OWNER_PROTECTION_ENABLED:
        return True

    # Check if user is the owner of the object
    # For User objects, check if the user is the object itself
    if (
        hasattr(object_instance, "_meta")
        and object_instance._meta.model_name == "customusermodel"
    ):
        if object_instance == user:
            return True
        # For user objects, if it's not the same user, check group permissions later
    else:
        # For other objects, check user or created_by field
        owner_field = getattr(object_instance, "user", None) or getattr(
            object_instance, "created_by", None
        )
        if owner_field == user:
            return True

    # Admin strict mode - even staff cannot edit other users' data
    if PermissionConfigUtils.ADMIN_STRICT_MODE:
        return False

    # Check group permissions if required groups are specified
    if required_groups:
        return has_group_permission(user, required_groups)

    # Default to staff bypass check if no specific groups required
    return PermissionConfigUtils.STAFF_BYPASS_ENABLED and user.is_staff


def require_groups(
    allowed_groups,
    error_message=None,
    ignore_staff_bypass=False,
    custom_check=None,
    include_superuser=True,
):
    """
    Decorator to check group permissions for API views with enhanced flexibility.

    Args:
        allowed_groups: UserGroup enum or list of UserGroup enums
        error_message: Custom error message for permission denial
        ignore_staff_bypass: If True, ignore the global STAFF_BYPASS_ENABLED setting
        custom_check: Optional callable that takes (user, request, *args, **kwargs) and returns bool
        include_superuser: If False, superuser bypass is disabled for this decorator

    Usage:
        @require_groups(UserGroup.LABORATORY_ASSISTANT)
        @require_groups([UserGroup.LABORATORY_HEAD, UserGroup.LABORATORY_TECHNICIAN])
        @require_groups(UserGroup.LABORATORY_HEAD, "Only lab head can perform this action")
        @require_groups(UserGroup.LABORATORY_TECHNICIAN, ignore_staff_bypass=True)
        @require_groups(UserGroup.LABORATORY_HEAD, custom_check=lambda user, request: user.is_active)

    Example:
        @require_groups(UserGroup.LABORATORY_HEAD, "Only lab head can perform this action")
        def sensitive_operation(self, request):
            pass
    """

    def decorator(view_function):
        @wraps(view_function)
        def wrapper(self, request, *args, **kwargs):
            # Check superuser permission if enabled
            if include_superuser and request.user.is_superuser:
                # Run custom check if provided
                if custom_check and not custom_check(
                    request.user, request, *args, **kwargs
                ):
                    message = error_message or _("Custom permission check failed")
                    return ResponsePresenter.forbidden_response(message)
                return view_function(self, request, *args, **kwargs)

            # Convert single group to list for consistent processing
            if not isinstance(allowed_groups, list):
                groups_to_check = [allowed_groups]
            else:
                groups_to_check = allowed_groups

            # Staff bypass check - unless explicitly ignored
            if (
                not ignore_staff_bypass
                and PermissionConfigUtils.STAFF_BYPASS_ENABLED
                and request.user.is_staff
            ):
                # Run custom check if provided
                if custom_check and not custom_check(
                    request.user, request, *args, **kwargs
                ):
                    message = error_message or _("Custom permission check failed")
                    return ResponsePresenter.forbidden_response(message)
                return view_function(self, request, *args, **kwargs)

            # Normal group-based permission check
            user_group = getattr(request.user, "group", None)
            allowed_group_values = [group.value for group in groups_to_check]

            if user_group not in allowed_group_values:
                message = error_message or _(
                    "Insufficient permissions to access this resource"
                )
                return ResponsePresenter.forbidden_response(message)

            # Run custom check if provided
            if custom_check and not custom_check(
                request.user, request, *args, **kwargs
            ):
                message = error_message or _("Custom permission check failed")
                return ResponsePresenter.forbidden_response(message)

            return view_function(self, request, *args, **kwargs)

        return wrapper

    return decorator


def require_owner_or_groups(
    allowed_groups=None,
    error_message=None,
    ignore_staff_bypass=False,
    custom_check=None,
    include_superuser=True,
    strict_owner_check=False,
):
    """
    Decorator to check owner OR group permissions for API views with enhanced flexibility.
    Useful for endpoints where users can access their own data or authorized groups can access any data.

    Args:
        allowed_groups: UserGroup enum or list of UserGroup enums (optional)
        error_message: Custom error message for permission denial
        ignore_staff_bypass: If True, ignore the global STAFF_BYPASS_ENABLED setting
        custom_check: Optional callable that takes (user, request, object_instance, *args, **kwargs) and returns bool
        include_superuser: If False, superuser bypass is disabled for this decorator
        strict_owner_check: If True, ignores global OWNER_PROTECTION_ENABLED setting

    Usage:
        @require_owner_or_groups()  # Owner only access
        @require_owner_or_groups([UserGroup.LABORATORY_HEAD])  # Owner or lab head
        @require_owner_or_groups([UserGroup.LABORATORY_HEAD, UserGroup.LABORATORY_TECHNICIAN])
        @require_owner_or_groups([UserGroup.LABORATORY_HEAD], strict_owner_check=True)
        @require_owner_or_groups([UserGroup.LABORATORY_HEAD],
                                custom_check=lambda user, request, obj: obj.is_active)

    Example:
        @require_owner_or_groups([UserGroup.LABORATORY_HEAD], "Only owner or lab head can modify")
        def update_schedule(self, request):
            pass
    """

    def decorator(view_function):
        @wraps(view_function)
        def wrapper(self, request, *args, **kwargs):
            # Get the object instance from the view
            object_instance = self.get_object()

            # Check superuser permission if enabled
            if include_superuser and request.user.is_superuser:
                # Run custom check if provided
                if custom_check and not custom_check(
                    request.user, request, object_instance, *args, **kwargs
                ):
                    message = error_message or _("Custom permission check failed")
                    return ResponsePresenter.forbidden_response(message)
                return view_function(self, request, *args, **kwargs)

            # Owner protection check - either strict or global setting
            owner_protection_enabled = (
                strict_owner_check or PermissionConfigUtils.OWNER_PROTECTION_ENABLED
            )

            if owner_protection_enabled:
                # Check if user is the owner of the object
                # For User objects, check if the user is the object itself
                is_owner = False
                if (
                    hasattr(object_instance, "_meta")
                    and object_instance._meta.model_name == "customusermodel"
                ):
                    is_owner = object_instance == request.user
                else:
                    # For other objects, check user or created_by field
                    owner_field = getattr(object_instance, "user", None) or getattr(
                        object_instance, "created_by", None
                    )
                    is_owner = owner_field == request.user

                if is_owner:
                    # Run custom check if provided
                    if custom_check and not custom_check(
                        request.user, request, object_instance, *args, **kwargs
                    ):
                        message = error_message or _("Custom permission check failed")
                        return ResponsePresenter.forbidden_response(message)
                    return view_function(self, request, *args, **kwargs)

            # Admin strict mode check
            if PermissionConfigUtils.ADMIN_STRICT_MODE:
                message = error_message or _(
                    "Admin strict mode: Cannot access other users' data"
                )
                return ResponsePresenter.forbidden_response(message)

            # Staff bypass check - unless explicitly ignored
            if (
                not ignore_staff_bypass
                and PermissionConfigUtils.STAFF_BYPASS_ENABLED
                and request.user.is_staff
            ):
                # Run custom check if provided
                if custom_check and not custom_check(
                    request.user, request, object_instance, *args, **kwargs
                ):
                    message = error_message or _("Custom permission check failed")
                    return ResponsePresenter.forbidden_response(message)
                return view_function(self, request, *args, **kwargs)

            # Group-based permission check if allowed groups are specified
            if allowed_groups:
                # Convert single group to list for consistent processing
                if not isinstance(allowed_groups, list):
                    groups_to_check = [allowed_groups]
                else:
                    groups_to_check = allowed_groups

                user_group = getattr(request.user, "group", None)
                allowed_group_values = [group.value for group in groups_to_check]

                if user_group in allowed_group_values:
                    # Run custom check if provided
                    if custom_check and not custom_check(
                        request.user, request, object_instance, *args, **kwargs
                    ):
                        message = error_message or _("Custom permission check failed")
                        return ResponsePresenter.forbidden_response(message)
                    return view_function(self, request, *args, **kwargs)

            # All checks failed
            message = error_message or _(
                "You can only access your own data or need higher privileges"
            )
            return ResponsePresenter.forbidden_response(message)

        return wrapper

    return decorator


def admin_require_groups(allowed_groups, error_message=None):
    """
    Decorator to check group permissions for Django admin views.

    Args:
        allowed_groups: UserGroup enum or list of UserGroup enums
        error_message: Custom error message for permission denial

    Usage:
        @admin_require_groups(UserGroup.LABORATORY_HEAD)
        def change_view(self, request, object_id=None, form_url='', extra_context=None):
            return super().change_view(request, object_id, form_url, extra_context)

    Example:
        class MyModelAdmin(admin.ModelAdmin):
            @admin_require_groups([UserGroup.LABORATORY_HEAD], "Only lab head can modify")
            def change_view(self, request, object_id=None, form_url='', extra_context=None):
                return super().change_view(request, object_id, form_url, extra_context)
    """

    def decorator(view_function):
        @wraps(view_function)
        def wrapper(self, request, *args, **kwargs):
            if not has_group_permission(request.user, allowed_groups):
                message = error_message or _(
                    "Insufficient permissions for this admin action"
                )
                messages.error(request, message)
                raise PermissionDenied(message)
            return view_function(self, request, *args, **kwargs)

        return wrapper

    return decorator


def admin_require_owner_or_groups(allowed_groups=None, error_message=None):
    """
    Decorator to check owner OR group permissions for Django admin views.

    Args:
        allowed_groups: UserGroup enum or list of UserGroup enums (optional)
        error_message: Custom error message for permission denial

    Usage:
        @admin_require_owner_or_groups()  # Owner only
        @admin_require_owner_or_groups([UserGroup.LABORATORY_HEAD])  # Owner or lab head

    Example:
        class UserModelAdmin(admin.ModelAdmin):
            @admin_require_owner_or_groups([UserGroup.LABORATORY_HEAD])
            def change_view(self, request, object_id=None, form_url='', extra_context=None):
                return super().change_view(request, object_id, form_url, extra_context)
    """

    def decorator(view_function):
        @wraps(view_function)
        def wrapper(self, request, object_id=None, *args, **kwargs):
            if object_id:
                # Get object from model for permission check
                model_class = self.model
                try:
                    object_instance = model_class.objects.get(pk=object_id)
                    if not is_owner_or_has_permission(
                        request.user, object_instance, allowed_groups
                    ):
                        message = error_message or _(
                            "You can only modify your own data or need higher privileges"
                        )
                        messages.error(request, message)
                        raise PermissionDenied(message)
                except model_class.DoesNotExist:
                    # Object doesn't exist, let the view handle it
                    pass
            return view_function(self, request, object_id, *args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# CONVENIENCE DECORATORS FOR API VIEWS
# =============================================================================


def laboratory_head_only(view_function):
    """Laboratory Head only access (with bypass if enabled)"""
    return require_groups(
        UserGroup.LABORATORY_HEAD, _("Only Laboratory Head can access this resource")
    )(view_function)


def laboratory_technician_only(view_function):
    """Laboratory Technician only access (with bypass if enabled)"""
    return require_groups(
        UserGroup.LABORATORY_TECHNICIAN,
        _("Only Laboratory Technician can access this resource"),
    )(view_function)


def laboratory_assistant_only(view_function):
    """Laboratory Assistant only access (with bypass if enabled)"""
    return require_groups(
        UserGroup.LABORATORY_ASSISTANT,
        _("Only Laboratory Assistant can access this resource"),
    )(view_function)


def student_only(view_function):
    """Student only access (with bypass if enabled)"""
    return require_groups(
        UserGroup.STUDENT, _("Only Students can access this resource")
    )(view_function)


def lecturer_only(view_function):
    """Lecturer only access (with bypass if enabled)"""
    return require_groups(
        UserGroup.LECTURER, _("Only Lecturers can access this resource")
    )(view_function)


def laboratory_staff_only(view_function):
    """Laboratory staff only access: Head, Technician, Assistant (with bypass if enabled)"""
    allowed_groups = [
        UserGroup.LABORATORY_HEAD,
        UserGroup.LABORATORY_TECHNICIAN,
        UserGroup.LABORATORY_ASSISTANT,
    ]
    return require_groups(
        allowed_groups, _("Only laboratory staff can access this resource")
    )(view_function)


def teaching_staff_only(view_function):
    """Teaching staff only access: Head, Technician, Lecturer (with bypass if enabled)"""
    allowed_groups = [
        UserGroup.LABORATORY_HEAD,
        UserGroup.LABORATORY_TECHNICIAN,
    ]
    return require_groups(
        allowed_groups, _("Only teaching staff can access this resource")
    )(view_function)


def owner_only(view_function):
    """Owner only access - users can only access their own data"""
    return require_owner_or_groups(
        error_message=_("You can only access your own data")
    )(view_function)


def owner_or_laboratory_head(view_function):
    """Owner or Laboratory Head access"""
    return require_owner_or_groups(
        [UserGroup.LABORATORY_HEAD],
        _("Only data owner or Laboratory Head can access this resource"),
    )(view_function)


def owner_or_laboratory_staff(view_function):
    """Owner or laboratory staff access"""
    allowed_groups = [
        UserGroup.LABORATORY_HEAD,
        UserGroup.LABORATORY_TECHNICIAN,
        UserGroup.LABORATORY_ASSISTANT,
    ]
    return require_owner_or_groups(
        allowed_groups,
        _("Only data owner or laboratory staff can access this resource"),
    )(view_function)


def owner_or_teaching_staff(view_function):
    """Owner or teaching staff access"""
    allowed_groups = [
        UserGroup.LABORATORY_HEAD,
        UserGroup.LABORATORY_TECHNICIAN,
        UserGroup.LECTURER,
    ]
    return require_owner_or_groups(
        allowed_groups, _("Only data owner or teaching staff can access this resource")
    )(view_function)


# =============================================================================
# CONVENIENCE DECORATORS FOR DJANGO ADMIN
# =============================================================================


def admin_laboratory_head_only(view_function):
    """Admin: Laboratory Head only access"""
    return admin_require_groups(
        UserGroup.LABORATORY_HEAD,
        _("Only Laboratory Head can perform this admin action"),
    )(view_function)


def admin_laboratory_technician_only(view_function):
    """Admin: Laboratory Technician only access"""
    return admin_require_groups(
        UserGroup.LABORATORY_TECHNICIAN,
        _("Only Laboratory Technician can perform this admin action"),
    )(view_function)


def admin_laboratory_staff_only(view_function):
    """Admin: Laboratory staff only access"""
    allowed_groups = [
        UserGroup.LABORATORY_HEAD,
        UserGroup.LABORATORY_TECHNICIAN,
        UserGroup.LABORATORY_ASSISTANT,
    ]
    return admin_require_groups(
        allowed_groups, _("Only laboratory staff can perform this admin action")
    )(view_function)


def admin_laboratory_employee_only(view_function):
    """Admin: Laboratory employee only access"""
    allowed_groups = [
        UserGroup.LABORATORY_HEAD,
        UserGroup.LABORATORY_TECHNICIAN,
    ]
    return admin_require_groups(
        allowed_groups, _("Only laboratory employees can perform this admin action")
    )(view_function)


def admin_owner_only(view_function):
    """Admin: Owner only access"""
    return admin_require_owner_or_groups(
        error_message=_("You can only modify your own data in admin")
    )(view_function)


def admin_owner_or_laboratory_head(view_function):
    """Admin: Owner or Laboratory Head access"""
    return admin_require_owner_or_groups(
        [UserGroup.LABORATORY_HEAD],
        _("Only data owner or Laboratory Head can modify this data"),
    )(view_function)


def admin_owner_or_technician(view_function):
    """Admin: Owner or Laboratory Technician access"""
    return admin_require_owner_or_groups(
        [UserGroup.LABORATORY_TECHNICIAN],
        _("Only data owner or Laboratory Technician can modify this data"),
    )(view_function)


def admin_owner_or_laboratory_staff(view_function):
    """Admin: Owner or laboratory staff access"""
    allowed_groups = [
        UserGroup.LABORATORY_HEAD,
        UserGroup.LABORATORY_TECHNICIAN,
        UserGroup.LABORATORY_ASSISTANT,
    ]
    return admin_require_owner_or_groups(
        allowed_groups, _("Only data owner or laboratory staff can modify this data")
    )(view_function)


# =============================================================================
# PERMISSION CONFIGURATION UTILITIES
# =============================================================================


def enable_staff_bypass():
    """Enable staff bypass - staff can access all resources regardless of group"""
    PermissionConfigUtils.STAFF_BYPASS_ENABLED = True


def disable_staff_bypass():
    """Disable staff bypass - enforce strict group-based permissions"""
    PermissionConfigUtils.STAFF_BYPASS_ENABLED = False


def enable_admin_strict_mode():
    """Enable admin strict mode - admin cannot edit other users' data"""
    PermissionConfigUtils.ADMIN_STRICT_MODE = True


def disable_admin_strict_mode():
    """Disable admin strict mode - admin can edit all data"""
    PermissionConfigUtils.ADMIN_STRICT_MODE = False


def enable_owner_protection():
    """Enable owner protection - users can only access their own data"""
    PermissionConfigUtils.OWNER_PROTECTION_ENABLED = True


def disable_owner_protection():
    """Disable owner protection - remove ownership restrictions"""
    PermissionConfigUtils.OWNER_PROTECTION_ENABLED = False


def get_permission_status():
    """
    Get current permission configuration status.

    Returns:
        dict: Current permission configuration
    """
    return {
        "staff_bypass_enabled": PermissionConfigUtils.STAFF_BYPASS_ENABLED,
        "admin_strict_mode": PermissionConfigUtils.ADMIN_STRICT_MODE,
        "owner_protection_enabled": PermissionConfigUtils.OWNER_PROTECTION_ENABLED,
    }


def get_user_hierarchy_level(user):
    """
    Get user's hierarchy level based on their group.
    Lower number = higher authority.

    Args:
        user: Django user instance

    Returns:
        int: Hierarchy level (1=highest, 5=lowest)
    """
    if user.is_superuser:
        return 0  # Superuser is above all hierarchy

    user_group = getattr(user, "group", None)
    return PermissionConfigUtils.GROUP_HIERARCHY.get(
        user_group, 999
    )  # Default to lowest if group not found


def has_higher_or_equal_hierarchy(user, target_user):
    """
    Check if user has higher or equal hierarchy than target user.

    Args:
        user: Django user instance (who is checking)
        target_user: Django user instance (target to check against)

    Returns:
        bool: True if user has higher or equal hierarchy
    """
    user_level = get_user_hierarchy_level(user)
    target_level = get_user_hierarchy_level(target_user)

    return user_level <= target_level  # Lower number = higher hierarchy


def has_higher_hierarchy(user, target_user):
    """
    Check if user has strictly higher hierarchy than target user.

    Args:
        user: Django user instance (who is checking)
        target_user: Django user instance (target to check against)

    Returns:
        bool: True if user has higher hierarchy
    """
    user_level = get_user_hierarchy_level(user)
    target_level = get_user_hierarchy_level(target_user)

    return user_level < target_level  # Lower number = higher hierarchy


def can_manage_user(user, target_user):
    """
    Check if user can manage (edit/delete) target user based on hierarchy.
    Rules:
    - Superuser can manage anyone
    - Users can manage themselves
    - Higher hierarchy can manage lower hierarchy
    - Same hierarchy cannot manage each other (except self)

    Args:
        user: Django user instance (who wants to manage)
        target_user: Django user instance (target to be managed)

    Returns:
        bool: True if user can manage target user
    """
    # Superuser can manage anyone
    if user.is_superuser:
        return True

    # Users can manage themselves
    if user.pk == target_user.pk:
        return True

    # Check hierarchy
    return has_higher_hierarchy(user, target_user)


def get_manageable_users_queryset(user, queryset):
    """
    Filter queryset to only include users that the given user can manage.

    Args:
        user: Django user instance
        queryset: User queryset to filter

    Returns:
        QuerySet: Filtered queryset
    """
    if user.is_superuser:
        return queryset

    user_level = get_user_hierarchy_level(user)

    # User can see:
    # 1. Themselves
    # 2. Users with lower hierarchy (higher number)
    manageable_groups = [
        group
        for group, level in PermissionConfigUtils.GROUP_HIERARCHY.items()
        if level > user_level  # Higher number = lower hierarchy
    ]

    return queryset.filter(
        models.Q(pk=user.pk)  # Self
        | models.Q(group__in=manageable_groups)  # Lower hierarchy users
    )


# =============================================================================
# HIERARCHY-BASED DECORATORS FOR API VIEWS
# =============================================================================


def require_hierarchy_level(min_level, error_message=None):
    """
    Decorator to check minimum hierarchy level for API views.
    Lower number = higher authority.

    Args:
        min_level: Minimum hierarchy level required (1-5)
        error_message: Custom error message for permission denial

    Usage:
        @require_hierarchy_level(1)  # Only Laboratory Head
        @require_hierarchy_level(3)  # Assistant level or higher
    """

    def decorator(view_function):
        @wraps(view_function)
        def wrapper(self, request, *args, **kwargs):
            user_level = get_user_hierarchy_level(request.user)
            if user_level > min_level:  # Higher number = lower hierarchy
                message = error_message or _(
                    "Insufficient hierarchy level to access this resource"
                )
                return ResponsePresenter.forbidden_response(message)
            return view_function(self, request, *args, **kwargs)

        return wrapper

    return decorator


def require_can_manage_target_user(error_message=None):
    """
    Decorator to check if user can manage target user based on hierarchy.
    Expects the view to have get_object() method that returns a User instance.

    Args:
        error_message: Custom error message for permission denial

    Usage:
        @require_can_manage_target_user()
        def update_user(self, request):
            pass
    """

    def decorator(view_function):
        @wraps(view_function)
        def wrapper(self, request, *args, **kwargs):
            target_user = self.get_object()
            if not can_manage_user(request.user, target_user):
                message = error_message or _(
                    "You cannot manage this user due to hierarchy restrictions"
                )
                return ResponsePresenter.forbidden_response(message)
            return view_function(self, request, *args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# HIERARCHY-BASED DECORATORS FOR DJANGO ADMIN
# =============================================================================


def admin_require_hierarchy_level(min_level, error_message=None):
    """
    Decorator to check minimum hierarchy level for Django admin views.

    Args:
        min_level: Minimum hierarchy level required (1-5)
        error_message: Custom error message for permission denial
    """

    def decorator(view_function):
        @wraps(view_function)
        def wrapper(self, request, *args, **kwargs):
            user_level = get_user_hierarchy_level(request.user)
            if user_level > min_level:
                message = error_message or _(
                    "Insufficient hierarchy level for this admin action"
                )
                messages.error(request, message)
                raise PermissionDenied(message)
            return view_function(self, request, *args, **kwargs)

        return wrapper

    return decorator


def admin_require_can_manage_target_user(error_message=None):
    """
    Decorator to check if user can manage target user for Django admin views.

    Args:
        error_message: Custom error message for permission denial
    """

    def decorator(view_function):
        @wraps(view_function)
        def wrapper(self, request, object_id=None, *args, **kwargs):
            if object_id:
                model_class = self.model
                try:
                    target_user = model_class.objects.get(pk=object_id)
                    if not can_manage_user(request.user, target_user):
                        message = error_message or _(
                            "You cannot manage this user due to hierarchy restrictions"
                        )
                        messages.error(request, message)
                        raise PermissionDenied(message)
                except model_class.DoesNotExist:
                    pass
            return view_function(self, request, object_id, *args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# HIERARCHY-BASED CONVENIENCE DECORATORS
# =============================================================================


def lab_head_only(view_function):
    """Hierarchy Level 1: Laboratory Head only"""
    return require_hierarchy_level(
        1, _("Only Laboratory Head can access this resource")
    )(view_function)


def technician_or_higher(view_function):
    """Hierarchy Level 2: Laboratory Technician or higher"""
    return require_hierarchy_level(
        2, _("Only Laboratory Technician or higher can access this resource")
    )(view_function)


def assistant_or_higher(view_function):
    """Hierarchy Level 3: Laboratory Assistant or higher"""
    return require_hierarchy_level(
        3, _("Only Laboratory Assistant or higher can access this resource")
    )(view_function)


def student_or_higher(view_function):
    """Hierarchy Level 4: Student or higher"""
    return require_hierarchy_level(
        4, _("Only Student or higher can access this resource")
    )(view_function)


def lecturer_or_higher(view_function):
    """Hierarchy Level 5: All authenticated users (Lecturer is lowest)"""
    return require_hierarchy_level(
        5, _("Authentication required to access this resource")
    )(view_function)


# Admin versions
def admin_lab_head_only(view_function):
    """Admin: Hierarchy Level 1: Laboratory Head only"""
    return admin_require_hierarchy_level(
        1, _("Only Laboratory Head can perform this admin action")
    )(view_function)


def admin_technician_or_higher(view_function):
    """Admin: Hierarchy Level 2: Laboratory Technician or higher"""
    return admin_require_hierarchy_level(
        2, _("Only Laboratory Technician or higher can perform this admin action")
    )(view_function)


def admin_assistant_or_higher(view_function):
    """Admin: Hierarchy Level 3: Laboratory Assistant or higher"""
    return admin_require_hierarchy_level(
        3, _("Only Laboratory Assistant or higher can perform this admin action")
    )(view_function)


def admin_student_or_higher(view_function):
    """Admin: Hierarchy Level 4: Student or higher"""
    return admin_require_hierarchy_level(
        4, _("Only Student or higher can perform this admin action")
    )(view_function)


def admin_lecturer_or_higher(view_function):
    """Admin: Hierarchy Level 5: All authenticated users"""
    return admin_require_hierarchy_level(
        5, _("Authentication required for this admin action")
    )(view_function)
