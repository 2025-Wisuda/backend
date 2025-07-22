"""
Course Session Attendance Face Recognition Service.

Extends GenericFaceRecognitionService with course session specific logic.
"""

import logging
from typing import Any, Dict

from asgiref.sync import sync_to_async
from django.utils import timezone
from shared.services.face_recognition_service import GenericFaceRecognitionService

from ..models import CourseSessionAttendanceModel

logger = logging.getLogger(__name__)


class CourseFaceRecognitionService(GenericFaceRecognitionService):
    """
    Course session attendance specific face recognition service.

    Handles course session attendance specific validation and attendance logic.
    """

    async def _validate_attendance_record(
        self, attendance_id: str, action: str, request_id: str
    ) -> Dict[str, Any]:
        """
        Validate course session attendance record.

        Args:
            attendance_id: UUID of course session attendance record
            action: Action type (always mark_attendance for course session)
            request_id: Unique request ID

        Returns:
            Dict with validation result
        """
        if action != "mark_attendance":
            await self.consumer.send_enhanced_error(
                "action must be 'mark_attendance' for course session", 400, request_id
            )
            return {"valid": False}

        # Get attendance record
        try:
            attendance = await sync_to_async(CourseSessionAttendanceModel.objects.get)(
                id=attendance_id, is_active=True
            )
        except CourseSessionAttendanceModel.DoesNotExist:
            await self.consumer.send_enhanced_error(
                "Attendance record not found", 404, request_id
            )
            return {"valid": False}

        # Validate TA permission - must be assigned to this course session
        course_session = await sync_to_async(lambda: attendance.course_session)()
        is_ta_assigned = await sync_to_async(
            course_session.teaching_assistants.filter(id=self.user.id).exists
        )()

        if not is_ta_assigned:
            await self.consumer.send_enhanced_error(
                "You are not assigned as TA to this course session", 403, request_id
            )
            return {"valid": False}

        # Check if attendance can be marked
        can_mark = await sync_to_async(attendance.can_mark_attendance)()
        if not can_mark:
            await self.consumer.send_enhanced_error(
                "Attendance already marked for this student", 400, request_id
            )
            return {"valid": False}

        # Build context for face recognition
        student = await sync_to_async(lambda: attendance.student)()
        expected_identifier = await sync_to_async(
            lambda: getattr(student, "student_number", str(student.id))
        )()

        context = {
            "module": "course_session",
            "attendance_id": str(attendance.id),
            "action": action,
            "expected_identifier": expected_identifier,
            "expected_name": "Student",  # Generic name for course session
            "identifier_type": "student_number",
        }

        return {
            "valid": True,
            "attendance": attendance,
            "context": context,
        }

    async def _apply_attendance(
        self,
        attendance_id: str,
        person_id: str,
        confidence: float,
        request_id: str,
        action: str = None,
    ) -> Dict[str, Any]:
        """
        Apply course session attendance based on face recognition result.

        Args:
            attendance_id: UUID of attendance record
            person_id: Detected person ID from face recognition
            confidence: Face recognition confidence
            request_id: Unique request ID
            action: Action type (ignored for course session, always mark_attendance)

        Returns:
            Dict with result
        """
        try:
            attendance = await sync_to_async(CourseSessionAttendanceModel.objects.get)(
                id=attendance_id, is_active=True
            )
        except CourseSessionAttendanceModel.DoesNotExist:
            return {
                "success": False,
                "error": "Attendance record not found",
                "code": 404,
            }

        # Get session safely to avoid property access in async context
        session = await sync_to_async(lambda: attendance.course_session)()

        # Update attendance fields directly (async-safe like duty attendance)
        attendance.marked_at = timezone.localtime()
        attendance.marked_by = self.user
        attendance.face_recognition_person_id = person_id
        attendance.face_recognition_confidence = confidence
        attendance.face_recognition_request_id = request_id
        attendance.manual_attendance_override = False

        # Calculate status with session parameter to avoid property access
        attendance.status = await sync_to_async(attendance._calculate_auto_status)(
            session=session
        )

        # Save via sync_to_async to avoid async context error
        await sync_to_async(attendance.save)(
            update_fields=[
                "marked_at",
                "marked_by",
                "face_recognition_person_id",
                "face_recognition_confidence",
                "face_recognition_request_id",
                "manual_attendance_override",
                "status",
            ],
        )

        # Get final status after save
        final_status = attendance.status

        return {
            "success": True,
            "status": final_status,
            "attendance": attendance,
        }

    async def _broadcast_attendance_update(
        self, attendance_result: Dict[str, Any]
    ) -> None:
        """
        Broadcast course session attendance update to other users.

        Args:
            attendance_result: Result from _apply_attendance
        """
        attendance = attendance_result.get("attendance")
        if not attendance:
            return

        # Get confidence percentage safely
        confidence_percentage = await sync_to_async(
            attendance.get_confidence_percentage
        )()

        # Get student ID safely
        student_id = await sync_to_async(lambda: str(attendance.student.id))()

        # Broadcast to course attendance group
        await self.consumer.channel_layer.group_send(
            "course_attendance",
            {
                "type": "attendance_update",
                "attendance_id": str(attendance.id),
                "student_id": student_id,
                "status": attendance_result.get("status"),
                "confidence": confidence_percentage,
            },
        )
