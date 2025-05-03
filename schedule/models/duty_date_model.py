from django.db import models
import uuid
from .duty_schedule_model import DutySchedule


class DutyDate(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID"
    )
    schedule = models.ForeignKey(
        DutySchedule,
        on_delete=models.CASCADE,
        related_name="duty_dates",
        verbose_name="Jadwal Piket",
    )
    duty_date = models.DateField(verbose_name="Tanggal Piket")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Dibuat")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Waktu Diperbarui")

    class Meta:
        db_table = "duty_date"
        ordering = ["duty_date"]
        verbose_name = "Tanggal Piket"
        verbose_name_plural = "Tanggal Piket"
        unique_together = ("schedule", "duty_date")

    def __str__(self):
        return str(self.duty_date)
