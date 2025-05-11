from django.db import models
from django.conf import settings
from core.models import BaseModel


class Course(BaseModel):
    title = models.CharField(max_length=100, verbose_name="Judul Praktikum")
    description = models.TextField(
        null=True, blank=True, verbose_name="Deskripsi Praktikum"
    )
    start_date = models.DateField(null=False, blank=False, verbose_name="Tanggal Mulai")
    end_date = models.DateField(null=False, blank=False, verbose_name="Tanggal Selesai")
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="course_students",
        blank=True,
        verbose_name="Peserta Praktikum",
    )
    teaching_assistants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="course_teaching_assistants",
        blank=True,
        verbose_name="Asisten Praktikum",
    )
    enroll_key = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Enroll Key"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_courses",
        verbose_name="Dibuat Oleh",
    )
    total_students = models.PositiveIntegerField(
        default=0, verbose_name="Jumlah Peserta"
    )
    total_teaching_assistants = models.PositiveIntegerField(
        default=0, verbose_name="Jumlah Asisten"
    )
    total_participants = models.PositiveIntegerField(
        default=0, verbose_name="Total Peserta Praktikum"
    )

    class Meta:
        db_table = "course"
        ordering = ["start_date"]
        verbose_name = "Praktikum"
        verbose_name_plural = "Praktikum"

    def __str__(self):
        return f"{self.title}"

    def is_user_enrolled(self, user):
        return (
            self.students.filter(id=user.id).exists()
            or self.teaching_assistants.filter(id=user.id).exists()
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if (
            self.created_by
            and not self.teaching_assistants.filter(id=self.created_by.id).exists()
        ):
            self.teaching_assistants.add(self.created_by)

    def add_student(self, user):
        self.students.add(user)
        self.total_students = self.students.count()
        self.total_participants = self.total_students + self.total_teaching_assistants
        self.save()
