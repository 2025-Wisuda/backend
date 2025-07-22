"""
Notification Log Model

Logs all FCM notifications sent to users.
"""

from core import BaseModel
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class NotificationLogModel(BaseModel):
    """
    Model to log FCM notifications sent to users.

    Used for tracking delivery status and debugging.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_logs",
        verbose_name=_("User"),
        help_text=_("User who received the notification"),
    )

    schedule = models.ForeignKey(
        "lab_schedule.LabScheduleModel",
        on_delete=models.CASCADE,
        related_name="notification_logs",
        null=True,
        blank=True,
        verbose_name=_("Lab Schedule"),
        help_text=_("Lab schedule this notification is about"),
    )

    notification_type = models.CharField(
        max_length=50,
        choices=[
            ("lab_reminder", _("Lab Reminder")),
            ("schedule_change", _("Schedule Change")),
            ("cancellation", _("Cancellation")),
            ("general", _("General Notification")),
        ],
        default="lab_reminder",
        verbose_name=_("Notification Type"),
        help_text=_("Type of notification sent"),
    )

    title = models.CharField(
        max_length=200, verbose_name=_("Title"), help_text=_("Notification title")
    )

    body = models.TextField(
        verbose_name=_("Body"), help_text=_("Notification message body")
    )

    data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Data"),
        help_text=_("Additional data sent with notification"),
    )

    sent_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Sent At"),
        help_text=_("When the notification was sent"),
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", _("Pending")),
            ("sent", _("Sent")),
            ("failed", _("Failed")),
            ("partial", _("Partial Success")),
        ],
        default="pending",
        verbose_name=_("Status"),
        help_text=_("Delivery status of the notification"),
    )

    fcm_response = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("FCM Response"),
        help_text=_("Response from FCM service"),
    )

    devices_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Devices Count"),
        help_text=_("Number of devices notification was sent to"),
    )

    success_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Success Count"),
        help_text=_("Number of successful deliveries"),
    )

    failure_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Failure Count"),
        help_text=_("Number of failed deliveries"),
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name=_("Is Read"),
        help_text=_("Whether the user has read this notification"),
    )

    class Meta:
        db_table = "notification_logs"
        ordering = ["-sent_at"]
        verbose_name = _("Notification Log")
        verbose_name_plural = _("Notification Logs")

        indexes = [
            models.Index(fields=["user", "sent_at"]),
            models.Index(fields=["notification_type", "sent_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.status})"

    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.devices_count == 0:
            return 0
        return (self.success_count / self.devices_count) * 100

    def mark_as_sent(self, success_count=0, failure_count=0, fcm_response=None):
        """Mark notification as sent with results"""
        self.success_count = success_count
        self.failure_count = failure_count
        self.devices_count = success_count + failure_count

        if fcm_response:
            self.fcm_response = fcm_response

        if failure_count == 0:
            self.status = "sent"
        elif success_count == 0:
            self.status = "failed"
        else:
            self.status = "partial"

        self.save(
            update_fields=[
                "success_count",
                "failure_count",
                "devices_count",
                "fcm_response",
                "status",
            ]
        )

    def mark_as_failed(self, error_message=None):
        """Mark notification as failed"""
        self.status = "failed"
        if error_message:
            self.fcm_response = {"error": error_message}
        self.save(update_fields=["status", "fcm_response"])

    @classmethod
    def create_log(
        cls, user, title, body, notification_type="general", schedule=None, data=None
    ):
        """
        Create a new notification log entry.

        Args:
            user: User instance
            title: Notification title
            body: Notification body
            notification_type: Type of notification
            schedule: Lab schedule instance (optional)
            data: Additional data (optional)

        Returns:
            NotificationLogModel instance
        """
        return cls.objects.create(
            user=user,
            schedule=schedule,
            notification_type=notification_type,
            title=title,
            body=body,
            data=data or {},
        )
