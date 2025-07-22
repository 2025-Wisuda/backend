"""
LabScheduleModel Aggregator Model

This is a simplified aggregator model that serves as the central point for 
cross-model conflict detection across different lab booking types:
- LabAllocation (technician workflow)
- CourseSession (assistant workflow) 
- RoomBooking (all users workflow)

This model stores only the essential scheduling information needed for conflict
detection and does not include approval workflows or bulk generation features.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core import BaseModel


class LabScheduleModel(BaseModel):
    """
    Pure aggregator model for lab scheduling conflict detection.

    This model stores essential scheduling information from all lab booking types
    to enable cross-model conflict detection. It acts as a central registry of
    all lab time slots regardless of booking type.

    This is a simple model with basic fields - no mixin needed because:
    - All validation happens in the source models (LabAllocation, etc.)
    - This just stores already-validated data for conflict detection
    - Other models' validators check conflicts against this model

    Fields:
        - date: Date of the scheduled activity
        - start_time: Start time of the activity
        - end_time: End time of the activity
        - source_model: Type of booking that created this entry
        - source_id: ID of the original booking record
        - type: Type of activity from source model
        - detail: Detailed description from source model
        - created_by: User who created the original booking (from BaseModel)
    """

    # Basic schedule fields - defined directly, no mixin needed
    date = models.DateField(
        db_index=True,
        verbose_name=_("Schedule Date"),
        help_text=_("Date when the lab activity is scheduled"),
    )
    start_time = models.TimeField(
        verbose_name=_("Start Time"),
        help_text=_("Start time of the lab activity"),
    )
    end_time = models.TimeField(
        verbose_name=_("End Time"),
        help_text=_("End time of the lab activity"),
    )

    # Source tracking for aggregation
    source_model = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name=_("Source Model"),
        help_text=_(
            "Type of booking that created this entry (e.g., 'LabAllocation', 'CourseSession')"
        ),
    )

    source_id = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name=_("Source ID"),
        help_text=_(
            "ID of the original booking record (supports both UUID and integer)"
        ),
    )

    # Activity information from source model
    type = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name=_("Activity Type"),
        help_text=_("Type of activity from the source model"),
    )

    detail = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Activity Detail"),
        help_text=_("Detailed description from the source model"),
    )

    class Meta:
        db_table = "lab_schedule"
        ordering = ["date", "start_time"]
        verbose_name = _("Lab Schedule")
        verbose_name_plural = _("Lab Schedules")

        # Ensure unique combination of source model and ID
        unique_together = [["source_model", "source_id"]]

        # Index for efficient conflict detection queries
        indexes = [
            models.Index(fields=["date", "start_time", "end_time"]),
        ]

    def __str__(self):
        return f"{self.date} {self.start_time}-{self.end_time} - {self.source_model}"

    @classmethod
    def sync_from_allocation(cls, allocation_instance):
        """
        Synchronize a LabAllocation instance with the aggregator.

        This method is called by signals when a LabAllocation is saved or soft-deleted.
        Instead of deleting entries physically, it updates the 'is_active' flag
        to reflect the current active state of the allocation.

        Args:
            allocation_instance: Instance of LabAllocationModel to sync.
        """
        # Try to find existing aggregator entry for this allocation
        existing = cls.objects.filter(
            source_model="LabAllocation", source_id=str(allocation_instance.pk)
        ).first()

        if existing:
            if allocation_instance.is_active:
                # Update existing entry with current allocation details
                existing.date = allocation_instance.get_date()
                existing.start_time = allocation_instance.get_start_time()
                existing.end_time = allocation_instance.get_end_time()
                existing.type = allocation_instance.type
                existing.detail = allocation_instance.detail or ""
                existing.created_by = allocation_instance.created_by
                existing.updated_by = allocation_instance.updated_by
                existing.is_active = True
                existing.save()
            else:
                # Soft delete: mark as inactive instead of physical delete
                existing.is_active = False
                existing.save()
        else:
            if allocation_instance.is_active:
                # Create new aggregator entry if allocation is active
                cls.objects.create(
                    date=allocation_instance.get_date(),
                    start_time=allocation_instance.get_start_time(),
                    end_time=allocation_instance.get_end_time(),
                    source_model="LabAllocation",
                    source_id=str(allocation_instance.pk),
                    type=allocation_instance.type,
                    detail=allocation_instance.detail or "",
                    created_by=allocation_instance.created_by,
                    updated_by=allocation_instance.updated_by,
                    is_active=True,
                )

    @classmethod
    def remove_allocation(cls, allocation_id):
        """
        Soft remove a LabAllocation entry from the aggregator.

        This method sets 'is_active' to False instead of deleting the record.

        Args:
            allocation_id: Primary key of the LabAllocation to remove.
        """
        entry = cls.objects.filter(
            source_model="LabAllocation", source_id=str(allocation_id)
        ).first()

        if entry:
            entry.is_active = False
            entry.save()

    @classmethod
    def sync_from_course_session(cls, session_instance):
        """
        Synchronize a CourseSession instance with the aggregator.

        This method is called by signals when a CourseSession is saved or soft-deleted.
        Instead of deleting entries physically, it updates the 'is_active' flag
        to reflect the current active state of the session.

        Args:
            session_instance: Instance of CourseSessionModel to sync.
        """
        # Try to find existing aggregator entry for this session
        existing = cls.objects.filter(
            source_model="CourseSession", source_id=str(session_instance.pk)
        ).first()

        if existing:
            if session_instance.is_active and session_instance.status != "cancelled":
                # Update existing entry with new data
                existing.date = session_instance.date
                existing.start_time = session_instance.start_time
                existing.end_time = session_instance.end_time
                existing.type = session_instance.get_course()
                existing.detail = session_instance.title
                existing.created_by = session_instance.created_by
                existing.updated_by = session_instance.updated_by
                existing.is_active = True
                existing.save()
            else:
                # Soft delete: mark as inactive instead of physical delete
                existing.is_active = False
                existing.save()
        else:
            if session_instance.is_active and session_instance.status != "cancelled":
                # Create new aggregator entry if session is active and not cancelled
                cls.objects.create(
                    date=session_instance.date,
                    start_time=session_instance.start_time,
                    end_time=session_instance.end_time,
                    source_model="CourseSession",
                    source_id=str(session_instance.pk),
                    type=session_instance.get_course(),
                    detail=session_instance.title,
                    created_by=session_instance.created_by,
                    updated_by=session_instance.updated_by,
                    is_active=True,
                )

    @classmethod
    def remove_course_session(cls, session_id):
        """
        Soft remove a CourseSession entry from the aggregator.

        This method sets 'is_active' to False instead of deleting the record.

        Args:
            session_id: Primary key of the CourseSession to remove.
        """
        entry = cls.objects.filter(
            source_model="CourseSession", source_id=str(session_id)
        ).first()

        if entry:
            entry.is_active = False
            entry.save()

    @classmethod
    def sync_from_room_booking(cls, booking_instance):
        """
        Synchronize a RoomBooking instance with the aggregator.

        This method is called by signals when a RoomBooking is saved or soft-deleted.
        Instead of deleting entries physically, it updates the 'is_active' flag
        to reflect the current active state of the booking.

        Args:
            booking_instance: Instance of RoomBookingModel to sync.
        """
        # Try to find existing aggregator entry for this booking
        existing = cls.objects.filter(
            source_model="RoomBooking", source_id=str(booking_instance.pk)
        ).first()

        # Import here to avoid circular imports
        from core.enums import ApprovalStatus

        # Check if booking should be synced (active AND approved)
        should_sync = (
            booking_instance.is_active
            and booking_instance.approval_status == ApprovalStatus.APPROVED.value
        )

        if existing:
            if should_sync:
                # Update existing entry with current booking details
                detail = " - ".join(
                    filter(
                        None,
                        [
                            booking_instance.research_title,
                            booking_instance.seminar_type,
                        ],
                    )
                )
                existing.date = booking_instance.get_date()
                existing.start_time = booking_instance.get_start_time()
                existing.end_time = booking_instance.get_end_time()
                existing.type = booking_instance.booking_type
                existing.detail = detail
                existing.created_by = booking_instance.created_by
                existing.updated_by = booking_instance.updated_by
                existing.is_active = True
                existing.save()
            else:
                # Mark as inactive if not approved or not active
                existing.is_active = False
                existing.save()
        else:
            if should_sync:
                # Create new aggregator entry only if booking is active AND approved
                detail = " - ".join(
                    filter(
                        None,
                        [
                            booking_instance.research_title,
                            booking_instance.seminar_type,
                        ],
                    )
                )
                cls.objects.create(
                    date=booking_instance.get_date(),
                    start_time=booking_instance.get_start_time(),
                    end_time=booking_instance.get_end_time(),
                    source_model="RoomBooking",
                    source_id=str(booking_instance.pk),
                    type=booking_instance.booking_type,
                    detail=detail,
                    created_by=booking_instance.created_by,
                    updated_by=booking_instance.updated_by,
                    is_active=True,
                )

    @classmethod
    def remove_room_booking(cls, booking_id):
        """
        Soft remove a RoomBooking entry from the aggregator.

        This method sets 'is_active' to False instead of deleting the record.

        Args:
            booking_id: Primary key of the RoomBooking to remove.
        """
        entry = cls.objects.filter(
            source_model="RoomBooking", source_id=str(booking_id)
        ).first()

        if entry:
            entry.is_active = False
            entry.save()
