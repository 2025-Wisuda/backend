"""
WebSocket Consumer for Duty Attendance.

Face recognition attendance for laboratory assistants.
Assistants connect via WebSocket for real-time communication.
"""

import json
import logging
import uuid
from datetime import datetime

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from core.enums import AttendanceStatus, UserGroup
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import DutyAttendanceModel, DutyScheduleModel
from .services.duty_face_recognition_service import DutyFaceRecognitionService

User = get_user_model()
logger = logging.getLogger(__name__)


class DutyAttendanceConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for duty attendance operations.

    Handles:
    1. Face recognition attendance for laboratory assistants
    2. Real-time status updates for admins
    3. OTP validation (via REST API)
    """

    async def connect(self):
        """Accept WebSocket connection and setup user session."""
        self.user = self.scope["user"]

        # Only authenticated users can connect
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Join user-specific group for personal updates
        self.user_group = f"duty_attendance_user_{self.user.id}"
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        # Join general duty attendance group
        await self.channel_layer.group_add("duty_attendance", self.channel_name)

        await self.accept()

        # Send welcome message with current status
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "message": "Connected to duty attendance service",
                    "user_id": str(self.user.id),
                    "username": self.user.username,
                    "timestamp": timezone.localtime().isoformat(),
                }
            )
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave groups
        await self.channel_layer.group_discard(self.user_group, self.channel_name)
        await self.channel_layer.group_discard("duty_attendance", self.channel_name)

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            # Route to appropriate handler
            if message_type == "face_recognition":
                await self.handle_face_recognition(data)
            elif message_type == "get_attendance":
                await self.handle_get_attendance(data)
            else:
                await self.send_error("Unknown message type", 400)

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format", 400)
        except Exception as e:
            await self.send_error(f"Server error: {str(e)}", 500)

    # =========================================================================
    # FACE RECOGNITION ATTENDANCE (USING GENERIC SERVICE)
    # =========================================================================

    async def handle_face_recognition(self, data):
        """
        Handle face recognition attendance request using generic service.

        Message format:
        {
            "type": "face_recognition",
            "attendance_id": "uuid",
            "image": "base64_string",
            "action": "clock_in" | "clock_out",
            "request_id": "uuid"
        }
        """
        # Use generic face recognition service
        service = DutyFaceRecognitionService(self)
        await service.handle_face_recognition_request(data)

    # =========================================================================
    # ATTENDANCE MANAGEMENT
    # =========================================================================

    async def handle_get_attendance(self, data):
        """
        Get attendance records for the connected user.

        Message format:
        {
            "type": "get_attendance",
            "date": "YYYY-MM-DD",  # Optional, defaults to today
            "request_id": "uuid"
        }
        """
        date_str = data.get("date")
        request_id = data.get("request_id", str(uuid.uuid4()))

        try:
            # Parse date or use today
            if date_str:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            else:
                target_date = timezone.localtime().date()

            # Get attendance records for user
            attendances = await sync_to_async(list)(
                DutyAttendanceModel.objects.filter(
                    laboratory_assistant=self.user, date=target_date, is_active=True
                )
                .select_related("duty_schedule")
                .order_by("duty_schedule__start_time")
            )

            # Serialize attendance data
            attendance_list = []
            for attendance in attendances:
                schedule = attendance.duty_schedule
                attendance_data = {
                    "id": str(attendance.id),
                    "date": attendance.date.isoformat(),
                    "start_time": schedule.start_time.isoformat(),
                    "end_time": schedule.end_time.isoformat(),
                    "status": attendance.status,
                    "clock_in_time": (
                        attendance.clock_in_time.isoformat()
                        if attendance.clock_in_time
                        else None
                    ),
                    "clock_out_time": (
                        attendance.clock_out_time.isoformat()
                        if attendance.clock_out_time
                        else None
                    ),
                    "can_clock_in": attendance.can_clock_in(),
                    "can_clock_out": attendance.can_clock_out(),
                    "is_otp_validated": attendance.is_otp_validated(),
                    "confidence": attendance.get_confidence_percentage(),
                }
                attendance_list.append(attendance_data)

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "attendance_list",
                        "request_id": request_id,
                        "date": target_date.isoformat(),
                        "attendances": attendance_list,
                        "timestamp": timezone.localtime().isoformat(),
                    }
                )
            )

        except ValueError:
            await self.send_error(
                "Invalid date format. Use YYYY-MM-DD", 400, request_id
            )
        except Exception as e:
            await self.send_error(
                f"Failed to get attendance: {str(e)}", 500, request_id
            )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    async def send_error(self, message, code=400, request_id=None):
        """Send error message to client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": message,
                    "code": code,
                    "request_id": request_id,
                    "timestamp": timezone.localtime().isoformat(),
                }
            )
        )

    async def send_enhanced_error(
        self,
        message,
        code=400,
        request_id=None,
        fr_result=None,
        action=None,
        attendance_id=None,
        extra_data=None,
    ):
        """Send enhanced error message with face recognition details."""
        error_response = {
            "type": "face_recognition_error",
            "message": message,
            "code": code,
            "request_id": request_id,
            "timestamp": timezone.localtime().isoformat(),
        }

        # Add action and attendance context if available
        if action:
            error_response["action"] = action
        if attendance_id:
            error_response["attendance_id"] = attendance_id

        # Add face recognition details if available
        if fr_result:
            error_response["face_recognition_details"] = {
                "success": fr_result.get("success", False),
                "person_id": fr_result.get("person_id"),
                "confidence": fr_result.get("confidence", 0.0),
                "confidence_percentage": round(
                    fr_result.get("confidence", 0.0) * 100, 1
                ),
                "threshold": fr_result.get("threshold", 0.7),
                "message": fr_result.get("message", ""),
                "attendance_type": fr_result.get("attendance_type"),
                "error": fr_result.get("error"),
            }

        # Add extra data if provided
        if extra_data:
            error_response.update(extra_data)

        await self.send(text_data=json.dumps(error_response))

    # Group message handlers
    async def attendance_update(self, event):
        """Handle attendance update broadcast."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "attendance_update_broadcast",
                    "attendance_id": event["attendance_id"],
                    "assistant_id": event["assistant_id"],  # Consistent field name
                    "status": event["status"],
                    "confidence": event.get("confidence"),
                    "timestamp": timezone.localtime().isoformat(),
                }
            )
        )

    # Handler for face recognition result broadcast by FaceRecognitionServiceConsumer
    async def fr_result(self, event):
        """Receive result from generic Face-Recognition service and continue duty flow."""
        ctx = event.get("context", {}) or {}

        # Only process if context module == 'duty'
        if ctx.get("module") != "duty":
            return

        # Use generic service to process result
        service = DutyFaceRecognitionService(self)
        await service.process_face_recognition_result(
            ctx=ctx,
            result=event.get("result", {}),
            request_id=event.get("request_id"),
        )

    async def send_face_recognition_response(
        self,
        success,
        code,
        request_id,
        details,
        error_message=None,
        attendance_id=None,
        action=None,
        status=None,
    ):
        """Send face recognition response."""
        response = {
            "type": "face_recognition_success" if success else "face_recognition_error",
            "code": code,
            "request_id": request_id,
            "face_recognition_details": details,
            "timestamp": timezone.localtime().isoformat(),
        }
        # Flatten all details to root for compatibility
        if details:
            response.update(
                {
                    "person_id": details.get("raw_person_id")
                    or details.get("person_id"),
                    "confidence": details.get("confidence"),
                    "confidence_percentage": details.get("confidence_percentage"),
                    "threshold": details.get("threshold"),
                    "message": details.get("message"),
                    "attendance_type": details.get("attendance_type"),
                    "error": details.get("error"),
                    "detected_identifier": details.get("detected_identifier"),
                    "detected_name": details.get("detected_name"),
                }
            )
        if error_message:
            response["message"] = error_message
        if attendance_id:
            response["attendance_id"] = attendance_id
        if action:
            response["action"] = action
        if status:
            response["status"] = status
        await self.send(text_data=json.dumps(response))
