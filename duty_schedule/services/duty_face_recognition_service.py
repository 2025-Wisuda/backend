"""
Duty Attendance Face Recognition Service.

Extends GenericFaceRecognitionService with duty-specific logic.
"""

import logging
from typing import Any, Dict

from asgiref.sync import sync_to_async
from django.utils import timezone
from shared.services.face_recognition_service import GenericFaceRecognitionService

from ..models import DutyAttendanceModel

logger = logging.getLogger(__name__)


class DutyFaceRecognitionService(GenericFaceRecognitionService):
    """
    Duty attendance specific face recognition service.

    Handles duty attendance specific validation and attendance logic.
    """

    async def _validate_attendance_record(
        self, attendance_id: str, action: str, request_id: str
    ) -> Dict[str, Any]:
        """
        Validate duty attendance record.

        Args:
            attendance_id: UUID of duty attendance record
            action: Action type (clock_in or clock_out)
            request_id: Unique request ID

        Returns:
            Dict with validation result
        """
        if action not in ["clock_in", "clock_out"]:
            await self.consumer.send_enhanced_error(
                "action must be 'clock_in' or 'clock_out'", 400, request_id
            )
            return {"valid": False}

        # Get attendance record
        try:
            attendance = await sync_to_async(DutyAttendanceModel.objects.get)(
                id=attendance_id, laboratory_assistant=self.user, is_active=True
            )
        except DutyAttendanceModel.DoesNotExist:
            await self.consumer.send_enhanced_error(
                "Attendance record not found", 404, request_id
            )
            return {"valid": False}

        # Check OTP validation for user today (not specific record)
        today = timezone.localtime().date()
        today_records = await sync_to_async(list)(
            DutyAttendanceModel.objects.filter(
                laboratory_assistant=self.user, date=today, is_active=True
            )
        )

        is_otp_valid = False
        if today_records:
            # Check OTP validation from any today's record
            is_otp_valid = await sync_to_async(today_records[0].is_otp_validated)()

        logger.debug(
            f"OTP Check - Attendance ID: {attendance.id}, Date: {attendance.date}, User: {self.user}, Today: {today}, Today records: {len(today_records)}, Is OTP valid: {is_otp_valid}"
        )

        if not is_otp_valid:
            await self.consumer.send_enhanced_error(
                "OTP validation required first", 403, request_id
            )
            return {"valid": False}

        # Check action validity
        if action == "clock_in":
            can_clock_in = await sync_to_async(attendance.can_clock_in)()
            if not can_clock_in:
                await self.consumer.send_enhanced_error(
                    "Cannot clock in: already clocked in or OTP expired",
                    400,
                    request_id,
                )
                return {"valid": False}
        else:  # clock_out
            can_clock_out = await sync_to_async(attendance.can_clock_out)()
            if not can_clock_out:
                await self.consumer.send_enhanced_error(
                    "Cannot clock out: must clock in first", 400, request_id
                )
                return {"valid": False}

        # Build context for face recognition
        context = {
            "module": "duty",
            "attendance_id": str(attendance.id),
            "action": action,
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
        action: str,
    ) -> Dict[str, Any]:
        """
        Apply duty attendance based on face recognition result.

        Args:
            attendance_id: UUID of attendance record
            person_id: Detected person ID from face recognition
            confidence: Face recognition confidence
            request_id: Unique request ID
            action: Action type (clock_in or clock_out)

        Returns:
            Dict with result
        """
        try:
            attendance = await sync_to_async(DutyAttendanceModel.objects.get)(
                id=attendance_id, is_active=True
            )
        except DutyAttendanceModel.DoesNotExist:
            return {
                "success": False,
                "error": "Attendance record not found",
                "code": 404,
            }

        # Debug: Log action for troubleshooting
        logger.info(
            f"[DEBUG] _apply_attendance - Action: {action}, Attendance ID: {attendance_id}"
        )

        # Apply attendance based on action
        if action == "clock_in":
            logger.info(f"[DEBUG] Processing clock_in for attendance {attendance_id}")
            final_status = await sync_to_async(
                attendance.clock_in_via_face_recognition
            )(
                person_id=person_id,
                confidence=confidence,
                request_id=request_id,
            )
        else:  # clock_out
            logger.info(f"[DEBUG] Processing clock_out for attendance {attendance_id}")
            final_status = await sync_to_async(
                attendance.clock_out_via_face_recognition
            )(
                person_id=person_id,
                confidence=confidence,
                request_id=request_id,
            )

        return {
            "success": True,
            "status": final_status,
            "attendance": attendance,
        }

    async def _broadcast_attendance_update(
        self, attendance_result: Dict[str, Any]
    ) -> None:
        """
        Broadcast duty attendance update to other users.

        Args:
            attendance_result: Result from _apply_attendance
        """
        attendance = attendance_result.get("attendance")
        if not attendance:
            return

        # Broadcast to duty attendance group
        await self.consumer.channel_layer.group_send(
            "duty_attendance",
            {
                "type": "attendance_update",
                "attendance_id": str(attendance.id),
                "assistant_id": str(attendance.laboratory_assistant.id),
                "status": attendance_result.get("status"),
                "confidence": attendance.get_confidence_percentage(),
            },
        )
