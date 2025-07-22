import json
import uuid

from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from shared.services.face_recognition_client import face_recognition_client


class FaceRecognitionConsumer(AsyncWebsocketConsumer):
    """Generic Face-Recognition service.

    Expects message:
    {
      "type": "recognition_request",
      "image": "<base64>",
      "request_id": "uuid",
      "context": { ... }  # arbitrary dict (module, ids, etc.)
    }
    It returns result via same socket and also broadcasts to group
    fr_response_<request_id> so feature consumers can subscribe easily.
    """

    async def connect(self):
        await self.accept()
        # Join internal group so backend consumers can forward requests
        await self.channel_layer.group_add(
            "fr_requests",
            self.channel_name,
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.close(code=4003)
            return

        if data.get("type") != "recognition_request":
            await self.send_json({
                "type": "error",
                "message": "Unsupported message type",
            })
            return

        image_data = data.get("image")
        request_id = data.get("request_id") or str(uuid.uuid4())
        context = data.get("context", {})

        if not image_data:
            await self.send_json({
                "type": "error",
                "message": "image is required",
                "request_id": request_id,
            })
            return

        # Async call to ML service
        try:
            recognition = await face_recognition_client.recognize_face_simple(
                image_data=image_data,
            )
            result = recognition.get("result", {})
            success = bool(result.get("success"))
        except Exception as e:
            result = {"success": False, "error": str(e)}
            success = False

        payload = {
            "type": "face_recognition_response",
            "success": success,
            "request_id": request_id,
            "context": context,
            "result": result,
            "timestamp": timezone.localtime().isoformat(),
        }

        # Send back to requester
        await self.send_json(payload)

        # Broadcast to group for feature consumers
        await self.channel_layer.group_send(
            f"fr_response_{request_id}",
            {"type": "fr.result", **payload},
        )

    async def fr_result(self, event):
        """Forward result event to socket."""
        await self.send_json(event)

    # ------------------------------------------------------------------
    # Internal forward handler (from backend feature consumers)
    # ------------------------------------------------------------------

    async def recognition_forward(self, event):
        """Handle forwarded recognition_request from other consumers"""
        data = event.get("data", {})
        await self._handle_request(data)

    # helper used by both websocket receive & forward
    async def _handle_request(self, data):
        image_data = data.get("image")
        request_id = data.get("request_id") or str(uuid.uuid4())
        context = data.get("context", {})

        if not image_data:
            await self.channel_layer.group_send(
                f"fr_response_{request_id}",
                {
                    "type": "fr.result",
                    "success": False,
                    "request_id": request_id,
                    "context": context,
                    "result": {"success": False, "error": "image required"},
                    "timestamp": timezone.localtime().isoformat(),
                },
            )
            return

        try:
            recognition = await face_recognition_client.recognize_face_simple(
                image_data=image_data,
            )
            result = recognition.get("result", {})
            success = bool(result.get("success"))
        except Exception as e:
            result = {"success": False, "error": str(e)}
            success = False

        payload = {
            "type": "fr.result",
            "success": success,
            "request_id": request_id,
            "context": context,
            "result": result,
            "timestamp": timezone.localtime().isoformat(),
        }

        # Send to response group (backend consumers subscribed)
        await self.channel_layer.group_send(
            f"fr_response_{request_id}", payload
        )
        # If the original request was via WebSocket directly (has self.accepted)
        if data.get("via_socket"):
            # send minimal response back to socket client
            await self.send_json({**payload, "type": "face_recognition_response"}) 