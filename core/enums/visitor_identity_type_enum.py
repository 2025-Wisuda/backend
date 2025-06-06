"""
Visitor Identity Type Enumeration for Guest Visit System.

This enum defines the types of identity that can be used for visitor identification,
following the same pattern as UserGroup enum for consistency.
"""

from enum import Enum

from django.utils.translation import gettext_lazy as _


class VisitorIdentityType(str, Enum):
    """
    Enumeration of visitor identity types.
    Stores identity types in Indonesian for consistent DB storage.
    """

    STUDENT_NUMBER = "Nomor Mahasiswa"
    EMPLOYEE_NUMBER = "Nomor Pegawai"

    @classmethod
    def choices(cls):
        """
        Return list of (value, label) tuples for Django model field choices.
        Both are Indonesian strings stored in the database.
        """
        return [(item.value, item.value) for item in cls]

    def display_label(self):
        """
        Return translated label for display in admin or API according to current language.
        """
        return _(self.value)
