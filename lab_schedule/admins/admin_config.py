"""
Admin interface organization - groups Lab Schedule, Lab Allocation, and Room Booking models under unified section.

Consolidates lab schedule management into single admin section for better UX.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class LabScheduleManagementAdminConfig:
    """Unified admin section configuration for lab schedule management."""

    @staticmethod
    def configure_admin():
        """Override admin site's get_app_list method to customize app grouping."""
        # Store original get_app_list method
        original_get_app_list = admin.site.get_app_list

        def custom_get_app_list(request, app_label=None):
            """Merge Lab Allocation and Room Booking models into lab_schedule app for unified view."""
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

                # Remove original app entries to avoid duplication
                app_list = [
                    app
                    for app in app_list
                    if app.get("app_label") not in ["lab_allocation", "room_booking"]
                ]

            return app_list

        # Override the admin site's get_app_list method
        admin.site.get_app_list = custom_get_app_list


LabScheduleManagementAdminConfig.configure_admin()
