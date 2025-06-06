"""
Laboratory Operating Hours Constants

This module defines the standard operating hours for laboratory facilities
within the Teaching Assistant Laboratory Management System.

What: Laboratory working hour time constants
Why: Standardizes lab scheduling across the application and provides
     centralized configuration for time-based business rules
How: Import and use time constants for scheduling validation and UI display
"""

from datetime import time


class LabOperatingHoursConstant:
    """
    Laboratory operating hours configuration.

    Defines the standard daily operating hours for laboratory facilities.
    Used for scheduling validation, UI display, and business rule enforcement.

    What: Standard lab operating time boundaries
    Why: Ensures consistent scheduling rules and prevents bookings outside operating hours
    How: Use START_TIME and END_TIME for time range validation

    Constants:
        START_TIME (time): Laboratory opening time (7:30 AM)
        END_TIME (time): Laboratory closing time (6:00 PM)

    Example:
        # Validate if a booking time is within operating hours
        booking_time = time(14, 30)  # 2:30 PM
        if (LabOperatingHoursConstant.START_TIME <= booking_time <=
            LabOperatingHoursConstant.END_TIME):
            print("Booking time is valid")
    """

    START_TIME = time(7, 30)  # 7:30 AM - Laboratory opening time
    END_TIME = time(18, 0)  # 6:00 PM - Laboratory closing time
