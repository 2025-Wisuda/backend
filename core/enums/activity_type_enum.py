from enum import Enum

from django.utils.translation import gettext_lazy as _


class ActivityType(str, Enum):
    """
    Enumeration of lab activity types.
    Stored in Indonesian for DB consistency.
    """

    PRACTICUM = "Praktikum"
    PROPOSAL_SEMINAR = "Seminar Proposal"
    RESULT_SEMINAR = "Seminar Hasil"
    INTERNSHIP_SEMINAR = "Seminar KP"
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
            self.PRACTICUM: _("Practicum"),
            self.PROPOSAL_SEMINAR: _("Proposal Seminar"),
            self.RESULT_SEMINAR: _("Result Seminar"),
            self.INTERNSHIP_SEMINAR: _("Internship Seminar"),
            self.OTHER: _("Other"),
        }[self]
