"""
Enum for clock in/out methods in attendance tracking.

This enum defines the available methods for clocking in and out,
supporting both manual entry and face recognition with manual as default.
"""

from enum import Enum


class ClockMethod(Enum):
    """
    Clock in/out method options.

    Values:
    - MANUAL: Manual clock in/out without biometric verification
    - FACE_RECOGNITION: Clock in/out using face recognition technology
    """

    MANUAL = "Manual"
    FACE_RECOGNITION = "Face Recognition"

    @classmethod
    def choices(cls):
        """Return Django model field choices."""
        return [
            (method.value, method.value.replace("_", " ").title()) for method in cls
        ]

    @classmethod
    def default(cls):
        """Return default clock method."""
        return cls.MANUAL.value
