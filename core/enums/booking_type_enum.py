"""
Enum for room booking types.

Provides booking type categorization based on user roles and requirements.
Different user groups can create different types of bookings with varying field requirements.
"""

from enum import Enum

from django.utils.translation import gettext_lazy as _


class BookingType(str, Enum):
    """
    Enumeration of room booking types based on user roles and purposes.

    Different booking types have different requirements:
    - SEMINAR: Full academic details required (for students/assistants)
    - CLASS: Course-related booking (for staff/faculty)
    """

    SEMINAR = "Seminar"
    CLASS = "Kelas Reguler"

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
            self.SEMINAR: _("Seminar"),
            self.CLASS: _("Regular Class"),
        }[self]

    @classmethod
    def student_allowed_types(cls):
        """
        Return booking types allowed for students and assistants.
        Students/assistants can only book for seminars which require full academic details.
        """
        return [cls.SEMINAR.value]

    @classmethod
    def staff_allowed_types(cls):
        """
        Return booking types allowed for staff and faculty.
        Staff can book for any purpose.
        """
        return [item.value for item in cls]

    @classmethod
    def requires_academic_details(cls, booking_type):
        """
        Check if a booking type requires full academic details.
        Only seminar bookings require supervisors, examiners, research title.
        """
        return booking_type == cls.SEMINAR.value

    def is_student_only_type(self):
        """
        Check if this booking type is restricted to students/assistants only.
        """
        return self.value in self.student_allowed_types()
