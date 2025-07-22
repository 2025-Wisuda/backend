"""
Celery tasks for FCM notification system.
"""

import logging

from celery import shared_task
from fcm_notifications.services.notification_scheduler import NotificationScheduler

logger = logging.getLogger(__name__)


@shared_task
def send_lab_schedule_reminders(minutes_ahead: int = 15):
    """
    Send lab schedule reminders via FCM.

    Args:
        minutes_ahead: Number of minutes to look ahead for schedules
    """
    try:
        scheduler = NotificationScheduler()
        results = scheduler.send_all_notifications(minutes_ahead)

        logger.info(
            f"Lab schedule reminders sent: {results['success']} successful, "
            f"{results['failure']} failed, {results['total']} total"
        )

        return {
            "success": results["success"],
            "failure": results["failure"],
            "total": results["total"],
        }

    except Exception as e:
        logger.error(f"Failed to send lab schedule reminders: {e}")
        return {"success": 0, "failure": 1, "total": 0, "error": str(e)}


@shared_task
def test_lab_notification_system():
    """
    Test the lab notification system health.
    """
    try:
        scheduler = NotificationScheduler()

        # Test upcoming schedules
        upcoming_schedules = scheduler.get_upcoming_schedules(60)  # Check next hour
        duty_schedules = scheduler.get_upcoming_duty_schedules(60)

        logger.info(
            f"Notification system health check: "
            f"{upcoming_schedules.count()} lab schedules, "
            f"{duty_schedules.count()} duty schedules found"
        )

        return {
            "status": "healthy",
            "lab_schedules": upcoming_schedules.count(),
            "duty_schedules": duty_schedules.count(),
        }

    except Exception as e:
        logger.error(f"Notification system health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@shared_task
def send_room_booking_notification(booking_id: str, notification_type: str):
    """
    Send room booking notification.

    Args:
        booking_id: Room booking ID
        notification_type: Type of notification to send
    """
    try:
        from fcm_notifications.services.fcm_service_v2 import FCMService
        from room_booking.models import RoomBookingModel

        booking = RoomBookingModel.objects.get(id=booking_id)
        fcm_service = FCMService()

        success = fcm_service.send_room_booking_notification(
            booking=booking, notification_type=notification_type
        )

        logger.info(
            f"Room booking notification sent: {booking_id} "
            f"({notification_type}) - Success: {success}"
        )

        return {"success": success, "booking_id": booking_id}

    except Exception as e:
        logger.error(f"Failed to send room booking notification: {e}")
        return {"success": False, "error": str(e)}


@shared_task
def send_duty_schedule_notification(duty_id: str, notification_type: str):
    """
    Send duty schedule notification.

    Args:
        duty_id: Duty attendance ID
        notification_type: Type of notification to send
    """
    try:
        from duty_schedule.models import DutyAttendanceModel
        from fcm_notifications.services.fcm_service_v2 import FCMService

        duty_attendance = DutyAttendanceModel.objects.get(id=duty_id)
        fcm_service = FCMService()

        success = fcm_service.send_duty_schedule_notification(
            duty_attendance=duty_attendance, notification_type=notification_type
        )

        logger.info(
            f"Duty schedule notification sent: {duty_id} "
            f"({notification_type}) - Success: {success}"
        )

        return {"success": success, "duty_id": duty_id}

    except Exception as e:
        logger.error(f"Failed to send duty schedule notification: {e}")
        return {"success": False, "error": str(e)}
