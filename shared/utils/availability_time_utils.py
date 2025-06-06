"""
Lab Schedule Availability Utilities

This module provides utility functions for calculating available time slots
in the laboratory scheduling system.

What: Availability calculation utilities with generator pattern
Why: Eliminates code duplication and provides memory-efficient slot generation
How: Use calculate_available_slots() generator for memory-efficient slot iteration
"""

from datetime import time
from typing import Generator, List, Tuple

from shared.constant import LabOperatingHoursConstant


def calculate_available_slots(
    occupied_slots: List[Tuple[time, time]]
) -> Generator[Tuple[time, time], None, None]:
    """
    Calculate available time slots using generator pattern.

    This generator yields available time slots between occupied periods,
    providing memory-efficient iteration over availability windows.

    Args:
        occupied_slots: List of tuples containing (start_time, end_time)
                       for occupied time periods

    Yields:
        Tuple[time, time]: Available time slot as (start_time, end_time)

    Example:
        occupied = [(time(9, 0), time(10, 0)), (time(14, 0), time(15, 0))]
        for start, end in calculate_available_slots(occupied):
            print(f"Available: {start} - {end}")

    Benefits:
        - Memory efficient for large datasets
        - Lazy evaluation
        - Can be consumed partially
        - Composable with other generators
    """
    lab_start = LabOperatingHoursConstant.START_TIME
    lab_end = LabOperatingHoursConstant.END_TIME

    # Sort occupied slots by start time
    sorted_slots = sorted(occupied_slots, key=lambda x: x[0])

    current_time = lab_start

    for start_time, end_time in sorted_slots:
        # If there's a gap before this occupied slot, yield it as available
        if current_time < start_time:
            yield (current_time, start_time)

        # Move current time to after this occupied slot
        # Allow overlap at exact end/start times (10:00 end, 10:00 start is OK)
        current_time = max(current_time, end_time)

    # Add remaining time after last occupied slot until lab closing
    if current_time < lab_end:
        yield (current_time, lab_end)


def format_available_slots_for_api(
    occupied_slots: List[Tuple[time, time]]
) -> List[dict]:
    """
    Format available slots for API response.

    Convenience function that uses the generator to create a formatted
    list suitable for API responses.

    Args:
        occupied_slots: List of tuples containing (start_time, end_time)

    Returns:
        List[dict]: Formatted available slots with string time representations

    Example:
        occupied = [(time(9, 0), time(10, 0))]
        result = format_available_slots_for_api(occupied)
        # Returns: [{"start_time": "07:30", "end_time": "09:00"}, ...]
    """
    return [
        {
            "start_time": start_time.strftime("%H:%M"),
            "end_time": end_time.strftime("%H:%M"),
        }
        for start_time, end_time in calculate_available_slots(occupied_slots)
    ]
