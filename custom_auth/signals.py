"""Django signals for automatic group initialization and permission assignment."""

import logging

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from core.enums import UserGroup

logger = logging.getLogger(__name__)

# Permission mapping for groups - using enum to avoid typos
GROUP_PERMISSIONS = {
    UserGroup.LABORATORY_HEAD: {
        "custom_auth.customusermodel": ["add", "view", "change"],
        "lab_schedule.labschedulemodel": ["add", "view", "change"],
        "lab_allocation.laballocationmodel": ["add", "view", "change"],
    },
    UserGroup.LABORATORY_TECHNICIAN: {
        "custom_auth.customusermodel": ["add", "view", "change"],
        "lab_schedule.labschedulemodel": ["add", "view", "change"],
        "lab_allocation.laballocationmodel": ["add", "view", "change"],
    },
    UserGroup.LABORATORY_ASSISTANT: {
        "custom_auth.customusermodel": ["add", "view", "change"],
        "lab_schedule.labschedulemodel": ["add", "view", "change"],
        "lab_allocation.laballocationmodel": ["add", "view", "change"],
    },
    UserGroup.LECTURER: {
        "custom_auth.customusermodel": [],
        "lab_schedule.labschedulemodel": [],
        "lab_allocation.laballocationmodel": [],
    },
    UserGroup.STUDENT: {
        "custom_auth.customusermodel": [],
        "lab_schedule.labschedulemodel": [],
        "lab_allocation.laballocationmodel": [],
    },
}


def assign_permissions_to_group(group_obj, permissions_config):
    """
    Assign permissions to a Django Group based on configuration.

    Args:
        group_obj (Group): Django Group object
        permissions_config (dict): Dictionary mapping app.model to permission list

    Returns:
        int: Number of permissions assigned
    """
    permissions_assigned = 0

    # Clear existing permissions
    group_obj.permissions.clear()

    for model_path, perms in permissions_config.items():
        try:
            app_label, model_name = model_path.split(".")
            content_type = ContentType.objects.get(
                app_label=app_label, model=model_name
            )

            for perm_code in perms:
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
    Create default user groups and assign permissions after migrations are applied.

    This handler ensures the required groups are present in the database
    and automatically assigns the correct permissions to each group.
    """
    if sender.name != "custom_auth":
        return

    try:
        with transaction.atomic():
            total_groups_created = 0
            total_permissions_assigned = 0

            for group_enum, permissions_config in GROUP_PERMISSIONS.items():
                group_name = group_enum.value  # Get the actual string value from enum

                # Create or get the group
                group_obj, created = Group.objects.get_or_create(name=group_name)
                if created:
                    total_groups_created += 1
                    logger.info(f'Group "{group_name}" created.')

                # Assign permissions to the group
                perms_assigned = assign_permissions_to_group(
                    group_obj, permissions_config
                )
                total_permissions_assigned += perms_assigned

                logger.info(
                    f'Group "{group_name}" configured with {perms_assigned} permissions.'
                )

            if total_groups_created > 0:
                logger.info(f"{total_groups_created} new groups created.")

            logger.info(
                f"Total {total_permissions_assigned} permissions assigned to groups."
            )
            logger.info("Group and permission setup completed successfully.")

    except Exception as e:
        logger.error(f"Error creating groups and permissions: {str(e)}")


# Legacy handler removed - functionality consolidated into create_default_groups_and_permissions
