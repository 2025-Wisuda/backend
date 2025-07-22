"""
Approval Mixin for Django Models

Provides reusable approval functionality for models that need approval workflow.
This mixin can be used by any model that requires approval status tracking.

Features:
- Auto-approval for staff users
- Approval status tracking with proper field management
- Timestamp and user tracking for approvals/rejections
- Consistent approval workflow across all models

Usage:
    from core.models import BaseModel, ApprovalMixin
    from core.enums import ApprovalStatus
    
    class MyModel(BaseModel, ApprovalMixin):
        # Your model fields here
        name = models.CharField(max_length=100)
        
        # Override these class attributes to customize field names
        APPROVAL_STATUS_FIELD = 'my_approval_status'
        APPROVED_BY_FIELD = 'my_approved_by'
        APPROVAL_TIMESTAMP_FIELD = 'my_approval_timestamp'
        APPROVAL_NOTES_FIELD = 'my_approval_notes'
        
        class Meta:
            db_table = "my_model"

Fields that will be added to your model:
- approval_status: CharField with ApprovalStatus choices (default: PENDING)
- approved_by: ForeignKey to User who approved/rejected
- approval_timestamp: DateTimeField when approved/rejected
- approval_notes: TextField for approval/rejection notes

Methods provided:
- approve(approved_by, notes=None): Approve with user, timestamp and optional notes
- reject(rejected_by, notes=None): Reject with user, timestamp and optional notes
- update_approval_status(new_status, user, notes=None): Update status with proper handling
- Auto-approval in save() method for staff group users (not students/assistants)
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..enums import ApprovalStatus, UserGroup


class ApprovalMixin(models.Model):
    """
    Mixin that provides approval functionality for any model.

    Adds approval status tracking with automatic handling of:
    - Approval status changes
    - Approved by user tracking
    - Approval timestamp recording
    - Auto-approval for staff users
    """

    # Class attributes for field name customization - can be overridden
    APPROVAL_STATUS_FIELD = "approval_status"
    APPROVED_BY_FIELD = "approved_by"
    APPROVAL_TIMESTAMP_FIELD = "approval_timestamp"
    APPROVAL_NOTES_FIELD = "approval_notes"

    class Meta:
        abstract = True

    # Accessor methods using field mapping
    def get_approval_status(self):
        """Get the approval status using mapped field name."""
        return getattr(self, self.APPROVAL_STATUS_FIELD)

    def set_approval_status(self, value):
        """Set the approval status using mapped field name."""
        setattr(self, self.APPROVAL_STATUS_FIELD, value)

    def get_approved_by(self):
        """Get the approved by user using mapped field name."""
        return getattr(self, self.APPROVED_BY_FIELD)

    def set_approved_by(self, value):
        """Set the approved by user using mapped field name."""
        setattr(self, self.APPROVED_BY_FIELD, value)

    def get_approval_timestamp(self):
        """Get the approval timestamp using mapped field name."""
        return getattr(self, self.APPROVAL_TIMESTAMP_FIELD)

    def set_approval_timestamp(self, value):
        """Set the approval timestamp using mapped field name."""
        setattr(self, self.APPROVAL_TIMESTAMP_FIELD, value)

    def get_approval_notes(self):
        """Get the approval notes using mapped field name."""
        return getattr(self, self.APPROVAL_NOTES_FIELD)

    def set_approval_notes(self, value):
        """Set the approval notes using mapped field name."""
        setattr(self, self.APPROVAL_NOTES_FIELD, value)

    def save(self, *args, **kwargs):
        """
        Override save method to handle auto-approval logic.
        If creator is staff group (not student or assistant), automatically approve.
        """
        # Auto-approve if creator is staff group and status is pending
        if (
            hasattr(self, "created_by")
            and self.created_by
            and hasattr(self.created_by, "group")
            and UserGroup.is_staff_group(self.created_by.group)
            and self.get_approval_status() == ApprovalStatus.PENDING.value
        ):
            self.approve(approved_by=self.created_by)

        super().save(*args, **kwargs)

    def clean(self):
        """Run approval validation."""
        super().clean()

        from ..validators import ApprovalValidator

        validator = ApprovalValidator(
            instance=self,
            model_class=self.__class__,
            approval_status_field=self.APPROVAL_STATUS_FIELD,
        )
        validator.validate()

    def approve(self, approved_by, notes=None):
        """
        Approve the record with proper approval details.

        Args:
            approved_by: User who approved the record
            notes: Optional approval notes
        """
        self.set_approval_status(ApprovalStatus.APPROVED.value)
        self.set_approved_by(approved_by)
        self.set_approval_timestamp(timezone.localtime())
        if notes:
            self.set_approval_notes(notes)

    def reject(self, rejected_by, notes=None):
        """
        Reject the record with proper rejection details.

        Args:
            rejected_by: User who rejected the record
            notes: Optional rejection notes (recommended for rejections)
        """
        self.set_approval_status(ApprovalStatus.REJECTED.value)
        self.set_approved_by(rejected_by)
        self.set_approval_timestamp(timezone.localtime())
        if notes:
            self.set_approval_notes(notes)

    def update_approval_status(self, new_status, user, notes=None):
        """
        Update approval status with proper handling of approval details.

        Args:
            new_status: New approval status value
            user: User making the change
            notes: Optional notes for the status change
        """
        if new_status == ApprovalStatus.APPROVED.value:
            self.approve(approved_by=user, notes=notes)
        elif new_status == ApprovalStatus.REJECTED.value:
            self.reject(rejected_by=user, notes=notes)
        elif new_status == ApprovalStatus.PENDING.value:
            self.set_approval_status(ApprovalStatus.PENDING.value)
            self.set_approved_by(None)
            self.set_approval_timestamp(None)
            self.set_approval_notes(None)
