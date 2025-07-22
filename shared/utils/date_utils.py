"""
Date and Time Utilities

Provides i18n-ready formatting for timestamps used in admin interfaces and exports.
All keys are in English for easy translation.
"""

from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def format_datetime_for_display(datetime_obj, include_time=True):
    """
    Format datetime for display in admin and exports.

    Args:
        datetime_obj: datetime object to format
        include_time: whether to include time in the format

    Returns:
        Formatted string ready for i18n
    """
    if not datetime_obj:
        return ""

    # Convert to local timezone
    local_time = timezone.localtime(datetime_obj)

    if include_time:
        # Format: "20 July 2025, 15:30" (ready for i18n)
        return local_time.strftime("%d %B %Y, %H:%M")
    else:
        # Format: "20 July 2025" (ready for i18n)
        return local_time.strftime("%d %B %Y")


def format_date_for_display(date_obj):
    """
    Format date for display in admin and exports.

    Args:
        date_obj: date object to format

    Returns:
        Formatted string ready for i18n
    """
    if not date_obj:
        return ""

    # Format: "20 July 2025" (ready for i18n)
    return date_obj.strftime("%d %B %Y")


def format_time_for_display(time_obj):
    """
    Format time for display in admin and exports.

    Args:
        time_obj: time object to format

    Returns:
        Formatted string ready for i18n
    """
    if not time_obj:
        return ""

    # Format: "15:30" (24-hour format)
    return time_obj.strftime("%H:%M")


def get_timestamp_field_headers():
    """
    Get i18n-ready field headers for timestamp fields.

    Returns:
        Dictionary of field names to display names
    """
    return {
        "created_at": _("Created At"),
        "updated_at": _("Updated At"),
        "date_joined": _("Date Joined"),
        "last_login": _("Last Login"),
        "start_date": _("Start Date"),
        "end_date": _("End Date"),
        "start_time": _("Start Time"),
        "end_time": _("End Time"),
    }


def get_timestamp_field_descriptions():
    """
    Get i18n-ready field descriptions for timestamp fields.

    Returns:
        Dictionary of field names to descriptions
    """
    return {
        "created_at": _("Date and time when this record was created"),
        "updated_at": _("Date and time when this record was last updated"),
        "date_joined": _("Date when the user joined the system"),
        "last_login": _("Date and time of the user's last login"),
        "start_date": _("Start date of the schedule or allocation"),
        "end_date": _("End date of the schedule or allocation"),
        "start_time": _("Start time of the schedule or allocation"),
        "end_time": _("End time of the schedule or allocation"),
    }
