from __future__ import annotations

from typing import TYPE_CHECKING

from core import BaseModel, UserGroup
from django.conf import settings
from django.db import models
from django.db.models.functions import Extract
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django.db.models.manager import Manager


class CourseModel(BaseModel):
    if TYPE_CHECKING:
        objects: Manager[CourseModel]
    title = models.CharField(
        max_length=200,
        verbose_name=_("Course Title"),
        help_text=_("Title of the laboratory course"),
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Course Description"),
        help_text=_("Detailed description of the course content and objectives"),
    )

    start_date = models.DateField(
        verbose_name=_("Course Start Date"),
        help_text=_("Start date of the course period"),
    )

    end_date = models.DateField(
        verbose_name=_("Course End Date"),
        help_text=_("End date of the course period"),
    )

    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="enrolled_courses",
        blank=True,
        limit_choices_to={"groups__name__in": UserGroup.student_groups()},
        verbose_name=_("Enrolled Students"),
        help_text=_("Students enrolled in this course"),
    )

    teaching_assistants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="assigned_courses",
        blank=True,
        limit_choices_to={"groups__name": UserGroup.LABORATORY_ASSISTANT.value},
        verbose_name=_("Teaching Assistants"),
        help_text=_("Teaching assistants assigned to this course"),
    )

    enroll_key = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        unique=True,
        verbose_name=_("Enrollment Key"),
        help_text=_("Enrollment key for student self-registration"),
    )



    image = models.ImageField(
        upload_to="course_images/",
        null=True,
        blank=True,
        verbose_name=_("Course Image"),
        help_text=_("Course cover image"),
    )

    class Meta:
        db_table = "course"
        ordering = ["-start_date", "title"]
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")

        constraints = [
            models.UniqueConstraint(
                Extract("start_date", "year"),
                "title",
                name="unique_title_per_year",
            )
        ]

        indexes = [
            models.Index(fields=["start_date", "end_date"]),
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()

        from django.core.exceptions import ValidationError

        errors = {}

        if self.end_date and self.end_date < self.start_date:
            errors["end_date"] = _("End date must be after or equal to start date.")

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def can_enroll_student(self, student):
        if not student.groups.filter(name__in=UserGroup.student_groups()).exists():
            return False

        if self.students.filter(pk=student.pk).exists():
            return False

        return self.can_enroll()

    def enroll_student(self, student):
        """
        Enroll student in course with atomic transaction.
        Returns True if successful, False if failed.
        """
        from django.db import transaction

        # Double-check eligibility in atomic context
        with transaction.atomic():
            # Refresh from DB to avoid race conditions
            course = CourseModel.objects.select_for_update().get(pk=self.pk)
            
            if not course.can_enroll_student(student):
                return False
            
            # Add student to course
            course.students.add(student)
            return True

    def can_enroll(self):
        from django.utils import timezone

        today = timezone.localtime().date()
        return today <= self.end_date
