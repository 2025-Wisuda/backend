"""
Enum for bulk schedule generation days selection.

Provides predefined day patterns for bulk schedule creation with internationalization support.
Stored in Indonesian for DB consistency.
"""

from enum import Enum

from django.utils.translation import gettext_lazy as _


class BulkDays(str, Enum):
    """
    Enum for bulk schedule generation day patterns.

    Values are stored as day names in Indonesian for DB consistency.
    """

    # Individual weekdays
    MONDAY = "Senin"
    TUESDAY = "Selasa"
    WEDNESDAY = "Rabu"
    THURSDAY = "Kamis"
    FRIDAY = "Jumat"
    SATURDAY = "Sabtu"
    SUNDAY = "Minggu"

    # Common patterns
    WEEKDAYS = "Senin,Selasa,Rabu,Kamis,Jumat"
    WEEKEND = "Sabtu,Minggu"
    ALL_DAYS = "Senin,Selasa,Rabu,Kamis,Jumat,Sabtu,Minggu"

    # Common academic patterns
    MON_WED_FRI = "Senin,Rabu,Jumat"
    TUE_THU = "Selasa,Kamis"
    MON_WED = "Senin,Rabu"
    WED_FRI = "Rabu,Jumat"

    @classmethod
    def choices(cls):
        """
        Return list of (value, label) tuples for Django model field choices.
        """
        return [(item.value, item.label()) for item in cls]

    def label(self):
        """
        Return translated label for display purposes.
        """
        return {
            self.MONDAY: _("Monday Only"),
            self.TUESDAY: _("Tuesday Only"),
            self.WEDNESDAY: _("Wednesday Only"),
            self.THURSDAY: _("Thursday Only"),
            self.FRIDAY: _("Friday Only"),
            self.SATURDAY: _("Saturday Only"),
            self.SUNDAY: _("Sunday Only"),
            self.WEEKDAYS: _("Weekdays (Mon-Fri)"),
            self.WEEKEND: _("Weekend (Sat-Sun)"),
            self.ALL_DAYS: _("All Days (Mon-Sun)"),
            self.MON_WED_FRI: _("Mon, Wed, Fri"),
            self.TUE_THU: _("Tue, Thu"),
            self.MON_WED: _("Mon, Wed"),
            self.WED_FRI: _("Wed, Fri"),
        }[self]

    @classmethod
    def get_weekday_numbers(cls, days_pattern):
        """
        Convert days pattern to list of weekday numbers (0=Monday, 6=Sunday).

        Args:
            days_pattern (str): Comma-separated Indonesian day names

        Returns:
            list: List of weekday numbers
        """
        # Mapping Indonesian day names to weekday numbers
        day_to_weekday = {
            "Senin": 0,  # Monday
            "Selasa": 1,  # Tuesday
            "Rabu": 2,  # Wednesday
            "Kamis": 3,  # Thursday
            "Jumat": 4,  # Friday
            "Sabtu": 5,  # Saturday
            "Minggu": 6,  # Sunday
        }

        if not days_pattern:
            return []

        # Split comma-separated days and convert to weekday numbers
        day_names = [day.strip() for day in days_pattern.split(",")]
        weekday_numbers = []

        for day_name in day_names:
            if day_name in day_to_weekday:
                weekday_numbers.append(day_to_weekday[day_name])

        return sorted(weekday_numbers)

    @classmethod
    def get_individual_days(cls, days_pattern):
        """
        Get list of individual day names from a pattern.

        Args:
            days_pattern (str): Comma-separated Indonesian day names

        Returns:
            list: List of individual day names
        """
        if not days_pattern:
            return []

        return [day.strip() for day in days_pattern.split(",")]
