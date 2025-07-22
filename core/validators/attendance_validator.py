"""
Validators for duty attendance functionality.

This module provides reusable validators for attendance-related operations
including status validation, location validation, and security checks.
"""

from core.enums.attendance_status_enum import AttendanceStatus
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class AttendanceStatusValidator:
    """
    Validator for attendance status operations.

    Provides reusable validation methods for attendance status changes,
    transitions, and business rule enforcement.
    """

    # Configuration constants
    LATE_THRESHOLD_MINUTES = 15
    EARLY_OUT_THRESHOLD_MINUTES = 15

    @staticmethod
    def validate_status_value(status):
        """
        Validate if the provided status is a valid attendance status.

        Args:
            status: Status value to validate

        Raises:
            ValidationError: If status is invalid
        """
        valid_statuses = [s.value for s in AttendanceStatus]
        if status not in valid_statuses:
            raise ValidationError(
                _("Invalid attendance status '{}'. Valid options: {}").format(
                    status, ", ".join(valid_statuses)
                )
            )

    @staticmethod
    def validate_status_transition(current_status, new_status):
        """
        Validate if status transition is allowed based on business rules.

        Args:
            current_status: Current attendance status
            new_status: Proposed new status

        Raises:
            ValidationError: If transition is not allowed
        """
        # Define allowed transitions
        allowed_transitions = {
            AttendanceStatus.SCHEDULED.value: [
                AttendanceStatus.PRESENT.value,
                AttendanceStatus.LATE.value,
                AttendanceStatus.ABSENT.value,
                AttendanceStatus.EARLY_OUT.value,
            ],
            AttendanceStatus.PRESENT.value: [
                AttendanceStatus.EARLY_OUT.value,
                AttendanceStatus.LATE.value,
            ],
            AttendanceStatus.LATE.value: [
                AttendanceStatus.PRESENT.value,
                AttendanceStatus.EARLY_OUT.value,
            ],
            AttendanceStatus.EARLY_OUT.value: [
                AttendanceStatus.PRESENT.value,
                AttendanceStatus.LATE.value,
            ],
            AttendanceStatus.ABSENT.value: [
                AttendanceStatus.PRESENT.value,
                AttendanceStatus.LATE.value,
            ],
        }

        # Validate both statuses first
        AttendanceStatusValidator.validate_status_value(current_status)
        AttendanceStatusValidator.validate_status_value(new_status)

        # Check if transition is allowed
        if current_status == new_status:
            return  # Same status is always allowed

        if current_status not in allowed_transitions:
            raise ValidationError(
                _("Cannot transition from status '{}'").format(current_status)
            )

        if new_status not in allowed_transitions[current_status]:
            raise ValidationError(
                _("Invalid status transition from '{}' to '{}'").format(
                    current_status, new_status
                )
            )

    @staticmethod
    def validate_manual_override(status, user=None):
        """
        Validate manual status override operation.

        Args:
            status: Status to set manually
            user: User performing the override (optional)

        Raises:
            ValidationError: If override is not allowed
        """
        # Validate status value
        AttendanceStatusValidator.validate_status_value(status)

        # Check if user has permission (if user is provided)
        if user and not user.is_staff:
            # Additional permission checks can be added here
            # For now, only staff users can perform manual overrides
            raise ValidationError(
                _("Only staff users can perform manual attendance overrides")
            )

    @staticmethod
    def get_valid_statuses():
        """
        Get list of all valid attendance status values.

        Returns:
            list: List of valid status values
        """
        return [s.value for s in AttendanceStatus]

    @staticmethod
    def get_present_statuses():
        """
        Get list of status values that indicate presence.

        Returns:
            list: List of status values indicating presence
        """
        return [
            AttendanceStatus.PRESENT.value,
            AttendanceStatus.LATE.value,
            AttendanceStatus.EARLY_OUT.value,
        ]

    @staticmethod
    def get_completed_statuses():
        """
        Get list of status values that indicate completed attendance.

        Returns:
            list: List of status values indicating completion
        """
        return [
            AttendanceStatus.PRESENT.value,
            AttendanceStatus.LATE.value,
            AttendanceStatus.EARLY_OUT.value,
            AttendanceStatus.ABSENT.value,
        ]

    @staticmethod
    def validate_time_sequence(clock_in_time, clock_out_time):
        """
        Validate that clock out time is after clock in time.

        Args:
            clock_in_time: Clock in datetime
            clock_out_time: Clock out datetime

        Raises:
            ValidationError: If times are invalid
        """
        if clock_in_time and clock_out_time:
            if clock_out_time <= clock_in_time:
                raise ValidationError(_("Clock out time must be after clock in time."))

    @staticmethod
    def calculate_status(
        date,
        start_time,
        end_time,
        clock_in_time=None,
        clock_out_time=None,
    ):
        """
        Calculate attendance status based on times and thresholds.

        Args:
            date: Date of the duty
            start_time: Scheduled start time
            end_time: Scheduled end time
            clock_in_time: Actual clock in time (optional)
            clock_out_time: Actual clock out time (optional)

        Returns:
            str: Calculated attendance status
        """
        from datetime import datetime, timedelta

        from django.utils import timezone

        # If no clock in, check if duty date has passed
        if not clock_in_time:
            datetime = datetime.combine(date, end_time)
            if timezone.localtime() > timezone.make_aware(datetime):
                return AttendanceStatus.ABSENT.value
            return AttendanceStatus.SCHEDULED.value

        # Expected start and end times for the duty date
        expected_start = datetime.combine(date, start_time)
        expected_end = datetime.combine(date, end_time)

        # Convert to timezone-aware if needed
        if timezone.is_naive(expected_start):
            expected_start = timezone.make_aware(expected_start)
        if timezone.is_naive(expected_end):
            expected_end = timezone.make_aware(expected_end)

        # Check if clocked in late
        late_threshold = expected_start + timedelta(
            minutes=AttendanceStatusValidator.LATE_THRESHOLD_MINUTES
        )
        is_late = clock_in_time > late_threshold

        # Check early departure if clocked out
        is_early_out = False
        if clock_out_time:
            early_threshold = expected_end - timedelta(
                minutes=AttendanceStatusValidator.EARLY_OUT_THRESHOLD_MINUTES
            )
            is_early_out = clock_out_time < early_threshold

        # Determine status
        if is_late and is_early_out:
            return AttendanceStatus.LATE.value  # Prioritize late over early out
        elif is_late:
            return AttendanceStatus.LATE.value
        elif is_early_out:
            return AttendanceStatus.EARLY_OUT.value
        else:
            return AttendanceStatus.PRESENT.value

    @staticmethod
    def calculate_security_score(
        clock_in_time,
        clock_out_time,
        clock_in_location,
        clock_out_location,
        clock_in_method,
        clock_out_method,
    ):
        """
        Calculate security validation score (0-100) for attendance entries.

        Args:
            clock_in_time: Clock in datetime
            clock_out_time: Clock out datetime
            clock_in_location: Clock in location data
            clock_out_location: Clock out location data
            clock_in_method: Clock in method
            clock_out_method: Clock out method

        Returns:
            int: Security score (0-100)
        """
        from core.enums.clock_method_enum import ClockMethod

        score = 0
        checks = 0

        # Clock in security checks
        if clock_in_time:
            checks += 2
            # Location verification check
            if clock_in_location and clock_in_location.get("verified"):
                score += 50
            # Method verification
            if clock_in_method == ClockMethod.MANUAL.value:
                score += 50

        # Clock out security checks (if clocked out)
        if clock_out_time:
            checks += 2
            # Location verification check
            if clock_out_location and clock_out_location.get("verified"):
                score += 50
            # Method verification
            if clock_out_method == ClockMethod.MANUAL.value:
                score += 50

        # Calculate final score
        if checks == 2:  # Only clock in
            return min(score, 100)
        elif checks == 4:  # Both clock in and out
            return score // 2  # Average of both
        else:
            return 0  # No data

    @staticmethod
    def validate_clock_in_preconditions(clock_in_time):
        """
        Validate preconditions for clock in operation.

        Args:
            clock_in_time: Current clock in time

        Raises:
            ValidationError: If preconditions are not met
        """
        if clock_in_time:
            raise ValidationError(_("Assistant has already clocked in for this duty."))

    @staticmethod
    def validate_clock_out_preconditions(clock_in_time, clock_out_time):
        """
        Validate preconditions for clock out operation.

        Args:
            clock_in_time: Current clock in time
            clock_out_time: Current clock out time

        Raises:
            ValidationError: If preconditions are not met
        """
        if not clock_in_time:
            raise ValidationError(_("Assistant must clock in before clocking out."))

        if clock_out_time:
            raise ValidationError(_("Assistant has already clocked out for this duty."))


class AttendanceLocationValidator:
    """
    Validator for attendance location operations.

    Provides validation for location data used in attendance tracking.
    """

    # UNILA Lab coordinates
    UNILA_LAB_LATITUDE = -5.3620393213
    UNILA_LAB_LONGITUDE = 105.240057347
    LOCATION_TOLERANCE = 0.001  # ~100 meters

    @staticmethod
    def validate_location_data(location_data):
        """
        Validate location data structure and content.

        Args:
            location_data: Dictionary containing location information

        Raises:
            ValidationError: If location data is invalid
        """
        if not isinstance(location_data, dict):
            raise ValidationError(_("Location data must be a dictionary"))

        required_fields = ["latitude", "longitude"]
        for field in required_fields:
            if field not in location_data:
                raise ValidationError(
                    _("Location data must contain '{}'").format(field)
                )

        # Validate coordinate values
        try:
            lat = float(location_data["latitude"])
            lng = float(location_data["longitude"])
        except (ValueError, TypeError):
            raise ValidationError(_("Latitude and longitude must be valid numbers"))

        # Validate coordinate ranges
        if not (-90 <= lat <= 90):
            raise ValidationError(_("Latitude must be between -90 and 90"))

        if not (-180 <= lng <= 180):
            raise ValidationError(_("Longitude must be between -180 and 180"))

    @staticmethod
    def validate_unila_location(location_data):
        """
        Validate if location is within UNILA lab area.

        Args:
            location_data: Dictionary containing location information

        Returns:
            bool: True if location is valid for UNILA lab

        Raises:
            ValidationError: If location is invalid
        """
        # First validate the data structure
        AttendanceLocationValidator.validate_location_data(location_data)

        lat = float(location_data["latitude"])
        lng = float(location_data["longitude"])

        # Check if within tolerance of UNILA lab coordinates
        lat_diff = abs(lat - AttendanceLocationValidator.UNILA_LAB_LATITUDE)
        lng_diff = abs(lng - AttendanceLocationValidator.UNILA_LAB_LONGITUDE)

        if (
            lat_diff <= AttendanceLocationValidator.LOCATION_TOLERANCE
            and lng_diff <= AttendanceLocationValidator.LOCATION_TOLERANCE
        ):
            return True

        raise ValidationError(
            _(
                "Location must be within UNILA laboratory area. "
                "Current location: ({}, {}), Expected: ({}, {})"
            ).format(
                lat,
                lng,
                AttendanceLocationValidator.UNILA_LAB_LATITUDE,
                AttendanceLocationValidator.UNILA_LAB_LONGITUDE,
            )
        )
