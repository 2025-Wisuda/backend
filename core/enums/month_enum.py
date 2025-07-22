"""
Month enumeration for consistent month choices across the application.

Provides standardized month choices that can be used in forms, filters,
and other components that need month selection functionality.
"""

from enum import Enum

from django.utils.translation import gettext_lazy as _


class Month(Enum):
    """Month enumeration with translated names."""

    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12

    @property
    def display_name(self):
        """Get translated month name."""
        month_names = {
            1: _("January"),
            2: _("February"),
            3: _("March"),
            4: _("April"),
            5: _("May"),
            6: _("June"),
            7: _("July"),
            8: _("August"),
            9: _("September"),
            10: _("October"),
            11: _("November"),
            12: _("December"),
        }
        return month_names[self.value]

    @property
    def number(self):
        """Get month number."""
        return self.value

    @classmethod
    def choices(cls, include_all=True):
        """
        Get month choices for forms.

        Args:
            include_all (bool): Whether to include "All Months" option

        Returns:
            List of tuples suitable for Django form choices
        """
        choices = []

        if include_all:
            choices.append(("", _("All Months")))

        choices.extend([(str(month.value), month.display_name) for month in cls])

        return choices

    @classmethod
    def get_month_name(cls, month_number):
        """
        Get month name by number.

        Args:
            month_number (int): Month number (1-12)

        Returns:
            str: Translated month name or None if invalid
        """
        for month in cls:
            if month.value == month_number:
                return str(month.display_name)
        return None

    @classmethod
    def get_month_by_number(cls, month_number):
        """
        Get Month enum by number.

        Args:
            month_number (int): Month number (1-12)

        Returns:
            Month: Month enum instance or None if invalid
        """
        for month in cls:
            if month.value == month_number:
                return month
        return None
