"""
WebSocket Consumer for Guest Visit Face Recognition.

Face recognition verification for guest visit registration.
"""

import json
import logging
import uuid
from datetime import datetime

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.utils import timezone

from .services.guest_face_recognition_service import GuestFaceRecognitionService

User = get_user_model()
logger = logging.getLogger(__name__)


class GuestVisitConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for guest visit face recognition operations.

    Handles:
    1. Face recognition verification for guest visit registration
    2. User identification via face recognition
    """

    async def connect(self):
        """Accept WebSocket connection and setup user session."""
        self.user = self.scope["user"]

        # Only authenticated users can connect
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Join user-specific group for personal updates
        self.user_group = f"guest_visit_user_{self.user.id}"
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        # Join general guest visit group
        await self.channel_layer.group_add("guest_visit", self.channel_name)

        await self.accept()

        # Send welcome message with current status
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "message": "Connected to guest visit face recognition service",
                    "user_id": str(self.user.id),
                    "username": self.user.username,
                    "timestamp": timezone.localtime().isoformat(),
                }
            )
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave groups only if they were initialized
        if hasattr(self, "user_group"):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        await self.channel_layer.group_discard("guest_visit", self.channel_name)

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            # Route to appropriate handler
            if message_type == "face_recognition":
                await self.handle_face_recognition(data)
            else:
                await self.send_error("Unknown message type", 400)

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format", 400)
        except Exception as e:
            await self.send_error(f"Server error: {str(e)}", 500)

    # =========================================================================
    # FACE RECOGNITION VERIFICATION (USING GENERIC SERVICE)
    # =========================================================================

    async def handle_face_recognition(self, data):
        """
        Handle face recognition verification request using generic service.

        Message format:
        {
            "type": "face_recognition",
            "image": "base64_string",
            "action": "verify_visitor",
            "request_id": "uuid"
        }
        """
        # Use generic face recognition service
        service = GuestFaceRecognitionService(self)
        await service.handle_face_recognition_request(data)

    # Handler for face recognition result broadcast by FaceRecognitionServiceConsumer
    async def fr_result(self, event):
        """Receive result from generic Face-Recognition service and continue guest visit flow."""
        ctx = event.get("context", {}) or {}

        # Only process if context module == 'guest_visit'
        if ctx.get("module") != "guest_visit":
            return

        # Use generic service to process result
        service = GuestFaceRecognitionService(self)
        await service.process_face_recognition_result(
            ctx=ctx,
            result=event.get("result", {}),
            request_id=event.get("request_id"),
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
        extra_data=None,
    ):
        """Send enhanced error message with additional context."""
        error_data = {
            "type": "error",
            "message": message,
            "code": code,
            "request_id": request_id,
            "timestamp": timezone.localtime().isoformat(),
        }

        if fr_result:
            error_data["fr_result"] = fr_result
        if action:
            error_data["action"] = action
        if extra_data:
            error_data["extra_data"] = extra_data

        await self.send(text_data=json.dumps(error_data))

    async def send_face_recognition_response(
        self,
        success,
        code,
        request_id,
        details,
        error_message=None,
        action=None,
        user_info=None,
    ):
        """Send face recognition response to client."""
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
        if action:
            response["action"] = action
        if user_info:
            response["user_info"] = user_info
        await self.send(text_data=json.dumps(response))
