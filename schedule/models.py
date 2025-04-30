import uuid
from django.db import models
from django.conf import settings


class LabSchedule(models.Model):
    class ActivityType(models.TextChoices):
        COURSE = "praktikum", "Praktikum"
        SEMINAR_PROPOSAL = "proposal", "Seminar Proposal"
        SEMINAR_HASIL = "Seminar Hasil"
        SEMINAR_KP = "Seminar KP"
        GENERAL = "lainnya", "Lainnya"

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID"
    )
    activity_type = models.CharField(
        max_length=50, choices=ActivityType.choices, verbose_name="Jenis Kegiatan"
    )
    activity_description = models.TextField(
        null=True, blank=True, verbose_name="Deskripsi Kegiatan"
    )
    schedule_date = models.DateField(verbose_name="Tanggal Jadwal")
    start_time = models.TimeField(verbose_name="Waktu Mulai")
    end_time = models.TimeField(verbose_name="Waktu Selesai")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lab_schedules",
        null=False,
        verbose_name="Dibuat Oleh",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Dibuat")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Waktu Diperbarui")

    class Meta:
        db_table = "lab_schedule"
        ordering = ["schedule_date", "start_time"]
        verbose_name = "Jadwal Lab"
        verbose_name_plural = "Jadwal Lab"

    def __str__(self):
        return f"{self.created_by} - {self.get_activity_type_display()}"
