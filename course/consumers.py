"""
WebSocket Consumer for Course Session Attendance.

Face recognition attendance for students in course sessions.
Teaching assistants connect via WebSocket for real-time communication.
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

from .models import CourseSessionAttendanceModel, CourseSessionModel
from .services.course_face_recognition_service import CourseFaceRecognitionService

User = get_user_model()
logger = logging.getLogger(__name__)


class CourseSessionAttendanceConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for course session attendance operations.

    Handles:
    1. Face recognition attendance for students (using generic service)
    2. Real-time status updates for TAs
    3. 1:1 student validation
    """

    async def connect(self):
        """Accept WebSocket connection and setup user session."""
        self.user = self.scope["user"]

        # Only authenticated users can connect
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Join user-specific group for personal updates
        self.user_group = f"course_attendance_user_{self.user.id}"
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        # Join general course attendance group
        await self.channel_layer.group_add("course_attendance", self.channel_name)

        await self.accept()

        # Send welcome message with current status
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "message": "Connected to course session attendance service",
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
        await self.channel_layer.group_discard("course_attendance", self.channel_name)

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            # Route to appropriate handler
            if message_type == "face_recognition":
                await self.handle_face_recognition(data)
            elif message_type == "get_attendance_list":
                await self.handle_get_attendance_list(data)
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
            "action": "mark_attendance",  # For course session, always mark_attendance
            "request_id": "uuid"
        }
        """
        # Use generic face recognition service
        service = CourseFaceRecognitionService(self)
        await service.handle_face_recognition_request(data)

    # =========================================================================
    # ATTENDANCE LIST MANAGEMENT
    # =========================================================================

    async def handle_get_attendance_list(self, data):
        """
        Get attendance list for a course session.

        Message format:
        {
            "type": "get_attendance_list",
            "course_session_id": "uuid",
            "request_id": "uuid"
        }
        """
        course_session_id = data.get("course_session_id")
        request_id = data.get("request_id", str(uuid.uuid4()))

        if not course_session_id:
            await self.send_error("course_session_id is required", 400, request_id)
            return

        try:
            # Get course session and validate TA permission
            course_session = await sync_to_async(CourseSessionModel.objects.get)(
                id=course_session_id, is_active=True
            )

            is_ta_assigned = await sync_to_async(
                course_session.teaching_assistants.filter(id=self.user.id).exists
            )()

            if not is_ta_assigned:
                await self.send_error(
                    "You are not assigned as TA to this course session", 403, request_id
                )
                return

            # Get attendance records with student info
            attendances = await sync_to_async(list)(
                CourseSessionAttendanceModel.objects.filter(
                    course_session=course_session, is_active=True
                )
                .select_related("student")
                .order_by("student__first_name", "student__last_name")
            )

            # Serialize attendance data (async-safe)
            attendance_list = []
            for attendance in attendances:
                student = attendance.student

                # Get student data via sync_to_async to avoid async context issues
                student_full_name = (
                    await sync_to_async(student.get_full_name)() or student.username
                )
                student_number = getattr(student, "student_number", "")

                # Get marked_by data safely
                marked_by_name = None
                if attendance.marked_by:
                    marked_by_name = await sync_to_async(
                        attendance.marked_by.get_full_name
                    )()

                # Get confidence percentage safely
                confidence_percentage = await sync_to_async(
                    attendance.get_confidence_percentage
                )()

                # Check if can mark attendance safely
                can_mark = await sync_to_async(attendance.can_mark_attendance)()

                attendance_data = {
                    "id": str(attendance.id),
                    "student": {
                        "id": str(student.id),
                        "full_name": student_full_name,
                        "student_number": student_number,
                    },
                    "status": attendance.status,
                    "marked_at": (
                        attendance.marked_at.isoformat()
                        if attendance.marked_at
                        else None
                    ),
                    "marked_by": marked_by_name,
                    "confidence": confidence_percentage,
                    "can_mark": can_mark,
                    "manual_override": attendance.manual_attendance_override,
                }
                attendance_list.append(attendance_data)

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "attendance_list",
                        "request_id": request_id,
                        "course_session_id": course_session_id,
                        "attendances": attendance_list,
                        "timestamp": timezone.localtime().isoformat(),
                    }
                )
            )

        except CourseSessionModel.DoesNotExist:
            await self.send_error("Course session not found", 404, request_id)
        except Exception as e:
            await self.send_error(
                f"Failed to get attendance list: {str(e)}", 500, request_id
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
        attendance_id = event.get("attendance_id")

        # Get confidence percentage safely if attendance_id is provided
        confidence = None
        if attendance_id:
            try:
                attendance = await sync_to_async(
                    CourseSessionAttendanceModel.objects.get
                )(id=attendance_id, is_active=True)
                confidence = await sync_to_async(attendance.get_confidence_percentage)()
            except CourseSessionAttendanceModel.DoesNotExist:
                pass

        await self.send(
            text_data=json.dumps(
                {
                    "type": "attendance_update_broadcast",
                    "attendance_id": event["attendance_id"],
                    "student_id": event["student_id"],
                    "status": event["status"],
                    "confidence": confidence or event.get("confidence"),
                    "timestamp": timezone.localtime().isoformat(),
                }
            )
        )

    # Handler for face recognition result broadcast by FaceRecognitionServiceConsumer
    async def fr_result(self, event):
        """Receive result from generic Face-Recognition service and continue course session flow."""
        ctx = event.get("context", {}) or {}

        # Only process if context module == 'course_session'
        if ctx.get("module") != "course_session":
            return

        # Use generic service to process result
        service = CourseFaceRecognitionService(self)
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
