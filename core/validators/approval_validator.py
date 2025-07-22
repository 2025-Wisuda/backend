"""
Approval Validator for Django Models

Provides reusable approval validation functionality for models that use ApprovalMixin.
This validator handles approval status change validation logic.

Features:
- Validates approval status transitions
- Ensures only pending approvals can be modified
- Configurable field names to work with different models
- Works with any model that has approval functionality

Usage:
    from core.validators import ApprovalValidator
    
    class MyModel(BaseModel, ApprovalMixin):
        def clean(self):
            super().clean()
            validator = ApprovalValidator(
                instance=self,
                model_class=MyModel
            )
            validator.validate()
"""

from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..enums import ApprovalStatus


class ApprovalValidator:
    """
    Validator for approval-related functionality.

    Handles validation of approval status changes and transitions
    to ensure proper approval workflow.
    """

    def __init__(
        self,
        instance,
        model_class,
        approval_status_field="approval_status",
        approval_pending_value=ApprovalStatus.PENDING.value,
        pk_field="pk",
        date_field="scheduled_date",  # For expiry validation
        start_time_field="activity_start_time",  # For schedule validation
        end_time_field="activity_end_time",  # For completion validation
    ):
        """
        Args:
            instance: model instance to validate
            model_class: model class for querying old data
            approval_status_field: name of approval status field (default 'approval_status')
            approval_pending_value: value representing pending status (default ApprovalStatus.PENDING.value)
            pk_field: name of primary key field (default 'pk')
            date_field: name of scheduled date field for expiry validation
            start_time_field: name of start time field for progress validation
            end_time_field: name of end time field for completion validation
        """
        self.instance = instance
        self.model_class = model_class
        self.approval_status_field = approval_status_field
        self.approval_pending_value = approval_pending_value
        self.pk_field = pk_field
        self.date_field = date_field
        self.start_time_field = start_time_field
        self.end_time_field = end_time_field

    def validate(self, user=None):
        """Run all approval validations."""
        self.validate_approval_status_transitions()
        self.validate_approval_fields_consistency()
        self.validate_schedule_timing()
        self.validate_expiry_conditions()
        if user:
            self.validate_approval_permissions(user)

    def validate_approval_status_transitions(self):
        """
        Validate that approval status transitions follow simplified business rules.

        Valid transitions:
        - PENDING -> APPROVED/REJECTED (manual)
        - APPROVED -> CANCELLED (manual)
        - PENDING -> EXPIRED (automatic, system only)
        - Final states (REJECTED/CANCELLED/EXPIRED) -> No changes allowed
        """
        if not (self.pk_field and hasattr(self.instance, self.pk_field)):
            return

        pk_val = getattr(self.instance, self.pk_field)
        if not pk_val:
            return

        old_obj = self.model_class.objects.filter(pk=pk_val).first()
        if not old_obj:
            return

        old_status = getattr(old_obj, self.approval_status_field, None)
        new_status = getattr(self.instance, self.approval_status_field, None)

        if old_status == new_status:
            return  # No change

        # Define valid transitions (simplified)
        valid_transitions = {
            ApprovalStatus.PENDING.value: [
                ApprovalStatus.APPROVED.value,
                ApprovalStatus.REJECTED.value,
                ApprovalStatus.EXPIRED.value,  # Only for system auto-expire
            ],
            ApprovalStatus.APPROVED.value: [
                ApprovalStatus.CANCELLED.value,
            ],
        }

        # Final states cannot be changed
        final_states = [
            ApprovalStatus.REJECTED.value,
            ApprovalStatus.CANCELLED.value,
            ApprovalStatus.EXPIRED.value,
        ]

        if old_status in final_states:
            raise ValidationError(
                {
                    self.approval_status_field: _(
                        "Cannot change status from final state '{}'. Final states are permanent."
                    ).format(old_status)
                }
            )

        # Check if transition is valid
        allowed_new_statuses = valid_transitions.get(old_status, [])
        if new_status not in allowed_new_statuses:
            raise ValidationError(
                {
                    self.approval_status_field: _(
                        "Invalid status transition from '{}' to '{}'. Allowed transitions: {}"
                    ).format(old_status, new_status, ", ".join(allowed_new_statuses))
                }
            )

    def validate_approval_fields_consistency(self):
        """
        Validate that approval fields are consistent with each other.

        Business rules:
        - If status is APPROVED/REJECTED/COMPLETED, approved_by should be set
        - If status is PENDING, approved_by should be None
        - Approval timestamp should be set for final statuses
        """
        approval_status = getattr(self.instance, self.approval_status_field, None)

        # Check for approved_by field
        if hasattr(self.instance, "approved_by_user"):
            approved_by = getattr(self.instance, "approved_by_user", None)

            # Statuses that require approved_by to be set
            requires_approver = [
                ApprovalStatus.APPROVED.value,
                ApprovalStatus.REJECTED.value,
                ApprovalStatus.COMPLETED.value,
            ]

            if approval_status in requires_approver and not approved_by:
                raise ValidationError(
                    {
                        "approved_by_user": _(
                            "Approver must be specified for status '{}'"
                        ).format(approval_status)
                    }
                )

            if approval_status == ApprovalStatus.PENDING.value and approved_by:
                raise ValidationError(
                    {
                        "approved_by_user": _(
                            "Approver should not be set for pending status"
                        )
                    }
                )

        # Check for approval timestamp
        if hasattr(self.instance, "approval_timestamp"):
            approval_timestamp = getattr(self.instance, "approval_timestamp", None)

            # Statuses that require approval timestamp
            requires_timestamp = [
                ApprovalStatus.APPROVED.value,
                ApprovalStatus.REJECTED.value,
                ApprovalStatus.COMPLETED.value,
                ApprovalStatus.EXPIRED.value,
            ]

            if approval_status in requires_timestamp and not approval_timestamp:
                # Auto-set timestamp if not provided
                setattr(self.instance, "approval_timestamp", timezone.localtime())

    def validate_approval_permissions(self, user=None):
        """
        Validate that the user has permission to make approval changes.

        Args:
            user: User attempting to make the approval change

        Permission rules:
        - Only staff can approve/reject
        - Only laboratory heads can manually set expired status
        - Users can cancel their own approved requests
        """
        if not user:
            return

        approval_status = getattr(self.instance, self.approval_status_field, None)

        # Staff-only actions
        staff_only_statuses = [
            ApprovalStatus.APPROVED.value,
            ApprovalStatus.REJECTED.value,
        ]

        if approval_status in staff_only_statuses and not user.is_staff:
            raise ValidationError(
                {
                    self.approval_status_field: _(
                        "Only staff members can set status to '{}'"
                    ).format(approval_status)
                }
            )

        # Laboratory head only actions (manual expire)
        from core.enums import UserGroup

        head_only_statuses = [ApprovalStatus.EXPIRED.value]

        if (
            approval_status in head_only_statuses
            and hasattr(user, "group")
            and user.group != UserGroup.LABORATORY_HEAD.value
        ):
            raise ValidationError(
                {
                    self.approval_status_field: _(
                        "Only laboratory heads can manually set status to '{}'"
                    ).format(approval_status)
                }
            )

        # Cancel validation - users can cancel their own approved items
        if approval_status == ApprovalStatus.CANCELLED.value:
            if hasattr(self.instance, "created_by"):
                created_by = getattr(self.instance, "created_by", None)
                if created_by and created_by != user and not user.is_staff:
                    raise ValidationError(
                        {
                            self.approval_status_field: _(
                                "You can only cancel your own requests or be a staff member"
                            )
                        }
                    )

    def validate_schedule_timing(self):
        """
        Validate schedule timing for expired status.

        Rules:
        - EXPIRED is automatically set for pending items past start date/time
        """
        approval_status = getattr(self.instance, self.approval_status_field, None)

        if not hasattr(self.instance, self.date_field):
            return

        scheduled_date = getattr(self.instance, self.date_field, None)
        if not scheduled_date:
            return

        today = date.today()
        now = timezone.localtime()

        # Auto-expire validation - only for system use
        if approval_status == ApprovalStatus.EXPIRED.value:
            # This should only be set by system auto-expire
            if scheduled_date >= today:
                # Check if it's today but still before start time
                if scheduled_date == today and hasattr(
                    self.instance, self.start_time_field
                ):
                    start_time = getattr(self.instance, self.start_time_field, None)
                    if start_time:
                        scheduled_datetime = timezone.make_aware(
                            datetime.combine(scheduled_date, start_time)
                        )
                        if now < scheduled_datetime:
                            raise ValidationError(
                                {
                                    self.approval_status_field: _(
                                        "Cannot set status to 'Expired' before scheduled start time"
                                    )
                                }
                            )
                else:
                    raise ValidationError(
                        {
                            self.approval_status_field: _(
                                "Cannot set status to 'Expired' for current or future dates"
                            )
                        }
                    )

    def validate_expiry_conditions(self):
        """
        Validate conditions for expired status.

        Rules:
        - EXPIRED can only be set for past dates
        - EXPIRED should not be set if already completed
        """
        approval_status = getattr(self.instance, self.approval_status_field, None)

        if approval_status != ApprovalStatus.EXPIRED.value:
            return

        if not hasattr(self.instance, self.date_field):
            return

        scheduled_date = getattr(self.instance, self.date_field, None)
        if not scheduled_date:
            return

        today = date.today()

        # Can only expire past events
        if scheduled_date >= today:
            raise ValidationError(
                {
                    self.approval_status_field: _(
                        "Cannot set status to 'Expired' for current or future dates"
                    )
                }
            )

        # Check if there's an end time and it hasn't passed yet
        if hasattr(self.instance, self.end_time_field):
            end_time = getattr(self.instance, self.end_time_field, None)
            if end_time and scheduled_date == today:
                scheduled_end_datetime = timezone.make_aware(
                    datetime.combine(scheduled_date, end_time)
                )
                if timezone.localtime() < scheduled_end_datetime:
                    raise ValidationError(
                        {
                            self.approval_status_field: _(
                                "Cannot set status to 'Expired' before scheduled end time"
                            )
                        }
                    )

    def can_auto_expire(self):
        """
        Check if the instance can be automatically expired.

        Returns:
            bool: True if the instance can be auto-expired

        Rules:
        - Only PENDING items can be auto-expired
        - Must be past scheduled start date/time
        """
        approval_status = getattr(self.instance, self.approval_status_field, None)

        # Only pending items can be auto-expired
        if approval_status != ApprovalStatus.PENDING.value:
            return False

        if not hasattr(self.instance, self.date_field):
            return False

        scheduled_date = getattr(self.instance, self.date_field, None)
        if not scheduled_date:
            return False

        today = date.today()
        now = timezone.localtime()

        # Check if it's past the scheduled date
        if scheduled_date < today:
            return True

        # Check if it's past the start time today
        if scheduled_date == today and hasattr(self.instance, self.start_time_field):
            start_time = getattr(self.instance, self.start_time_field, None)
            if start_time:
                scheduled_datetime = timezone.make_aware(
                    datetime.combine(scheduled_date, start_time)
                )
                return now > scheduled_datetime

        return False

    def auto_expire(self):
        """
        Automatically expire the instance if conditions are met.

        Returns:
            bool: True if auto-expired, False otherwise
        """
        if not self.can_auto_expire():
            return False

        setattr(self.instance, self.approval_status_field, ApprovalStatus.EXPIRED.value)

        # Set approval timestamp if field exists
        if hasattr(self.instance, "approval_timestamp"):
            setattr(self.instance, "approval_timestamp", timezone.localtime())

        return True
