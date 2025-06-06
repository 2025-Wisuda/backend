from enum import Enum

from django.utils.translation import gettext_lazy as _


class ApprovalStatus(str, Enum):
    """
    Enumeration of approval status values for laboratory scheduling system.
    Stored in Indonesian for DB consistency.

    Status Flow:
    PENDING -> APPROVED/REJECTED/CANCELLED
    APPROVED -> COMPLETED/EXPIRED/CANCELLED
    """

    PENDING = "Menunggu"
    APPROVED = "Disejutui"
    REJECTED = "Ditolak"
    CANCELLED = "Dibatalkan"
    COMPLETED = "Selesai"
    EXPIRED = "Kedaluwarsa"
    IN_PROGRESS = "Sedang Berlangsung"

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
            self.PENDING: _("Pending"),
            self.APPROVED: _("Approved"),
            self.REJECTED: _("Rejected"),
            self.CANCELLED: _("Cancelled"),
            self.COMPLETED: _("Completed"),
            self.EXPIRED: _("Expired"),
            self.IN_PROGRESS: _("In Progress"),
        }[self]

    @classmethod
    def active_statuses(cls):
        """
        Return statuses that are considered 'active' (not final states).
        """
        return [cls.PENDING, cls.APPROVED, cls.IN_PROGRESS]

    @classmethod
    def final_statuses(cls):
        """
        Return statuses that are final (no further changes expected).
        """
        return [cls.REJECTED, cls.CANCELLED, cls.COMPLETED, cls.EXPIRED]

    @classmethod
    def can_be_cancelled(cls):
        """
        Return statuses that can be cancelled by users.
        """
        return [cls.PENDING, cls.APPROVED]

    @classmethod
    def requires_approval(cls):
        """
        Return statuses that require approval action.
        """
        return [cls.PENDING]
