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

from core import (
    ActivityType,
    ApprovalMixin,
    ApprovalStatus,
    BaseModel,
    BookingType,
    LabScheduleMixin,
    UserGroup,
)
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


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
        - date: Date the room is booked
        - start_time: Starting time of the booking
        - end_time: Ending time of the booking

    Approval fields (from ApprovalMixin):
        - approval_status: Status of booking (PENDING, APPROVED, REJECTED)
        - approved_by_user: Reference to user who approved the booking
        - approval_timestamp: Timestamp when it was approved
    """

    SCHEDULE_DATE_FIELD = "date"
    START_TIME_FIELD = "start_time"
    END_TIME_FIELD = "end_time"

    APPROVAL_STATUS_FIELD = "approval_status"
    APPROVED_BY_FIELD = "approved_by_user"
    APPROVAL_TIMESTAMP_FIELD = "approval_timestamp"
    APPROVAL_NOTES_FIELD = "approval_notes"

    date = models.DateField(
        db_index=True,
        verbose_name=_("Booking Date"),
        help_text=_("Date when the room is booked"),
    )
    start_time = models.TimeField(
        verbose_name=_("Booking Start Time"),
        help_text=_("Start time of the room booking"),
    )
    end_time = models.TimeField(
        verbose_name=_("Booking End Time"),
        help_text=_("End time of the room booking"),
    )

    approval_status = models.CharField(
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

    booker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="room_bookings",
        verbose_name=_("Booker"),
        help_text=_("User who created this room booking"),
    )

    booking_type = models.CharField(
        max_length=20,
        choices=BookingType.choices(),
        verbose_name=_("Booking Type"),
        help_text=_("Type of booking - determines required fields"),
        db_index=True,
    )

    purpose = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Purpose"),
        help_text=_("Purpose or reason for booking the room (optional)"),
    )

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
        db_index=True,
    )

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

    examiner = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_("Examiner"),
        help_text=_("Name and details of the examiner (required for seminar bookings)"),
    )

    document_proof = models.FileField(
        upload_to="room_booking_documents/%Y/%m/",
        null=True,
        blank=True,
        verbose_name=_("Document Proof"),
        help_text=_("Upload supporting documents (PDF)"),
    )

    class Meta:
        db_table = "room_booking"
        ordering = ["date", "start_time"]
        verbose_name = _("Room Booking")
        verbose_name_plural = _("Room Bookings")

        indexes = [
            models.Index(fields=["date", "start_time", "end_time"]),
            models.Index(fields=["booker", "date"]),
            models.Index(fields=["booking_type", "approval_status"]),
            models.Index(fields=["research_title"]),
        ]

    def __str__(self):
        user_identifier = self.booker.get_full_name() or self.booker.username
        if self.booking_type == BookingType.SEMINAR.value and self.seminar_type:
            return f"{user_identifier} - {self.seminar_type} on {self.date}"
        return f"{user_identifier} - {self.booking_type} on {self.date}"

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
            return

        user_group = self.booker.group
        is_student_group = UserGroup.is_student_group(user_group)

        errors = {}

        if (
            is_student_group
            and self.booking_type not in BookingType.student_allowed_types()
        ):
            errors["booking_type"] = _(
                "Students and assistants can only create seminar bookings. "
                f"Available types: {', '.join(BookingType.student_allowed_types())}"
            )

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
        if (
            not self.pk
            and self.booker
            and hasattr(self.booker, "group")
            and UserGroup.is_staff_group(self.booker.group)
            and self.get_approval_status() == ApprovalStatus.PENDING.value
        ):
            self.approve(approved_by=self.booker, notes="Auto-approved for staff user")

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

    def _validate_schedule_conflicts_for_approval(self):
        """
        Validate that the booking does not conflict with existing lab schedules.
        
        This method checks conflicts specifically for the approval process
        by validating against the LabSchedule aggregator which contains all
        approved bookings from different sources.
        
        Raises:
            ValidationError: If schedule conflicts are found
        """
        from lab_schedule.models import LabScheduleModel

        # Check for conflicts against active lab schedules on the same date
        conflicting_schedules = LabScheduleModel.objects.filter(
            date=self.date,
            is_active=True,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        )
        
        if conflicting_schedules.exists():
            # Get details of first conflict for error message
            first_conflict = conflicting_schedules.first()
            if first_conflict:
                conflict_detail = f"{first_conflict.source_model}: {first_conflict.start_time}-{first_conflict.end_time}"
            else:
                conflict_detail = "unknown schedule"
            
            raise ValidationError(
                _("Cannot approve booking: Schedule conflicts with existing lab activity "
                  f"({conflict_detail}). The requested time slot is already occupied.")
            )

    def approve(self, approved_by, notes=None):
        """
        Override approve method to validate schedule conflicts before approval.
        
        This ensures that room bookings are only approved if they don't conflict
        with existing lab schedules, similar to how lab allocation validation works.
        
        Args:
            approved_by: User who approved the record
            notes: Optional approval notes
            
        Raises:
            ValidationError: If schedule conflicts are found
        """
        # Validate schedule conflicts before approving
        self._validate_schedule_conflicts_for_approval()
        
        # If no conflicts, proceed with approval
        super().approve(approved_by, notes)

    @classmethod
    def bulk_update_with_sync(cls, queryset, **update_fields):
        """
        Bulk update room bookings and manually sync to lab schedule.

        This method performs bulk update and then manually syncs each affected
        booking to the lab schedule aggregator since bulk operations don't
        trigger Django signals.

        Args:
            queryset: QuerySet of RoomBookingModel objects to update
            **update_fields: Fields to update

        Returns:
            int: Number of updated bookings
        """
        # Get the IDs before bulk update
        booking_ids = list(queryset.values_list("id", flat=True))

        # Perform bulk update
        updated_count = queryset.update(**update_fields)

        if updated_count > 0:
            # Manually sync each updated booking
            updated_bookings = cls.objects.filter(id__in=booking_ids)

            for booking in updated_bookings:
                # Import here to avoid circular imports
                from lab_schedule.models import LabScheduleModel

                try:
                    LabScheduleModel.sync_from_room_booking(booking)
                except Exception as e:
                    # Log error but don't stop the process
                    import logging

                    logger = logging.getLogger("application.room_booking")
                    logger.error(
                        f"Failed to sync booking {booking.id} to lab schedule: {e}"
                    )

        return updated_count

    @classmethod
    def bulk_approve_with_sync(
        cls, approved_by_user=None, approval_notes="Bulk approved", **filters
    ):
        """
        Bulk approve room bookings with lab schedule sync.

        Args:
            approved_by_user: User who approved the bookings
            approval_notes: Notes for approval
            **filters: Filters for the queryset (for finding bookings to approve)

        Returns:
            int: Number of approved bookings
        """
        from core.enums import ApprovalStatus
        from django.utils import timezone

        queryset = cls.objects.filter(
            approval_status=ApprovalStatus.PENDING.value, is_active=True, **filters
        )

        update_fields = {
            "approval_status": ApprovalStatus.APPROVED.value,
            "approval_timestamp": timezone.localtime(),
            "approval_notes": approval_notes,
        }

        if approved_by_user:
            update_fields["approved_by_user"] = approved_by_user

        return cls.bulk_update_with_sync(queryset, **update_fields)

    @classmethod
    def bulk_reject_with_sync(cls, approval_notes="Bulk rejected", **filters):
        """
        Bulk reject room bookings with lab schedule sync.

        Args:
            approval_notes: Notes for rejection
            **filters: Filters for the queryset (for finding bookings to reject)

        Returns:
            int: Number of rejected bookings
        """
        from core.enums import ApprovalStatus
        from django.utils import timezone

        queryset = cls.objects.filter(
            approval_status=ApprovalStatus.PENDING.value, is_active=True, **filters
        )
        return cls.bulk_update_with_sync(
            queryset,
            approval_status=ApprovalStatus.REJECTED.value,
            approval_timestamp=timezone.localtime(),
            approval_notes=approval_notes,
        )

    @classmethod
    def bulk_deactivate_with_sync(cls, **filters):
        """
        Bulk deactivate room bookings with lab schedule sync.

        Args:
            **filters: Filters for the queryset

        Returns:
            int: Number of deactivated bookings
        """
        queryset = cls.objects.filter(is_active=True, **filters)
        return cls.bulk_update_with_sync(queryset, is_active=False)

    @classmethod
    def bulk_activate_with_sync(cls, **filters):
        """
        Bulk activate room bookings with lab schedule sync.

        Args:
            **filters: Filters for the queryset

        Returns:
            int: Number of activated bookings
        """
        queryset = cls.objects.filter(is_active=False, **filters)
        return cls.bulk_update_with_sync(queryset, is_active=True)

    @classmethod
    def auto_sync_statuses(cls):
        """Automatically update booking statuses based on date/time progress.

        Logic:
        1. PENDING bookings whose end time has passed -> EXPIRED
        2. APPROVED bookings whose end time has passed -> COMPLETED
        """
        from django.utils import timezone

        now = timezone.localtime()
        today = now.date()
        current_time = now.time()

        # 1. Expire pending bookings that have passed
        pending_expired_qs = cls.objects.filter(
            approval_status=ApprovalStatus.PENDING.value,
            is_active=True,
        ).filter(
            models.Q(date__lt=today)
            | (models.Q(date=today) & models.Q(end_time__lt=current_time))
        )
        if pending_expired_qs.exists():
            pending_expired_qs.update(
                approval_status=ApprovalStatus.EXPIRED.value,
                approval_notes="Auto expired: schedule passed without approval",
            )

        # 2. Mark completed approved bookings whose end time has passed
        approved_completed_qs = cls.objects.filter(
            approval_status=ApprovalStatus.APPROVED.value,
            is_active=True,
        ).filter(
            models.Q(date__lt=today)
            | (models.Q(date=today) & models.Q(end_time__lt=current_time))
        )
        if approved_completed_qs.exists():
            approved_completed_qs.update(
                approval_status=ApprovalStatus.COMPLETED.value,
                approval_notes=models.F("approval_notes"),  # keep existing notes
            )
