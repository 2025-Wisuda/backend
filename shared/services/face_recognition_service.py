"""
Generic Face Recognition Service for Attendance Modules.

This service provides reusable face recognition functionality that can be used
by both duty attendance and course session attendance modules.
"""

import json
import logging
import uuid
from typing import Any, Dict, Optional

from asgiref.sync import sync_to_async
from django.utils import timezone

logger = logging.getLogger(__name__)


class GenericFaceRecognitionService:
    """
    Generic service for handling face recognition attendance.

    Can be used by both duty attendance and course session attendance modules.
    """

    def __init__(self, consumer_instance):
        """
        Initialize with consumer instance for WebSocket communication.

        Args:
            consumer_instance: WebSocket consumer instance (DutyAttendanceConsumer or CourseSessionAttendanceConsumer)
        """
        self.consumer = consumer_instance
        self.user = consumer_instance.user

    async def handle_face_recognition_request(self, data: Dict[str, Any]) -> None:
        """
        Generic face recognition handler that can be used by both modules.

        Args:
            data: WebSocket message data containing:
                - attendance_id: UUID of attendance record
                - image: Base64 image data
                - action: Action type (clock_in/clock_out for duty, mark_attendance for course)
                - request_id: Unique request ID
        """
        attendance_id = data.get("attendance_id")
        image_data = data.get("image")
        action = data.get("action")
        request_id = data.get("request_id", str(uuid.uuid4()))

        # Validate required fields
        if not attendance_id or not image_data:
            await self.consumer.send_enhanced_error(
                "attendance_id and image are required", 400, request_id
            )
            return

        # Get module-specific validation and context
        validation_result = await self._validate_attendance_record(
            attendance_id, action, request_id
        )
        if not validation_result["valid"]:
            return

        attendance = validation_result["attendance"]
        context = validation_result["context"]

        try:
            # Forward to face recognition service
            await self._forward_to_face_recognition(
                request_id=request_id, image_data=image_data, context=context
            )

            # Notify client that processing started
            await self.consumer.send(
                text_data=json.dumps(
                    {
                        "type": "processing_started",
                        "request_id": request_id,
                        "timestamp": timezone.localtime().isoformat(),
                    }
                )
            )

        except Exception as e:
            await self.consumer.send_enhanced_error(
                f"Face recognition failed: {str(e)}", 500, request_id
            )

    async def _validate_attendance_record(
        self, attendance_id: str, action: str, request_id: str
    ) -> Dict[str, Any]:
        """
        Validate attendance record based on module type.

        This method should be overridden by specific modules.

        Returns:
            Dict with validation result:
                - valid: bool
                - attendance: attendance record (if valid)
                - context: dict with module-specific context
        """
        raise NotImplementedError(
            "Subclasses must implement _validate_attendance_record"
        )

    async def _forward_to_face_recognition(
        self, request_id: str, image_data: str, context: Dict[str, Any]
    ) -> None:
        """
        Forward request to face recognition service.

        Args:
            request_id: Unique request ID
            image_data: Base64 image data
            context: Module-specific context
        """
        # Subscribe to response group
        await self.consumer.channel_layer.group_add(
            f"fr_response_{request_id}",
            self.consumer.channel_name,
        )

        logger.debug(
            f"[{context.get('module', 'UNKNOWN')}] forward to fr_requests req={request_id}"
        )

        # Send to face recognition service
        await self.consumer.channel_layer.send(
            "fr_requests",
            {
                "type": "recognition_forward",
                "data": {
                    "type": "recognition_request",
                    "request_id": request_id,
                    "image": image_data,
                    "context": context,
                },
            },
        )

    async def process_face_recognition_result(
        self, ctx: Dict[str, Any], result: Dict[str, Any], request_id: str
    ) -> None:
        """
        Process face recognition result and apply to attendance record.

        Args:
            ctx: Context from face recognition service
            result: Face recognition result
            request_id: Unique request ID
        """
        attendance_id = ctx.get("attendance_id")

        if not attendance_id:
            await self.consumer.send_face_recognition_response(
                success=False,
                code=400,
                request_id=request_id,
                error_message="attendance_id missing in context",
                details=self._build_face_recognition_details(
                    ctx=ctx, result=result, error="attendance_id missing in context"
                ),
            )
            return

        # Extract face recognition details
        person_id = result.get("person_id")
        confidence = result.get("confidence", 0.0)
        threshold = result.get("threshold", 0.7)
        message = result.get("message", "")
        attendance_type = result.get("attendance_type")
        raw_person_id = person_id

        # Parse detected identifier and name
        if person_id and "_" in person_id:
            detected_identifier, detected_name = person_id.split("_", 1)
            detected_name = detected_name.replace("_", " ")
        else:
            detected_identifier = person_id or ""
            detected_name = ""

        # Get expected identifier from context
        expected_identifier = ctx.get("expected_identifier", "")
        expected_name = ctx.get("expected_name", "")

        # If context doesn't have expected_identifier, calculate from user (fallback to old logic)
        if not expected_identifier:
            expected_identifier = getattr(self.user, "student_number", None) or str(
                self.user.id
            )
            expected_name = (
                getattr(self.user, "first_name", "")
                + " "
                + getattr(self.user, "last_name", "")
            ).strip() or self.user.username

        # Get identifier_type from context or calculate from user
        identifier_type = ctx.get("identifier_type", "")
        if not identifier_type:
            identifier_type = (
                "student_number" if hasattr(self.user, "student_number") else "user_id"
            )

        # If recognition failed
        if not result.get("success"):
            error_msg = result.get("error", "Face recognition failed")
            await self.consumer.send_face_recognition_response(
                success=False,
                code=400,
                request_id=request_id,
                error_message=error_msg,
                details=self._build_face_recognition_details(
                    ctx=ctx,
                    result=result,
                    expected_identifier=expected_identifier,
                    expected_name=expected_name,
                    detected_identifier=detected_identifier,
                    detected_name=detected_name,
                    identifier_type=identifier_type,
                    confidence=confidence,
                    threshold=threshold,
                    attendance_type=attendance_type,
                    error=error_msg,
                    raw_person_id=raw_person_id,
                ),
            )
            return

        if not person_id:
            await self.consumer.send_face_recognition_response(
                success=False,
                code=400,
                request_id=request_id,
                error_message="No face detected",
                details=self._build_face_recognition_details(
                    ctx=ctx,
                    result=result,
                    expected_identifier=expected_identifier,
                    expected_name=expected_name,
                    detected_identifier="",
                    detected_name="",
                    identifier_type=identifier_type,
                    confidence=confidence,
                    threshold=threshold,
                    attendance_type=attendance_type,
                    error="No face detected",
                    raw_person_id=raw_person_id,
                ),
            )
            return

        # Validate identifier matches expected
        if expected_identifier != detected_identifier:
            await self.consumer.send_face_recognition_response(
                success=False,
                code=403,
                request_id=request_id,
                error_message="Identifier mismatch",
                details=self._build_face_recognition_details(
                    ctx=ctx,
                    result=result,
                    expected_identifier=expected_identifier,
                    expected_name=expected_name,
                    detected_identifier=detected_identifier,
                    detected_name=detected_name,
                    identifier_type=identifier_type,
                    confidence=confidence,
                    threshold=threshold,
                    attendance_type=attendance_type,
                    error="Identifier mismatch",
                    raw_person_id=raw_person_id,
                ),
            )
            return

        # Apply attendance (module-specific)
        action = ctx.get("action", "clock_in")
        attendance_result = await self._apply_attendance(
            attendance_id=attendance_id,
            person_id=person_id,
            confidence=confidence,
            request_id=request_id,
            action=action,
        )

        if not attendance_result["success"]:
            await self.consumer.send_face_recognition_response(
                success=False,
                code=attendance_result.get("code", 500),
                request_id=request_id,
                error_message=attendance_result.get(
                    "error", "Failed to apply attendance"
                ),
                details=self._build_face_recognition_details(
                    ctx=ctx,
                    result=result,
                    expected_identifier=expected_identifier,
                    expected_name=expected_name,
                    detected_identifier=detected_identifier,
                    detected_name=detected_name,
                    identifier_type=identifier_type,
                    confidence=confidence,
                    threshold=threshold,
                    attendance_type=attendance_type,
                    error=attendance_result.get("error"),
                    raw_person_id=raw_person_id,
                ),
            )
            return

        # Success response
        await self.consumer.send_face_recognition_response(
            success=True,
            code=200,
            request_id=request_id,
            details=self._build_face_recognition_details(
                ctx=ctx,
                result=result,
                expected_identifier=expected_identifier,
                expected_name=expected_name,
                detected_identifier=detected_identifier,
                detected_name=detected_name,
                identifier_type=identifier_type,
                confidence=confidence,
                threshold=threshold,
                attendance_type=attendance_type,
                raw_person_id=raw_person_id,
            ),
            attendance_id=attendance_id,
            action=ctx.get("action"),
            status=attendance_result.get("status"),
        )

        # Broadcast update (module-specific)
        await self._broadcast_attendance_update(attendance_result)

    async def _apply_attendance(
        self,
        attendance_id: str,
        person_id: str,
        confidence: float,
        request_id: str,
        action: str,
    ) -> Dict[str, Any]:
        """
        Apply attendance based on face recognition result.

        This method should be overridden by specific modules.

        Returns:
            Dict with result:
                - success: bool
                - status: attendance status (if success)
                - error: error message (if not success)
                - code: error code (if not success)
        """
        raise NotImplementedError("Subclasses must implement _apply_attendance")

    async def _broadcast_attendance_update(
        self, attendance_result: Dict[str, Any]
    ) -> None:
        """
        Broadcast attendance update to other users.

        This method should be overridden by specific modules.
        """
        raise NotImplementedError(
            "Subclasses must implement _broadcast_attendance_update"
        )

    def _build_face_recognition_details(
        self,
        ctx: Dict[str, Any],
        result: Dict[str, Any],
        expected_identifier: Optional[str] = None,
        expected_name: Optional[str] = None,
        detected_identifier: Optional[str] = None,
        detected_name: Optional[str] = None,
        identifier_type: Optional[str] = None,
        confidence: Optional[float] = None,
        threshold: Optional[float] = None,
        attendance_type: Optional[str] = None,
        error: Optional[str] = None,
        raw_person_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build face recognition details for response.

        Returns:
            Dict with face recognition details
        """
        return {
            "success": result.get("success", False),
            "expected_identifier": expected_identifier,
            "expected_name": expected_name,
            "detected_identifier": detected_identifier,
            "detected_name": detected_name,
            "identifier_type": identifier_type,
            "confidence": confidence,
            "confidence_percentage": (
                round(confidence * 100, 1) if confidence is not None else None
            ),
            "threshold": threshold,
            "attendance_type": attendance_type,
            "error": error or result.get("error"),
            "raw_person_id": raw_person_id,
        }
