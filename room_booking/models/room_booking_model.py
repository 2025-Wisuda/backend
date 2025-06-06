"""
Room Booking Model for General Lab Room Booking System

This model handles room booking requests from all user types (students, assistants, staff, faculty)
with conditional field requirements based on user roles and booking types.

Features:
- User relationship instead of student-specific fields
- Conditional required fields based on user role and booking type
- Academic details required only for seminar bookings by students/assistants
- Staff/faculty can create simple bookings with minimal requirements
- Approval workflow with different rules for different user roles
- Document proof upload capability
- Integration with LabSchedule aggregator for conflict detection
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core import (
    ActivityType,
    ApprovalMixin,
    ApprovalStatus,
    BaseModel,
    BookingType,
    LabScheduleMixin,
    UserGroup,
)


class RoomBookingModel(BaseModel, ApprovalMixin, LabScheduleMixin):
    """
    Model for room booking requests from all user types.

    This model stores comprehensive information about room bookings with
    conditional field requirements based on user roles:

    User Relationship:
        - booker: ForeignKey to User who created the booking
        - Replaces student_name/student_npm with proper user relationship

    Booking Types & Requirements:
        - SEMINAR (students/assistants): Full academic details required
        - GENERAL/COURSE/MEETING/EVENT (staff/faculty): Basic info only        Conditional Field Logic:
        Students/Assistants + SEMINAR booking:
            - research_title: REQUIRED
            - seminar_type: REQUIRED
            - supervisor_main: REQUIRED
            - examiner: REQUIRED
            - supervisor_secondary: OPTIONAL

        Staff/Faculty + any booking type:
            - purpose: OPTIONAL
            - All academic fields: OPTIONAL/IGNORED

    Schedule fields (from LabScheduleMixin):
        - booking_date: Date the room is booked
        - booking_start_time: Starting time of the booking
        - booking_end_time: Ending time of the booking

    Approval fields (from ApprovalMixin):
        - booking_approval_status: Status of booking (PENDING, APPROVED, REJECTED)
        - approved_by_user: Reference to user who approved the booking
        - approval_timestamp: Timestamp when it was approved
    """

    # Override field mappings to use custom field names for scheduling
    SCHEDULE_DATE_FIELD = "booking_date"
    START_TIME_FIELD = "booking_start_time"
    END_TIME_FIELD = "booking_end_time"

    # Override field mappings for ApprovalMixin
    APPROVAL_STATUS_FIELD = "booking_approval_status"
    APPROVED_BY_FIELD = "approved_by_user"
    APPROVAL_TIMESTAMP_FIELD = "approval_timestamp"
    APPROVAL_NOTES_FIELD = "approval_notes"

    # Custom schedule fields with room booking context
    booking_date = models.DateField(
        db_index=True,
        verbose_name=_("Booking Date"),
        help_text=_("Date when the room is booked"),
    )
    booking_start_time = models.TimeField(
        verbose_name=_("Booking Start Time"),
        help_text=_("Start time of the room booking"),
    )
    booking_end_time = models.TimeField(
        verbose_name=_("Booking End Time"),
        help_text=_("End time of the room booking"),
    )

    # Custom approval fields for room booking context
    booking_approval_status = models.CharField(
        max_length=20,
        db_index=True,
        choices=ApprovalStatus.choices(),
        default=ApprovalStatus.PENDING.value,
        verbose_name=_("Booking Approval Status"),
        help_text=_("Current approval status of the room booking"),
    )
    approved_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_room_bookings",
        verbose_name=_("Approved By User"),
        help_text=_("User who approved or rejected this booking"),
    )
    approval_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Approval Timestamp"),
        help_text=_("Timestamp when the booking was approved or rejected"),
    )
    approval_notes = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Approval Notes"),
        help_text=_("Notes from approver/rejector explaining the decision"),
    )

    # User and booking information
    booker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="room_bookings",
        verbose_name=_("Booker"),
        help_text=_("User who created this room booking"),
        db_index=True,
    )

    booking_type = models.CharField(
        max_length=20,
        choices=BookingType.choices(),
        verbose_name=_("Booking Type"),
        help_text=_("Type of booking - determines required fields"),
        db_index=True,
    )

    # Purpose field - optional for all booking types
    purpose = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Purpose"),
        help_text=_("Purpose or reason for booking the room (optional)"),
    )

    # Academic fields - required only for student seminar bookings
    seminar_type = models.CharField(
        max_length=30,
        choices=ActivityType.choices(),
        null=True,
        blank=True,
        verbose_name=_("Seminar Type"),
        help_text=_("Type of seminar (required for seminar bookings)"),
    )

    research_title = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("Research Title"),
        help_text=_("Title of the research/thesis (required for seminar bookings)"),
        db_index=True,  # For search functionality
    )

    # Supervisor information - required only for student seminar bookings
    supervisor_main = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_("Main Supervisor"),
        help_text=_(
            "Name and details of the main supervisor (required for seminar bookings)"
        ),
    )
    supervisor_secondary = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_("Secondary Supervisor"),
        help_text=_("Name and details of the secondary supervisor (optional)"),
    )

    # Examiner information - required only for student seminar bookings
    examiner = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_("Examiner"),
        help_text=_("Name and details of the examiner (required for seminar bookings)"),
    )

    # Document proof upload
    document_proof = models.FileField(
        upload_to="room_booking_documents/%Y/%m/",
        null=True,
        blank=True,
        verbose_name=_("Document Proof"),
        help_text=_("Upload supporting documents (PDF, DOC, etc.)"),
    )

    class Meta:
        db_table = "room_booking"
        ordering = ["booking_date", "booking_start_time"]
        verbose_name = _("Room Booking")
        verbose_name_plural = _("Room Bookings")

        # Add indexes for efficient queries
        indexes = [
            models.Index(
                fields=["booking_date", "booking_start_time", "booking_end_time"]
            ),
            models.Index(fields=["booker", "booking_date"]),
            models.Index(fields=["booking_type", "booking_approval_status"]),
            models.Index(fields=["research_title"]),  # For search
        ]

    def __str__(self):
        user_identifier = self.booker.get_full_name() or self.booker.username
        if self.booking_type == BookingType.SEMINAR.value and self.seminar_type:
            return f"{user_identifier} - {self.seminar_type} on {self.booking_date}"
        return f"{user_identifier} - {self.booking_type} on {self.booking_date}"

    def clean(self):
        """
        Validate the model based on user role and booking type.

        Validation Rules:
        1. Students/Assistants can only create SEMINAR bookings
        2. Staff/Faculty can create any booking type
        3. SEMINAR bookings require full academic details
        4. Other booking types only require basic information
        """
        super().clean()

        if not self.booker:
            return  # Skip validation if no booker set yet

        from custom_auth.models import CustomUserModel

        user_group = self.booker.group
        is_student_group = UserGroup.is_student_group(user_group)
        is_staff_group = UserGroup.is_staff_group(user_group)

        errors = {}

        # 1. Validate booking type permissions
        if (
            is_student_group
            and self.booking_type not in BookingType.student_allowed_types()
        ):
            errors["booking_type"] = _(
                "Students and assistants can only create seminar bookings. "
                f"Available types: {', '.join(BookingType.student_allowed_types())}"
            )

        # 2. Validate required fields for seminar bookings
        if self.booking_type == BookingType.SEMINAR.value:
            if not self.research_title:
                errors["research_title"] = _(
                    "Research title is required for seminar bookings."
                )
            if not self.seminar_type:
                errors["seminar_type"] = _(
                    "Seminar type is required for seminar bookings."
                )
            if not self.supervisor_main:
                errors["supervisor_main"] = _(
                    "Main supervisor is required for seminar bookings."
                )
            if not self.examiner:
                errors["examiner"] = _("Examiner is required for seminar bookings.")

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Override save method to implement approval workflow rules.

        Approval Rules:
        - Students/Assistants: Always created with PENDING status
        - Staff/Faculty: Auto-approved upon creation
        """
        # Check if this is a new instance and set auto-approval for staff
        if (
            not self.pk  # New instance
            and self.booker
            and hasattr(self.booker, "group")
            and UserGroup.is_staff_group(self.booker.group)
            and self.get_approval_status() == ApprovalStatus.PENDING.value
        ):
            self.approve(approved_by=self.booker, notes="Auto-approved for staff user")

        # Let ApprovalMixin handle the rest (but skip auto-approval since we handle it here)
        models.Model.save(self, *args, **kwargs)

    def is_seminar_booking(self):
        """Check if this is a seminar-type booking."""
        return self.booking_type == BookingType.SEMINAR.value

    def requires_academic_details(self):
        """Check if this booking requires full academic details."""
        return BookingType.requires_academic_details(self.booking_type)

    def get_user_identifier(self):
        """Get appropriate user identifier based on user group."""
        if hasattr(self.booker, "student_number") and self.booker.student_number:
            return self.booker.student_number
        elif hasattr(self.booker, "employee_number") and self.booker.employee_number:
            return self.booker.employee_number
        return self.booker.username
