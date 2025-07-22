"""
Notification Scheduler Service

Handles automatic scheduling and sending of lab schedule notifications.
"""

import logging
from datetime import timedelta
from typing import Dict, List

from django.utils import timezone
from lab_schedule.models import LabScheduleModel

from .fcm_service_v2 import FCMService

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """
    Scheduler for automatic lab schedule notifications.
    """

    def __init__(self):
        """Initialize the notification scheduler"""
        self.fcm_service = FCMService()

    def get_upcoming_schedules(self, minutes_ahead: int = 15) -> List[LabScheduleModel]:
        """
        Get lab schedules that will start within the specified minutes.

        Args:
            minutes_ahead: Number of minutes to look ahead (default: 15)

        Returns:
            List of LabScheduleModel instances
        """
        now = timezone.localtime()
        check_time = now + timedelta(minutes=minutes_ahead)

        schedules = LabScheduleModel.objects.filter(
            is_active=True,
            date=check_time.date(),
            start_time__lte=check_time.time(),
            start_time__gte=(check_time - timedelta(minutes=5)).time(),
        ).select_related("created_by")

        logger.info(
            f"Found {schedules.count()} upcoming schedules in next {minutes_ahead} minutes"
        )
        return schedules

    def get_upcoming_duty_schedules(self, minutes_ahead: int = 15) -> List:
        """
        Get duty schedules that will start within the specified minutes.

        Args:
            minutes_ahead: Number of minutes to look ahead (default: 15)

        Returns:
            List of DutyAttendanceModel instances
        """
        now = timezone.localtime()
        check_time = now + timedelta(minutes=minutes_ahead)

        from duty_schedule.models import DutyAttendanceModel

        duty_schedules = DutyAttendanceModel.objects.filter(
            is_active=True,
            date=check_time.date(),
            start_time__lte=check_time.time(),
            start_time__gte=(check_time - timedelta(minutes=5)).time(),
        ).select_related("laboratory_assistant")

        logger.info(
            f"Found {duty_schedules.count()} upcoming duty schedules in next {minutes_ahead} minutes"
        )
        return duty_schedules

    def get_ending_duty_schedules(self, minutes_ahead: int = 15) -> List:
        """
        Get duty schedules that will end within the specified minutes.

        Args:
            minutes_ahead: Number of minutes to look ahead (default: 15)

        Returns:
            List of DutyAttendanceModel instances
        """
        now = timezone.localtime()
        check_time = now + timedelta(minutes=minutes_ahead)

        from duty_schedule.models import DutyAttendanceModel

        duty_schedules = DutyAttendanceModel.objects.filter(
            is_active=True,
            date=check_time.date(),
            end_time__lte=check_time.time(),
            end_time__gte=(check_time - timedelta(minutes=5)).time(),
        ).select_related("laboratory_assistant")

        logger.info(
            f"Found {duty_schedules.count()} ending duty schedules in next {minutes_ahead} minutes"
        )
        return duty_schedules

    def send_schedule_notifications(self, minutes_ahead: int = 15) -> Dict[str, int]:
        """
        Send notifications for upcoming lab schedules.

        Args:
            minutes_ahead: Number of minutes to look ahead

        Returns:
            Dict with success and failure counts
        """
        schedules = self.get_upcoming_schedules(minutes_ahead)

        success_count = 0
        failure_count = 0

        for schedule in schedules:
            try:
                success = self.fcm_service.send_schedule_notification(
                    user=schedule.created_by,
                    schedule=schedule,
                    notification_type="lab_schedule_start",
                )

                if success:
                    success_count += 1
                else:
                    failure_count += 1

            except Exception as e:
                logger.error(
                    f"Failed to send schedule notification for {schedule.id}: {e}"
                )
                failure_count += 1

        return {
            "success": success_count,
            "failure": failure_count,
            "total": len(schedules),
        }

    def send_duty_schedule_notifications(
        self, minutes_ahead: int = 15
    ) -> Dict[str, int]:
        """
        Send notifications for upcoming duty schedules.

        Args:
            minutes_ahead: Number of minutes to look ahead

        Returns:
            Dict with success and failure counts
        """
        from core.enums import NotificationTypeEnum

        # Start notifications
        start_schedules = self.get_upcoming_duty_schedules(minutes_ahead)
        success_count = 0
        failure_count = 0

        for duty_schedule in start_schedules:
            try:
                success = self.fcm_service.send_duty_schedule_notification(
                    duty_attendance=duty_schedule,
                    notification_type=NotificationTypeEnum.DUTY_SCHEDULE_START.value,
                )

                if success:
                    success_count += 1
                else:
                    failure_count += 1

            except Exception as e:
                logger.error(
                    f"Failed to send duty start notification for {duty_schedule.id}: {e}"
                )
                failure_count += 1

        # End notifications
        end_schedules = self.get_ending_duty_schedules(minutes_ahead)

        for duty_schedule in end_schedules:
            try:
                success = self.fcm_service.send_duty_schedule_notification(
                    duty_attendance=duty_schedule,
                    notification_type=NotificationTypeEnum.DUTY_SCHEDULE_END.value,
                )

                if success:
                    success_count += 1
                else:
                    failure_count += 1

            except Exception as e:
                logger.error(
                    f"Failed to send duty end notification for {duty_schedule.id}: {e}"
                )
                failure_count += 1

        return {
            "success": success_count,
            "failure": failure_count,
            "total": len(start_schedules) + len(end_schedules),
        }

    def send_all_notifications(self, minutes_ahead: int = 15) -> Dict[str, int]:
        """
        Send all types of notifications.

        Args:
            minutes_ahead: Number of minutes to look ahead

        Returns:
            Dict with total success and failure counts
        """
        schedule_results = self.send_schedule_notifications(minutes_ahead)
        duty_results = self.send_duty_schedule_notifications(minutes_ahead)

        return {
            "success": schedule_results["success"] + duty_results["success"],
            "failure": schedule_results["failure"] + duty_results["failure"],
            "total": schedule_results["total"] + duty_results["total"],
        }
