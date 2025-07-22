"""
Custom Auth Signals

Django signals for automatic group and permission management.
Ensures role-based access control is properly initialized after migrations.

Critical for laboratory management system security - creates groups and assigns
permissions based on user roles defined in UserGroup enum.
"""

import logging

from core.enums import UserGroup
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.signals import post_migrate
from django.dispatch import receiver

logger = logging.getLogger(__name__)

# Permission mapping for laboratory roles
# Defines CRUD permissions for each user group across system models
GROUP_PERMISSIONS = {
    # All permissions now handled by admin override
    # No database permissions needed - using enum approach
}


def assign_permissions_to_group(group_obj, permissions_config):
    """
    Assign permissions to a Django Group based on configuration.

    Args:
        group_obj: Django Group instance
        permissions_config: Dict mapping model paths to permission codes

    Returns:
        int: Number of permissions successfully assigned

    Security Note: Clears existing permissions before assignment to ensure clean state
    """
    permissions_assigned = 0
    group_obj.permissions.clear()  # Clean slate for permission assignment

    for model_path, perms in permissions_config.items():
        try:
            app_label, model_name = model_path.split(".")
            content_type = ContentType.objects.get(
                app_label=app_label, model=model_name
            )

            for perm_code in perms:
                # Django permission naming convention: {action}_{model}
                permission_codename = f"{perm_code}_{content_type.model}"
                try:
                    permission = Permission.objects.get(
                        content_type=content_type, codename=permission_codename
                    )
                    group_obj.permissions.add(permission)
                    permissions_assigned += 1
                    logger.debug(
                        f"Added permission {permission_codename} to group {group_obj.name}"
                    )
                except Permission.DoesNotExist:
                    logger.warning(
                        f"Permission {permission_codename} not found for {model_path}"
                    )

        except (ValueError, ContentType.DoesNotExist) as e:
            logger.warning(f"Error processing model {model_path}: {e}")

    return permissions_assigned


@receiver(post_migrate)
def create_default_groups_and_permissions(sender, **kwargs):
    """
    Signal handler to create groups and assign permissions after migration.

    Triggered after each migration run to ensure groups and permissions
    are properly configured for role-based access control.

    Security Critical: Only runs for custom_auth app to prevent interference
    with other apps' permission systems.
    """
    # Only process when custom_auth app migrations complete
    if sender.name != "custom_auth":
        return

    try:
        with transaction.atomic():  # Ensure all-or-nothing group creation
            total_groups_created = 0
            total_permissions_assigned = 0

            for group_enum, permissions_config in GROUP_PERMISSIONS.items():
                group_name = group_enum.value

                # Create group if it doesn't exist
                group_obj, created = Group.objects.get_or_create(name=group_name)
                if created:
                    total_groups_created += 1
                    logger.info(f'Group "{group_name}" created.')

                # Assign permissions to group (overwrites existing)
                perms_assigned = assign_permissions_to_group(
                    group_obj, permissions_config
                )
                total_permissions_assigned += perms_assigned

                logger.info(
                    f'Group "{group_name}" configured with {perms_assigned} permissions.'
                )

            # Summary logging for deployment tracking
            if total_groups_created > 0:
                logger.info(f"{total_groups_created} new groups created.")

            logger.info(
                f"Total {total_permissions_assigned} permissions assigned to groups."
            )
            logger.info("Group and permission setup completed successfully.")

    except Exception as e:
        logger.error(f"Error creating groups and permissions: {str(e)}")
