import uuid
from django.db import models
from django.conf import settings
from datetime import datetime


class LabSchedule(models.Model):
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

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID"
    )
    activity_type = models.CharField(
        max_length=50,
        choices=ActivityType.choices,
        verbose_name="Jenis Kegiatan",
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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Dibuat")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Waktu Diperbarui")

    class Meta:
        db_table = "lab_schedule"
        ordering = ["schedule_date", "start_time"]
        verbose_name = "Jadwal Lab"
        verbose_name_plural = "Jadwal Lab"

    def save(self, *args, **kwargs):
        if (
            not self.pk
            and self.created_by
            and (self.created_by.is_staff or self.created_by.is_superuser)
        ):
            self.approval_status = self.ApprovalStatus.APPROVED
            self.approved_by = self.created_by
            self.approval_time = datetime.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.created_by} - {self.get_activity_type_display()}"
