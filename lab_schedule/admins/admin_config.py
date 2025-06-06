"""
Custom Django admin configuration for Lab Schedule Management section.

This module provides custom admin site configuration to group
LabSchedule, LabAllocation, and RoomBooking models under a single section.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class LabScheduleManagementAdminConfig:
    """Configuration class for Lab Schedule Management admin section."""

    @staticmethod
    def configure_admin():
        """
        Configure admin to group LabSchedule, LabAllocation, and RoomBooking models.

        Override the admin site's get_app_list method to customize app grouping.
        """
        # Store original get_app_list method
        original_get_app_list = admin.site.get_app_list

        def custom_get_app_list(request, app_label=None):
            """Custom app list that groups related lab scheduling models."""
            app_list = original_get_app_list(request, app_label)

            lab_schedule_app = None
            lab_allocation_app = None
            room_booking_app = None

            for app in app_list:
                if app.get("app_label") == "lab_schedule":
                    lab_schedule_app = app
                elif app.get("app_label") == "lab_allocation":
                    lab_allocation_app = app
                elif app.get("app_label") == "room_booking":
                    room_booking_app = app

            if lab_schedule_app:
                # Merge LabAllocation models
                if lab_allocation_app:
                    lab_schedule_app["models"].extend(
                        lab_allocation_app.get("models", [])
                    )

                # Merge RoomBooking models
                if room_booking_app:
                    lab_schedule_app["models"].extend(
                        room_booking_app.get("models", [])
                    )

                # Update app display name
                lab_schedule_app["name"] = _("Lab Schedule Management")

                # Remove original app entries
                app_list = [
                    app
                    for app in app_list
                    if app.get("app_label") not in ["lab_allocation", "room_booking"]
                ]

            return app_list

        # Override the admin site's get_app_list method
        admin.site.get_app_list = custom_get_app_list


# Apply admin grouping configuration
LabScheduleManagementAdminConfig.configure_admin()
