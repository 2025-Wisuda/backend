import uuid
from django.db import models
from django.conf import settings


class LabSchedule(models.Model):
    class ActivityType(models.TextChoices):
        COURSE = "praktikum", "Praktikum"
        SEMINAR_PROPOSAL = "proposal", "Seminar Proposal"
        SEMINAR_HASIL = "hasil", "Seminar Hasil"
        SEMINAR_KP = "kp", "Seminar KP"
        GENERAL = "lainnya", "Lainnya"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity_type = models.CharField(max_length=50, choices=ActivityType.choices)
    activity_description = models.TextField(null=True, blank=True)
    schedule_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lab_schedules",
        null=False,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lab_schedule"
        ordering = ["schedule_date", "start_time"]
        verbose_name = "Lab Schedule"
        verbose_name_plural = "Lab Schedules"

    def __str__(self):
        return f"{self.schedule_date} - {self.get_activity_type_display()}"
