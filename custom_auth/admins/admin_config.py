"""
Admin Configuration

Central configuration for custom authentication admin interface.
Handles admin site registration and app list customization for user management.
"""

from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from ..models import CustomUserModel
from .group_admin import GroupAdmin, GroupProxy
from .user_admin import UserAdmin


class UserManagementAdminConfig:
    """
    Configuration class for user management admin interface.

    Responsibilities:
    - Register custom admin classes
    - Configure admin site layout
    - Manage app list organization for better UX
    """

    @staticmethod
    def configure_admin():
        """
        Register custom admin classes with enhanced functionality.

        Safely unregisters existing models and registers custom implementations
        with enhanced features like export, audit trails, and role-based access.
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
        Customize admin app list for better organization.

        Consolidates Group management under custom_auth app
        to provide unified user management interface.
        """
        app_list = admin.site.get_app_list(request)

        # Move Group models from 'auth' app to 'custom_auth' app for better organization
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
