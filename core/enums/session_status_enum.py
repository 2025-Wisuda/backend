from enum import Enum

from django.utils.translation import gettext_lazy as _


class SessionStatus(str, Enum):
    """
    Enumeration of course session status values for laboratory scheduling system.
    Stored in Indonesian for DB consistency.

    Status Flow:
    SCHEDULED -> COMPLETED/CANCELLED
    CANCELLED -> SCHEDULED (reschedule)
    """

    SCHEDULED = "Terjadwal"
    COMPLETED = "Selesai"
    CANCELLED = "Dibatalkan"

    @classmethod
    def choices(cls):
        """
        Return list of (value, label) tuples for Django model field choices.
        """
        return [(item.value, item.label()) for item in cls]

    def label(self):
        """
        Return human-readable label for each status.
        """
        return {
            self.SCHEDULED: _("Scheduled"),
            self.COMPLETED: _("Completed"),
            self.CANCELLED: _("Cancelled"),
        }[self]

    @classmethod
    def active_statuses(cls):
        """Return statuses considered as active sessions."""
        return [cls.SCHEDULED]

    @classmethod
    def inactive_statuses(cls):
        """Return statuses considered as inactive sessions."""
        return [cls.COMPLETED, cls.CANCELLED]

    def is_active(self):
        """Check if this status represents an active session."""
        return self in self.active_statuses()

    def is_inactive(self):
        """Check if this status represents an inactive session."""
        return self in self.inactive_statuses()

    def can_transition_to(self, new_status):
        """
        Validate status transitions based on business rules.

        Args:
            new_status: SessionStatus enum value

        Returns:
            bool: True if transition is allowed
        """
        valid_transitions = {
            self.SCHEDULED: [self.COMPLETED, self.CANCELLED],
            self.COMPLETED: [],  # Final state
            self.CANCELLED: [self.SCHEDULED],  # Can reschedule
        }

        return new_status in valid_transitions.get(self, [])
