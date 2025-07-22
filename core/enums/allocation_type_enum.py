"""
Enum for lab allocation types.

Provides predefined allocation types for technician lab management with internationalization support.
Stored in Indonesian for DB consistency.
"""

from enum import Enum

from django.utils.translation import gettext_lazy as _


class AllocationType(str, Enum):
    """
    Enum for lab allocation types.

    Values are stored in Indonesian for DB consistency.
    Used for technician-managed lab allocations.
    """

    REGULAR_CLASS = "Kelas Reguler"
    MAINTENANCE = "Pemeliharaan"
    EQUIPMENT_SETUP = "Persiapan Alat"
    OTHER = "Lainnya"

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
            self.REGULAR_CLASS: _("Regular Class"),
            self.MAINTENANCE: _("Maintenance"),
            self.EQUIPMENT_SETUP: _("Equipment Setup"),
            self.OTHER: _("Other"),
        }[self]
