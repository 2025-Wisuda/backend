from django.db import models
from .course_model import Course
from django.conf import settings
from core.models import BaseModel


class CourseSession(BaseModel):
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    course = models.ForeignKey(
        Course,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name="Praktikum",
    )
    session_date = models.DateField(null=True, blank=True, verbose_name="Tanggal")
    start_time = models.TimeField(null=True, blank=True, verbose_name="Waktu Mulai")
    end_time = models.TimeField(null=True, blank=True, verbose_name="Waktu Selesai")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled",
        verbose_name="Status",
    )
    title = models.CharField(
        max_length=100, null=False, blank=False, verbose_name="Judul Pertemuan"
    )
    teaching_assistants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="course_sessions_teaching_assistants",
        blank=True,
        verbose_name="Asisten Praktikum (Judul)",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_course_sessions",
        null=False,
        verbose_name="Dibuat Oleh",
    )

    lab_schedule = models.OneToOneField(
        "schedule.LabSchedule",
        on_delete=models.CASCADE,
        related_name="course_session",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "course_session"
        ordering = ["session_date"]
        verbose_name = "Pertemuan Praktikum"
        verbose_name_plural = "Pertemuan Praktikum"

    def __str__(self):
        return f"{self.title} - {self.course.title}"
