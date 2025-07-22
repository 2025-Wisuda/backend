from enum import Enum

from django.utils.translation import gettext_lazy as _


class AttendanceStatus(str, Enum):
    """
    Enumeration of attendance status values for duty attendance tracking.
    Stored in Indonesian for DB consistency.

    Status Flow:
    SCHEDULED -> PRESENT/ABSENT/LATE/EARLY_OUT
    """

    SCHEDULED = "Belum Hadir"
    PRESENT = "Hadir"
    ABSENT = "Tidak Hadir"
    LATE = "Terlambat"
    EARLY_OUT = "Pulang Lebih Awal"
    EXCUSED = "Izin"
    SICK = "Sakit"

    @classmethod
    def choices(cls):
        """
        Return list of (value, label) tuples for Django model field choices.
        """
        return [(item.value, item.label()) for item in cls]

    def label(self):
        """
        Return human-readable label for the status.
        """
        labels = {
            self.SCHEDULED: _("Scheduled"),
            self.PRESENT: _("Present"),
            self.ABSENT: _("Absent"),
            self.LATE: _("Late"),
            self.EARLY_OUT: _("Early Out"),
            self.EXCUSED: _("Excused"),
            self.SICK: _("Sick"),
        }
        return labels.get(self, self.value)

    @classmethod
    def get_status_choices(cls):
        """
        Get simplified choices for common statuses.
        """
        return [
            (cls.PRESENT, cls.PRESENT.label()),
            (cls.ABSENT, cls.ABSENT.label()),
            (cls.LATE, cls.LATE.label()),
            (cls.EARLY_OUT, cls.EARLY_OUT.label()),
            (cls.EXCUSED, cls.EXCUSED.label()),
            (cls.SICK, cls.SICK.label()),
        ]

    @classmethod
    def get_completed_statuses(cls):
        """
        Get list of statuses that indicate attendance is completed.
        """
        return [cls.PRESENT, cls.ABSENT, cls.LATE, cls.EARLY_OUT, cls.EXCUSED, cls.SICK]

    @classmethod
    def get_present_statuses(cls):
        """
        Get list of statuses that indicate the person was present.
        """
        return [cls.PRESENT, cls.LATE, cls.EARLY_OUT]
