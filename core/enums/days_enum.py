"""
Enum for bulk schedule generation days selection.

Provides predefined day patterns for bulk schedule creation with internationalization support.
Stored in Indonesian for DB consistency.
"""

from enum import Enum

from django.utils.translation import gettext_lazy as _


class DaysEnum(str, Enum):
    """
    Enum for duty schedule days selection.

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
            self.MONDAY: _("Monday"),
            self.TUESDAY: _("Tuesday"),
            self.WEDNESDAY: _("Wednesday"),
            self.THURSDAY: _("Thursday"),
            self.FRIDAY: _("Friday"),
            self.SATURDAY: _("Saturday"),
            self.SUNDAY: _("Sunday"),
        }[self]
