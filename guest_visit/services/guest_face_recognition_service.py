"""
Guest Visit Face Recognition Service.

Extends GenericFaceRecognitionService with guest visit specific logic.
"""

import json
import logging
import uuid
from typing import Any, Dict

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from shared.services.face_recognition_service import GenericFaceRecognitionService

from ..models import GuestVisitModel

User = get_user_model()
logger = logging.getLogger(__name__)


class GuestFaceRecognitionService(GenericFaceRecognitionService):
    """
    Guest visit specific face recognition service.
    Handles guest visit specific validation and user identification logic.
    """

    async def handle_face_recognition_request(self, data: Dict[str, Any]) -> None:
        image_data = data.get("image")
        action = data.get("action")
        request_id = data.get("request_id", str(uuid.uuid4()))

        if not image_data:
            await self.consumer.send_enhanced_error(
                "image is required", 400, request_id
            )
            return

        if action != "verify_visitor":
            await self.consumer.send_enhanced_error(
                "action must be 'verify_visitor' for guest visit", 400, request_id
            )
            return

        # Build context for AI WS
        context = {
            "module": "guest_visit",
            "action": action,
        }

        # Forward to AI WS
        await self._forward_to_face_recognition(
            request_id=request_id, image_data=image_data, context=context
        )

        await self.consumer.send(
            text_data=json.dumps(
                {
                    "type": "processing_started",
                    "request_id": request_id,
                    "timestamp": timezone.localtime().isoformat(),
                }
            )
        )

    async def process_face_recognition_result(self, ctx, result, request_id):
        # Ambil person_id dari AI WS (format: NPM_NAMA)
        person_id = result.get("person_id", "")
        confidence = result.get("confidence", 0.0)
        threshold = result.get("threshold", 0.7)
        message = result.get("message", "")
        attendance_type = "guest_visit"
        error = result.get("error", "")
        detected_name = result.get("detected_name", "")
        success = result.get("success", False)

        # Check if face recognition was successful
        if not success:
            await self.consumer.send_face_recognition_response(
                success=False,
                code=400,
                request_id=request_id,
                details={
                    "success": False,
                    "detected_identifier": "",
                    "confidence": confidence,
                    "threshold": threshold,
                    "message": "Face not recognized",
                    "attendance_type": attendance_type,
                    "error": error or "Face not found in database",
                    "detected_name": "",
                    "person_id": person_id,
                },
            )
            return

        # Check if confidence meets threshold
        if confidence < threshold:
            await self.consumer.send_face_recognition_response(
                success=False,
                code=400,
                request_id=request_id,
                details={
                    "success": False,
                    "detected_identifier": "",
                    "confidence": confidence,
                    "threshold": threshold,
                    "message": f"Confidence too low ({confidence:.2f} < {threshold})",
                    "attendance_type": attendance_type,
                    "error": "Face recognition confidence below threshold",
                    "detected_name": detected_name or "",
                    "person_id": person_id,
                },
            )
            return

        # For guest visit: Extract NPM from AI response and find user
        detected_identifier = ""
        if person_id and "_" in person_id:
            # Extract NPM from format: NPM_NAMA
            npm = person_id.split("_")[0]

            # Search for user by both student_number and employee_number
            user = await sync_to_async(
                User.objects.filter(
                    models.Q(student_number=npm) | models.Q(employee_number=npm)
                ).first
            )()

            if user:
                # Replace detected_identifier with user ID
                detected_identifier = str(user.id)
                detected_name = (
                    detected_name
                    or f"{user.first_name} {user.last_name}".strip()
                    or user.username
                )
                logger.info(
                    f"✅ Guest visit: Found user {user.username} (ID: {user.id}) for NPM {npm}"
                )
            else:
                logger.warning(f"❌ Guest visit: No user found for NPM {npm}")
                # Still return success but with empty detected_identifier
                # This allows mobile app to handle unknown visitors

        # SUCCESS - Face recognized and confidence is good
        details = {
            "success": True,
            "detected_identifier": detected_identifier,
            "confidence": confidence,
            "threshold": threshold,
            "message": message or "Face recognized successfully",
            "attendance_type": attendance_type,
            "error": "",
            "detected_name": detected_name or "",
            "person_id": person_id,
        }

        await self.consumer.send_face_recognition_response(
            success=True,
            code=200,
            request_id=request_id,
            details=details,
        )
