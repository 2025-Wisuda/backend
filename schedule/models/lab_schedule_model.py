from django.db import models
from django.conf import settings
from datetime import datetime
from core.models import BaseModel


class LabSchedule(BaseModel):
    class ActivityType(models.TextChoices):
        PRACTICUM = "praktikum", "Praktikum"
        PROPOSAL_SEMINAR = "proposal", "Seminar Proposal"
        RESULT_SEMINAR = "hasil", "Seminar Hasil"
        INTERNSHIP_SEMINAR = "kp", "Seminar KP"
        OTHER = "lainnya", "Lainnya"

    class ApprovalStatus(models.TextChoices):
        PENDING = "menunggu", "Menunggu"
        APPROVED = "diterima", "Diterima"
        REJECTED = "ditolak", "Ditolak"

    activity_type = models.CharField(
        max_length=50,
        choices=ActivityType.choices,
        verbose_name="Jenis Kegiatan",
    )
    activity_description = models.TextField(
        null=True, blank=True, verbose_name="Deskripsi Kegiatan"
    )
    schedule_date = models.DateField(null=True, blank=True, verbose_name="Tanggal Jadwal")
    start_time = models.TimeField(null=True, blank=True, verbose_name="Waktu Mulai")
    end_time = models.TimeField(null=True, blank=True, verbose_name="Waktu Selesai")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lab_schedules",
        null=False,
        verbose_name="Dibuat Oleh",
    )
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        verbose_name="Status Persetujuan",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_lab_schedules",
        verbose_name="Disetujui Oleh",
    )
    approval_time = models.DateTimeField(
        null=True, blank=True, verbose_name="Waktu Persetujuan"
    )

    class Meta:
        db_table = "lab_schedule"
        ordering = ["schedule_date", "start_time"]
        verbose_name = "Jadwal Lab"
        verbose_name_plural = "Jadwal Lab"

    def __str__(self):
        return f"{self.created_by} - {self.get_activity_type_display()}"
