import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.enums import UserGroup


class CustomUserModel(AbstractUser):
    """
    Custom model for custom user with laboratory-specific fields.

    - Stores group as a string value (name) from UserGroup enum.
    - Role-based group (e.g., student, staff) using `UserGroup` enum
    - Audit fields: created_by/at, updated_by/at
    - Validation logic in `clean()` method to enforce group-based constraints
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
    face_image_url = models.ImageField(
        _("Face Image"),
        upload_to="faces/",
        null=True,
        blank=True,
        help_text=_("Upload a face photo for attendance purposes."),
    )
    face_uploaded = models.BooleanField(_("Face Uploaded"), default=False)
    avatar_url = models.ImageField(
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

        if self.student_number is not None:
            self.student_number = self.student_number.strip() or None
        if self.employee_number is not None:
            self.employee_number = self.employee_number.strip() or None

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
