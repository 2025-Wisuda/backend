from django.db import models
from django.conf import settings
from schedule.utils import generate_duty_dates
from datetime import time
from core.models import BaseModel


class DutySchedule(BaseModel):
    class Days(models.TextChoices):
        MONDAY = "monday", "Senin"
        TUESDAY = "tuesday", "Selasa"
        WEDNESDAY = "wednesday", "Rabu"
        THURSDAY = "thursday", "Kamis"
        FRIDAY = "friday", "Jumat"
        SATURDAY = "saturday", "Sabtu"
        SUNDAY = "sunday", "Minggu"

    teaching_assistants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="duty_schedules",
        blank=True,
        verbose_name="Asisten Laboratorium",
    )
    days = models.CharField(
        max_length=50, choices=Days.choices, blank=True, null=True, verbose_name="Hari"
    )
    start_date = models.DateField(blank=False, null=False, verbose_name="Tanggal Mulai")
    end_date = models.DateField(blank=False, null=False, verbose_name="Tanggal Selesai")
    start_time = models.TimeField(default=time(7, 30), verbose_name="Waktu Mulai")
    end_time = models.TimeField(default=time(16, 0), verbose_name="Waktu Selesai")

    class Meta:
        db_table = "duty_schedule"
        ordering = ["start_date"]
        verbose_name = "Jadwal Piket"
        verbose_name_plural = "Jadwal Piket"

    def assign_duty_dates(self):
        generate_duty_dates(self)

    def __str__(self):
        return f"{self.days} {self.start_time}–{self.end_time}"
