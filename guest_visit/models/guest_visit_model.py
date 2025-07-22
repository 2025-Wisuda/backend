"""
Guest Visit Model for Laboratory Visitor Management System.

This model handles visitor registration with support for both
manual entry and user reference modes.

Features:
- Conditional visitor information (manual vs registered user)
- Basic scheduling fields (date, start/end time)
- Purpose and signature tracking
- Integration with laboratory schedule system
"""

from core import BaseModel, VisitorIdentityType
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class GuestVisitModel(BaseModel):
    """
    Model for laboratory guest visit tracking.

    This model supports two modes:
    1. Manual Entry: Fill visitor_name, visitor_identity_type, visitor_identity manually
    2. User Reference: Select visitor_user, other fields auto-populated

    Conditional Field Logic:
    - If visitor_user is set: visitor_name, visitor_identity_type, visitor_identity ignored
    - If visitor_user is None: visitor_name required, identity fields optional but recommended
    """

    # Visitor information - conditional fields
    visitor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="guest_visits_as_visitor",
        verbose_name=_("Registered Visitor"),
        help_text=_("Select if visitor is a registered user in the system"),
    )

    # Manual visitor fields (used when visitor is None)
    name = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_("Visitor Name"),
        help_text=_("Name of the visitor (required if not a registered user)"),
    )

    identity_type = models.CharField(
        max_length=20,
        choices=VisitorIdentityType.choices(),
        null=True,
        blank=True,
        verbose_name=_("Identity Type"),
        help_text=_("Type of identity number (optional)"),
    )

    identity_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_("Identity Number"),
        help_text=_("Identity number (optional)"),
    )

    # Visit details - required fields
    date = models.DateField(
        db_index=True,
        verbose_name=_("Visit Date"),
        help_text=_("Date of the visit"),
    )

    start_time = models.TimeField(
        verbose_name=_("Start Time"),
        help_text=_("Start time of the visit"),
    )

    end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("End Time"),
        help_text=_("End time of the visit (optional)"),
    )

    purpose = models.TextField(
        verbose_name=_("Purpose"),
        help_text=_("Purpose of the visit"),
    )

    class Meta:
        db_table = "guest_visit"
        ordering = ["-date", "-start_time"]
        verbose_name = _("Guest Visit")
        verbose_name_plural = _("Guest Visits")

        # Indexes for efficient queries
        indexes = [
            models.Index(fields=["date", "start_time"]),
            models.Index(fields=["visitor", "date"]),
        ]

    def __str__(self):
        visitor_name = self.get_visitor_name()
        return f"{visitor_name} - {self.date} ({self.purpose[:50]})"

    def clean(self):
        """Validate guest visit data."""
        errors = {}

        # Either visitor OR name must be provided
        if not self.visitor and not self.name:
            errors["name"] = _(
                "Either select a registered user or provide visitor name"
            )

        # If manual entry with identity, both type and number should be provided
        if not self.visitor:
            if self.identity_type and not self.identity_number:
                errors["identity_number"] = _(
                    "Identity number required when identity type is selected"
                )
            if self.identity_number and not self.identity_type:
                errors["identity_type"] = _(
                    "Identity type required when identity number is provided"
                )

        # End time should be after start time if provided
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            errors["end_time"] = _("End time must be after start time")

        if errors:
            raise ValidationError(errors)

    def get_visitor_name(self):
        """Get visitor name from user or manual field."""
        if self.visitor:
            return self.visitor.get_full_name() or self.visitor.username
        return self.name or "Unknown Visitor"

    def get_visitor_identity(self):
        """Get visitor identity from user or manual field."""
        if self.visitor:
            if hasattr(self.visitor, "student_number") and self.visitor.student_number:
                return f"{VisitorIdentityType.STUDENT_NUMBER.value}: {self.visitor.student_number}"
            elif (
                hasattr(self.visitor, "employee_number")
                and self.visitor.employee_number
            ):
                return f"{VisitorIdentityType.EMPLOYEE_NUMBER.value}: {self.visitor.employee_number}"
        elif self.identity_type and self.identity_number:
            return f"{self.identity_type}: {self.identity_number}"
        return None

    def is_manual_entry(self):
        """Check if this is a manual entry (not linked to a user)."""
        return self.visitor is None

    def can_edit(self):
        """Check if this visit can still be edited (within 5 minutes of creation)."""
        from datetime import timedelta

        if not self.created_at:
            return True  # New object, can edit

        # Allow editing within 5 minutes of creation
        time_limit = self.created_at + timedelta(minutes=5)
        return timezone.localtime() <= time_limit
