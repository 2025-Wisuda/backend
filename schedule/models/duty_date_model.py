from django.db import models
from core.models import BaseModel
from .duty_schedule_model import DutySchedule


class DutyDate(BaseModel):
    schedule = models.ForeignKey(
        DutySchedule,
        on_delete=models.CASCADE,
        related_name="duty_dates",
        verbose_name="Jadwal Piket",
    )
    duty_date = models.DateField(verbose_name="Tanggal Piket")

    class Meta:
        db_table = "duty_date"
        ordering = ["duty_date"]
        verbose_name = "Tanggal Piket"
        verbose_name_plural = "Tanggal Piket"
        unique_together = ("schedule", "duty_date")

    def __str__(self):
        return str(self.duty_date)
