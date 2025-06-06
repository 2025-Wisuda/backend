"""
Custom Django admin configuration for User Management section.

This module provides custom admin site configuration to group
User and Group models under a single "User Management" section.
"""

from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from ..models import CustomUserModel
from .group_admin import GroupAdmin, GroupProxy
from .user_admin import UserAdmin


class UserManagementAdminConfig:
    """Configuration class for User Management admin section."""

    @staticmethod
    def configure_admin():
        """
        Configure admin to display Users and Groups under same section.

        This method sets up the admin interface to group User and Group
        models under the "User Management" section for better organization.
        """
        try:
            admin.site.unregister(Group)
        except admin.sites.NotRegistered:
            pass

        try:
            admin.site.unregister(CustomUserModel)
        except admin.sites.NotRegistered:
            pass

        admin.site.register(CustomUserModel, UserAdmin)
        admin.site.register(GroupProxy, GroupAdmin)

    @staticmethod
    def get_app_list(request, app_label=None):
        """
        Custom app list to group User and Group models.

        This method customizes the admin app list to display
        Users and Groups under the same application section.
        """
        app_list = admin.site.get_app_list(request)

        for app in app_list:
            if app.get("app_label") == "custom_auth":
                for other_app in app_list:
                    if other_app.get("app_label") == "auth":
                        group_models = [
                            model
                            for model in other_app.get("models", [])
                            if "group" in model.get("object_name", "").lower()
                        ]
                        app["models"].extend(group_models)
                        break
                break

        return app_list


UserManagementAdminConfig.configure_admin()
