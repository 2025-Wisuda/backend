"""
Custom User Model

Extended Django AbstractUser model with laboratory-specific fields and role-based validation.
Supports both student and staff users with appropriate identifier requirements.

Key Features:
- UUID primary key for enhanced security
- Role-based validation (student_number for students, employee_number for staff)
- Face recognition integration for attendance
- Audit trail with created_by/updated_by tracking
- Profile image support
"""

import uuid

from core.enums import UserGroup
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserModel(AbstractUser):
    """
    Extended user model for laboratory management system.

    Extends Django's AbstractUser with laboratory-specific fields including
    role-based identifiers, face recognition support, and audit tracking.

    Validation Rules:
    - Staff groups require employee_number, no student_number
    - Student groups require student_number, no employee_number
    - Group field is mandatory for all users
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_number = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("Student Number"),
    )
    employee_number = models.CharField(
        max_length=18,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("Employee Number"),
    )
    group = models.CharField(
        max_length=20,
        choices=UserGroup.choices(),
        null=False,
        blank=False,
        verbose_name=_("Group"),
        help_text=_("Select the user's role in the laboratory."),
    )
    avatar = models.ImageField(
        _("Avatar"),
        upload_to="avatars/",
        null=True,
        blank=True,
        help_text=_("Upload a user avatar."),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_%(class)s_set",
        editable=False,
        verbose_name=_("Created By"),
        help_text=_("User who created this record."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        verbose_name=_("Created At"),
        help_text=_("Date and time when this record was created."),
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_%(class)s_set",
        editable=False,
        verbose_name=_("Updated By"),
        help_text=_("User who last updated this record."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        editable=False,
        verbose_name=_("Updated At"),
        help_text=_("Date and time when this record was last updated."),
    )

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-created_at"]
        db_table = "custom_user"

    def clean(self):
        """
        Model validation with role-based identifier requirements.

        Critical validation rules:
        - Staff groups MUST have employee_number, NO student_number
        - Student groups MUST have student_number, NO employee_number
        - Group field is mandatory for all users
        - Identifier fields are auto-trimmed and normalized

        This validation prevents data inconsistency and ensures proper
        user categorization for laboratory access control.
        """
        super().clean()
        from django.core.exceptions import ValidationError

        if not self.group:
            raise ValidationError(
                {
                    "group": _(
                        "Group selection is required. Please select the user's role in the laboratory."
                    )
                }
            )

        # Normalize identifier fields - critical for uniqueness constraints
        if self.student_number is not None:
            self.student_number = self.student_number.strip() or None
        if self.employee_number is not None:
            self.employee_number = self.employee_number.strip() or None

        # Role-based validation - prevents invalid identifier combinations
        if UserGroup.is_staff_group(self.group):
            if not self.employee_number:
                raise ValidationError(
                    {
                        "employee_number": _(
                            "Employee number is required for staff groups."
                        )
                    }
                )
            if self.student_number:
                raise ValidationError(
                    {
                        "student_number": _(
                            "Student number should not be provided for staff groups."
                        )
                    }
                )

        elif UserGroup.is_student_group(self.group):
            if not self.student_number:
                raise ValidationError(
                    {
                        "student_number": _(
                            "Student number is required for student groups."
                        )
                    }
                )
            if self.employee_number:
                raise ValidationError(
                    {
                        "employee_number": _(
                            "Employee number should not be provided for student groups."
                        )
                    }
                )
