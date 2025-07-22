"""
FCM Service V2

Handles Firebase Cloud Messaging operations using Firebase Admin SDK V1 API.
"""

import logging
from typing import Any, Dict, List, Optional

import firebase_admin
from django.conf import settings
from firebase_admin import credentials, messaging

from ..models import FCMDeviceModel, NotificationLogModel

logger = logging.getLogger(__name__)


class FCMService:
    """
    Service class for Firebase Cloud Messaging operations using Admin SDK V1.
    """

    def __init__(self):
        """Initialize Firebase Admin SDK"""
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK if not already initialized"""
        try:
            # Check if Firebase is already initialized
            firebase_admin.get_app()
            logger.info("Firebase Admin SDK already initialized")
        except ValueError:
            # Initialize Firebase Admin SDK
            try:
                cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
                firebase_admin.initialize_app(
                    cred, {"projectId": settings.FCM_PROJECT_ID}
                )
                logger.info("Firebase Admin SDK initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
                raise

    def send_lab_reminder(self, user, schedule, custom_message=None):
        """
        Send lab schedule reminder to user's devices.

        Args:
            user: User instance
            schedule: LabScheduleModel instance
            custom_message: Optional custom message

        Returns:
            NotificationLogModel instance
        """
        try:
            # Get active device tokens
            tokens = FCMDeviceModel.get_active_tokens_for_user(user)

            if not tokens:
                logger.warning(f"No active FCM tokens for user {user.username}")
                return None

            # Prepare notification content
            title = "Lab Reminder"
            body = custom_message or self._generate_lab_reminder_message(schedule)

            # Additional data for mobile app
            data = {
                "type": "lab_reminder",
                "schedule_id": str(schedule.pk),
                "schedule_date": schedule.date.isoformat(),
                "start_time": schedule.start_time.isoformat(),
                "end_time": schedule.end_time.isoformat(),
                "activity_type": schedule.type,
                "source_model": schedule.source_model,
            }

            # Create notification log
            log = NotificationLogModel.create_log(
                user=user,
                schedule=schedule,
                title=title,
                body=body,
                notification_type="lab_reminder",
                data=data,
            )

            # Send notification using Firebase Admin SDK
            success_count, failure_count, fcm_response = self._send_multicast_message(
                tokens=tokens, title=title, body=body, data=data
            )

            # Update log with results
            log.mark_as_sent(
                success_count=success_count,
                failure_count=failure_count,
                fcm_response=fcm_response,
            )

            logger.info(
                f"Lab reminder sent to {user.username}: "
                f"{success_count} success, {failure_count} failed"
            )

            return log

        except Exception as e:
            logger.error(f"Failed to send lab reminder to {user.username}: {e}")
            if "log" in locals():
                log.mark_as_failed(str(e))
                return log
            return None

    def send_bulk_reminders(self, notifications_data: List[Dict[str, Any]]):
        """
        Send multiple notifications efficiently.

        Args:
            notifications_data: List of notification data dicts
                Each dict should contain: user, schedule, message (optional)

        Returns:
            List of NotificationLogModel instances
        """
        results = []

        for notification in notifications_data:
            user = notification["user"]
            schedule = notification["schedule"]
            message = notification.get("message")

            result = self.send_lab_reminder(user, schedule, message)
            if result:
                results.append(result)

        return results

    def register_device(
        self, user, token: str, device_type: str = "android", device_name: str = None
    ):
        """
        Register user's device for FCM notifications.

        Args:
            user: User instance
            token: FCM registration token
            device_type: Type of device ('android', 'ios', 'web')
            device_name: Optional device name

        Returns:
            FCMDeviceModel instance
        """
        try:
            device = FCMDeviceModel.register_device(
                user=user, token=token, device_type=device_type, device_name=device_name
            )

            logger.info(f"FCM device registered for {user.username}: {device_type}")
            return device

        except Exception as e:
            logger.error(f"Failed to register FCM device for {user.username}: {e}")
            raise

    def unregister_device(self, token: str):
        """
        Unregister (deactivate) a device token.

        Args:
            token: FCM registration token to unregister

        Returns:
            bool: True if successful
        """
        try:
            devices = FCMDeviceModel.objects.filter(registration_token=token)

            if devices.exists():
                devices.update(is_active=False)
                logger.info(f"FCM device unregistered: {token[:20]}...")
                return True
            else:
                logger.warning(f"FCM device not found for token: {token[:20]}...")
                return False

        except Exception as e:
            logger.error(f"Failed to unregister FCM device: {e}")
            return False

    def send_schedule_change_notification(self, user, schedule, change_type="modified"):
        """
        Send notification about schedule changes.

        Args:
            user: User instance
            schedule: LabScheduleModel instance
            change_type: Type of change ('modified', 'cancelled', 'rescheduled')

        Returns:
            NotificationLogModel instance
        """
        try:
            # Get device tokens
            tokens = FCMDeviceModel.get_active_tokens_for_user(user)
            if not tokens:
                return None

            # Prepare content
            title_map = {
                "modified": "Schedule Modified",
                "cancelled": "Schedule Cancelled",
                "rescheduled": "Schedule Rescheduled",
            }

            title = title_map.get(change_type, "Schedule Update")
            body = self._generate_schedule_change_message(schedule, change_type)

            data = {
                "type": "schedule_change",
                "change_type": change_type,
                "schedule_id": str(schedule.pk),
                "schedule_date": schedule.date.isoformat(),
                "start_time": schedule.start_time.isoformat(),
                "end_time": schedule.end_time.isoformat(),
            }

            # Create log and send
            log = NotificationLogModel.create_log(
                user=user,
                schedule=schedule,
                title=title,
                body=body,
                notification_type="schedule_change",
                data=data,
            )

            success_count, failure_count, fcm_response = self._send_multicast_message(
                tokens=tokens, title=title, body=body, data=data
            )

            log.mark_as_sent(success_count, failure_count, fcm_response)

            return log

        except Exception as e:
            logger.error(f"Failed to send schedule change notification: {e}")
            if "log" in locals():
                log.mark_as_failed(str(e))
                return log
            return None

    def test_notification(
        self,
        user,
        test_message=None,
        title=None,
    ):
        """
        Send test notification to user.

        Args:
            user: User instance
            test_message: Test message to send (optional, uses default if None)
            title: Notification title (optional, uses default if None)

        Returns:
            bool: True if successful
        """
        from django.utils.translation import gettext as _

        # Use default messages if not provided
        if test_message is None:
            test_message = _("Test notification from Lab Management")
        if title is None:
            title = _("Test Notification")
        try:
            tokens = FCMDeviceModel.get_active_tokens_for_user(user)
            success_count = 0
            failure_count = 0

            if not tokens:
                logger.warning(f"No active tokens for user {user.username}")
                # Still create log even if no tokens
                failure_count = 1
            else:
                # Send to each token individually (more reliable than multicast)
                for token in tokens:
                    result = self.send_notification(
                        token=token,
                        title=title,
                        body=test_message,
                        data={"type": "test"},
                    )

                    if result["success"]:
                        success_count += 1
                    else:
                        failure_count += 1
                        logger.warning(
                            f"Failed to send to token {token[:20]}...: {result.get('error')}"
                        )

            logger.info(
                f"Test notification sent to {user.username}: {success_count} successful, {failure_count} failed"
            )

            # Log notification to database (ALWAYS log, regardless of FCM success)
            from django.utils import timezone
            from fcm_notifications.models import NotificationLogModel

            try:
                NotificationLogModel.objects.create(
                    user=user,
                    title=title,
                    body=test_message,
                    notification_type="test",
                    data={
                        "sent_at": timezone.localtime().isoformat(),
                        "fcm_success": success_count > 0,
                    },
                    status="sent" if success_count > 0 else "failed",
                    success_count=success_count,
                    failure_count=failure_count,
                    devices_count=success_count + failure_count,
                )
                logger.info(
                    f"Test notification logged for user {user.username} (status: {'sent' if success_count > 0 else 'failed'})"
                )
            except Exception as log_error:
                logger.error(
                    f"Failed to log test notification for {user.username}: {log_error}"
                )

            return success_count > 0

        except Exception as e:
            logger.error(f"Failed to send test notification: {e}")
            return False

    def is_configured(self):
        """Check if Firebase Admin SDK is properly configured"""
        try:
            firebase_admin.get_app()
            return True
        except ValueError:
            return False

    def _send_multicast_message(
        self, tokens: List[str], title: str, body: str, data: Dict[str, str]
    ):
        """
        Send notification to multiple tokens using Firebase Admin SDK.

        Args:
            tokens: List of FCM registration tokens
            title: Notification title
            body: Notification body
            data: Additional data

        Returns:
            tuple: (success_count, failure_count, response_data)
        """
        try:
            # Create message
            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data=data,
                tokens=tokens,
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        sound="default", click_action="FLUTTER_NOTIFICATION_CLICK"
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound="default", badge=1)
                    )
                ),
            )

            # Send message
            response = messaging.send_multicast(message)

            success_count = response.success_count
            failure_count = response.failure_count

            # Handle failed tokens
            if failure_count > 0:
                self._handle_failed_tokens(response.responses, tokens)

            # Prepare response data
            response_data = {
                "success_count": success_count,
                "failure_count": failure_count,
                "multicast_id": getattr(response, "multicast_id", None),
                "responses": [
                    {
                        "success": resp.success,
                        "message_id": resp.message_id if resp.success else None,
                        "error": str(resp.exception) if resp.exception else None,
                    }
                    for resp in response.responses
                ],
            }

            return success_count, failure_count, response_data

        except Exception as e:
            logger.error(f"Failed to send multicast message: {e}")
            return 0, len(tokens), {"error": str(e)}

    def _handle_failed_tokens(self, responses, tokens):
        """Handle failed FCM tokens by deactivating invalid ones"""
        for i, response in enumerate(responses):
            if not response.success and response.exception:
                error_code = (
                    response.exception.code
                    if hasattr(response.exception, "code")
                    else str(response.exception)
                )
                token = tokens[i]

                # Deactivate tokens with permanent errors
                if "NOT_FOUND" in error_code or "INVALID_ARGUMENT" in error_code:
                    logger.info(f"Deactivating invalid FCM token: {token[:20]}...")
                    try:
                        device = FCMDeviceModel.objects.get(registration_token=token)
                        device.deactivate()
                    except FCMDeviceModel.DoesNotExist:
                        pass

    def _generate_lab_reminder_message(self, schedule):
        """Generate reminder message for lab schedule"""
        from django.utils.translation import gettext as _

        time_str = f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}"
        return _("Your {activity_type} is starting soon at {time}. {detail}").format(
            activity_type=schedule.type, time=time_str, detail=schedule.detail or ""
        )

    def _generate_schedule_change_message(self, schedule, change_type):
        """Generate message for schedule changes"""
        from django.utils.translation import gettext as _

        time_str = f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}"

        if change_type == "cancelled":
            return _(
                "Your {activity_type} scheduled for {time} has been cancelled."
            ).format(activity_type=schedule.type, time=time_str)
        elif change_type == "rescheduled":
            return _("Your {activity_type} has been rescheduled to {time}.").format(
                activity_type=schedule.type, time=time_str
            )
        else:
            return _("Your {activity_type} at {time} has been modified.").format(
                activity_type=schedule.type, time=time_str
            )

    def send_notification(self, token, title, body, data=None):
        """
        Send simple FCM notification to a specific token.

        Args:
            token (str): FCM registration token
            title (str): Notification title
            body (str): Notification body
            data (dict): Optional data payload

        Returns:
            dict: Result of sending notification
        """
        try:
            # Create FCM message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=token,
            )

            # Send the message
            response = messaging.send(message)

            logger.info(f"FCM notification sent successfully. Response: {response}")
            return {
                "success": True,
                "response": response,
            }
        except ValueError as e:
            logger.error(f"Invalid FCM argument: {e}")
            return {
                "success": False,
                "error": f"Invalid argument: {str(e)}",
            }
        except messaging.UnregisteredError as e:
            logger.warning(f"FCM token unregistered: {e}")
            # Mark token as inactive
            try:
                devices = FCMDeviceModel.objects.filter(registration_token=token)
                for device in devices:
                    device.is_active = False
                    device.save()
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up unregistered token: {cleanup_error}")
            return {
                "success": False,
                "error": f"Token unregistered: {str(e)}",
            }
        except Exception as e:
            logger.error(f"Error sending FCM notification: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def send_schedule_notification(
        self, user, schedule, notification_type="schedule_reminder"
    ):
        """
        Send natural notification for lab schedules with proper formatting.

        Args:
            user: User instance
            schedule: LabScheduleModel instance
            notification_type: Type of notification

        Returns:
            bool: True if successful
        """
        try:
            tokens = FCMDeviceModel.get_active_tokens_for_user(user)
            if not tokens:
                logger.warning(f"No active tokens for user {user.username}")
                return False

            # Generate natural notification message based on schedule type
            title, body = self._generate_natural_schedule_message(schedule)

            success_count = 0
            failure_count = 0

            # Send to each token individually
            for token in tokens:
                result = self.send_notification(
                    token=token,
                    title=title,
                    body=body,
                    data={
                        "type": notification_type,
                        "schedule_id": str(schedule.id),
                        "source_model": schedule.source_model,
                    },
                )

                if result["success"]:
                    success_count += 1
                else:
                    failure_count += 1
                    logger.warning(
                        f"Failed to send to token {token[:20]}...: {result.get('error')}"
                    )

            logger.info(
                f"Schedule notification sent to {user.username}: {success_count} successful, {failure_count} failed"
            )

            # Log notification to database
            if success_count > 0:
                from django.utils import timezone
                from fcm_notifications.models import NotificationLogModel

                try:
                    NotificationLogModel.objects.create(
                        user=user,
                        title=title,
                        body=body,
                        notification_type=notification_type,
                        data={
                            "schedule_id": str(schedule.id),
                            "source_model": schedule.source_model,
                            "sent_at": timezone.localtime().isoformat(),
                            "fcm_success": success_count > 0,
                        },
                        status="sent" if success_count > 0 else "failed",
                        success_count=success_count,
                        failure_count=failure_count,
                        devices_count=success_count + failure_count,
                    )
                    logger.info(
                        f"Schedule notification logged for user {user.username}"
                    )
                except Exception as log_error:
                    logger.error(
                        f"Failed to log schedule notification for {user.username}: {log_error}"
                    )

            return success_count > 0

        except Exception as e:
            logger.error(f"Failed to send schedule notification: {e}")
            return False

    def _generate_natural_schedule_message(self, schedule):
        """
        Generate natural notification message based on schedule type.

        Args:
            schedule: LabScheduleModel instance

        Returns:
            tuple: (title, body)
        """
        from django.utils.translation import gettext as _

        time_str = f"{schedule.start_time.strftime('%H:%M')} - {schedule.end_time.strftime('%H:%M')}"

        if schedule.source_model == "RoomBooking":
            # Room booking notification
            title = _("🏢 You have a room booking")
            body = _("{booking_type} at {time}").format(
                booking_type=schedule.type, time=time_str
            )

            if schedule.detail:
                body += f"\n{_('📝 Detail')}: {schedule.detail}"

                # Add motivational text for room bookings
            if "seminar" in schedule.type.lower():
                body += f"\n\n{_('💪 Good luck with your presentation!')}"
            elif "meeting" in schedule.type.lower():
                body += f"\n\n{_('🤝 Have a productive meeting!')}"
            else:
                body += f"\n\n{_('✨ Have a great session!')}"

        elif schedule.source_model == "CourseSession":
            # Course session notification
            title = _("📚 You have a course session")
            body = _("{course_title} at {time}").format(
                course_title=schedule.type, time=time_str
            )

            if schedule.detail:
                body += f"\n{_('📖 Session')}: {schedule.detail}"

            # Add campus-style reminder
            body += f"\n\n{_('⏰ Don\'t be late!')}"

        elif schedule.source_model == "LabAllocation":
            # Lab allocation notification
            title = _("🧪 You have a lab activity")
            body = _("{activity_type} at {time}").format(
                activity_type=schedule.type, time=time_str
            )

            if schedule.detail:
                body += f"\n{_('🔬 Description')}: {schedule.detail}"

            # Add lab-specific motivation
            body += f"\n\n{_('🔬 Ready to experiment!')}"

        else:
            # Generic notification
            title = _("📅 You have a scheduled activity")
            body = _("{activity_type} at {time}").format(
                activity_type=schedule.type, time=time_str
            )

            if schedule.detail:
                body += f"\n{_('📝 Detail')}: {schedule.detail}"

            # Add generic motivation
            body += f"\n\n{_('🚀 You got this!')}"

        return title, body

    def send_room_booking_notification(
        self, booking, notification_type, recipients=None
    ):
        """
        Send room booking notification to appropriate recipients.

        Args:
            booking: RoomBookingModel instance
            notification_type: NotificationTypeEnum value
            recipients: List of users to notify (if None, uses default logic)

        Returns:
            bool: True if successful
        """
        from core.enums import NotificationTypeEnum
        from django.utils.translation import gettext as _

        try:
            # Determine recipients based on notification type
            if recipients is None:
                if notification_type == NotificationTypeEnum.ROOM_BOOKING_CREATED.value:
                    # Notify technicians and lab heads
                    from core.enums import UserGroup
                    from django.contrib.auth import get_user_model

                    UserModel = get_user_model()
                    recipients = UserModel.objects.filter(
                        groups__name__in=UserGroup.laboratory_staff_employee_groups()
                    )
                else:
                    # Notify the booker
                    recipients = [booking.booker]

            # Generate notification message
            title, body = self._generate_room_booking_notification_message(
                booking, notification_type
            )

            success_count = 0
            failure_count = 0

            # Send to each recipient
            for user in recipients:
                tokens = FCMDeviceModel.get_active_tokens_for_user(user)
                if not tokens:
                    logger.warning(f"No active tokens for user {user.username}")
                    continue

                for token in tokens:
                    result = self.send_notification(
                        token=token,
                        title=title,
                        body=body,
                        data={
                            "type": notification_type,
                            "booking_id": str(booking.id),
                            "source_model": "RoomBooking",
                        },
                    )

                    if result["success"]:
                        success_count += 1
                    else:
                        failure_count += 1
                        logger.warning(
                            f"Failed to send to token {token[:20]}...: {result.get('error')}"
                        )

            logger.info(
                f"Room booking notification sent: {success_count} successful, {failure_count} failed"
            )

            # Log notifications to database (ALWAYS log, regardless of FCM success)
            from django.utils import timezone
            from fcm_notifications.models import NotificationLogModel

            for user in recipients:
                try:
                    NotificationLogModel.objects.create(
                        user=user,
                        title=title,
                        body=body,
                        notification_type=notification_type,
                        data={
                            "booking_id": str(booking.id),
                            "source_model": "RoomBooking",
                            "sent_at": timezone.localtime().isoformat(),
                            "fcm_success": success_count > 0,
                        },
                        status="sent" if success_count > 0 else "failed",
                        success_count=success_count,
                        failure_count=failure_count,
                        devices_count=success_count + failure_count,
                    )
                    logger.info(
                        f"Notification logged for user {user.username} (status: {'sent' if success_count > 0 else 'failed'})"
                    )
                except Exception as log_error:
                    logger.error(
                        f"Failed to log notification for {user.username}: {log_error}"
                    )

            return success_count > 0

        except Exception as e:
            logger.error(f"Failed to send room booking notification: {e}")
            return False

    def _generate_room_booking_notification_message(self, booking, notification_type):
        """
        Generate room booking notification message.

        Args:
            booking: RoomBookingModel instance
            notification_type: NotificationTypeEnum value

        Returns:
            tuple: (title, body)
        """
        from core.enums import NotificationTypeEnum
        from django.utils.translation import activate
        from django.utils.translation import gettext as _

        # Set translation context to Indonesian
        activate("id")

        # Handle time formatting safely
        if hasattr(booking.start_time, "strftime"):
            start_time_str = booking.start_time.strftime("%H:%M")
        else:
            start_time_str = str(booking.start_time)

        if hasattr(booking.end_time, "strftime"):
            end_time_str = booking.end_time.strftime("%H:%M")
        else:
            end_time_str = str(booking.end_time)

        time_str = f"{start_time_str} - {end_time_str}"

        # Handle date formatting safely
        if hasattr(booking.date, "strftime"):
            date_str = booking.date.strftime("%d %B %Y")
        else:
            date_str = str(booking.date)

        if notification_type == NotificationTypeEnum.ROOM_BOOKING_CREATED.value:
            # Notify technicians about new booking
            title = _("🏢 New room booking request")
            body = _(
                "{booker_name} requested {booking_type} on {date} at {time}"
            ).format(
                booker_name=booking.booker.get_full_name() or booking.booker.username,
                booking_type=booking.booking_type,
                date=date_str,
                time=time_str,
            )

            if booking.purpose:
                body += f"\n{_('📝 Purpose')}: {booking.purpose}"

            body += f"\n\n{_('🔍 Please review and approve/reject')}"

        elif notification_type == NotificationTypeEnum.ROOM_BOOKING_APPROVED.value:
            # Notify booker about approval
            title = _("✅ Room booking approved!")
            body = _(
                "Your {booking_type} on {date} at {time} has been approved"
            ).format(booking_type=booking.booking_type, date=date_str, time=time_str)

            if booking.approval_notes:
                body += f"\n{_('📝 Note')}: {booking.approval_notes}"

            body += f"\n\n{_('🎉 You can now use the room!')}"

        elif notification_type == NotificationTypeEnum.ROOM_BOOKING_REJECTED.value:
            # Notify booker about rejection
            title = _("❌ Room booking rejected")
            body = _(
                "Your {booking_type} on {date} at {time} has been rejected"
            ).format(booking_type=booking.booking_type, date=date_str, time=time_str)

            if booking.approval_notes:
                body += f"\n{_('📝 Reason')}: {booking.approval_notes}"

            body += f"\n\n{_('💡 Please check for conflicts or contact lab staff')}"

        return title, body

    def send_duty_schedule_notification(self, duty_attendance, notification_type):
        """
        Send duty schedule notification.

        Args:
            duty_attendance: DutyAttendanceModel instance
            notification_type: NotificationTypeEnum value

        Returns:
            bool: True if successful
        """
        try:
            user = duty_attendance.laboratory_assistant
            tokens = FCMDeviceModel.get_active_tokens_for_user(user)
            if not tokens:
                logger.warning(f"No active tokens for user {user.username}")
                return False

            # Generate notification message
            title, body = self._generate_duty_schedule_notification_message(
                duty_attendance, notification_type
            )

            success_count = 0
            failure_count = 0

            # Send to each token
            for token in tokens:
                result = self.send_notification(
                    token=token,
                    title=title,
                    body=body,
                    data={
                        "type": notification_type,
                        "duty_id": str(duty_attendance.id),
                        "source_model": "DutyAttendance",
                    },
                )

                if result["success"]:
                    success_count += 1
                else:
                    failure_count += 1
                    logger.warning(
                        f"Failed to send to token {token[:20]}...: {result.get('error')}"
                    )

            logger.info(
                f"Duty schedule notification sent to {user.username}: {success_count} successful, {failure_count} failed"
            )

            # Log notification to database (ALWAYS log, regardless of FCM success)
            from django.utils import timezone
            from fcm_notifications.models import NotificationLogModel

            try:
                NotificationLogModel.objects.create(
                    user=user,
                    title=title,
                    body=body,
                    notification_type=notification_type,
                    data={
                        "duty_id": str(duty_attendance.id),
                        "source_model": "DutyAttendance",
                        "sent_at": timezone.localtime().isoformat(),
                        "fcm_success": success_count > 0,
                    },
                    status="sent" if success_count > 0 else "failed",
                    success_count=success_count,
                    failure_count=failure_count,
                    devices_count=success_count + failure_count,
                )
                logger.info(
                    f"Duty notification logged for user {user.username} (status: {'sent' if success_count > 0 else 'failed'})"
                )
            except Exception as log_error:
                logger.error(
                    f"Failed to log duty notification for {user.username}: {log_error}"
                )

            return success_count > 0

        except Exception as e:
            logger.error(f"Failed to send duty schedule notification: {e}")
            return False

    def _generate_duty_schedule_notification_message(
        self, duty_attendance, notification_type
    ):
        """
        Generate duty schedule notification message.

        Args:
            duty_attendance: DutyAttendanceModel instance
            notification_type: NotificationTypeEnum value

        Returns:
            tuple: (title, body)
        """
        from core.enums import NotificationTypeEnum
        from django.utils.translation import gettext as _

        time_str = f"{duty_attendance.start_time.strftime('%H:%M')} - {duty_attendance.end_time.strftime('%H:%M')}"
        date_str = duty_attendance.date.strftime("%d %B %Y")

        if notification_type == NotificationTypeEnum.DUTY_SCHEDULE_START.value:
            title = _("🕐 Your duty starts soon")
            body = _("Duty schedule on {date} at {time}").format(
                date=date_str, time=time_str
            )

            body += f"\n\n{_('👨‍💼 Time to assist students!')}"

        elif notification_type == NotificationTypeEnum.DUTY_SCHEDULE_END.value:
            title = _("⏰ Duty ending soon")
            body = _("Your duty on {date} ends at {end_time}").format(
                date=date_str, end_time=duty_attendance.end_time.strftime("%H:%M")
            )

            body += f"\n\n{_('📊 Don\'t forget to complete your tasks!')}"

        return title, body
