import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()


import logging

from channels.consumer import AsyncConsumer
from django.utils import timezone
from shared.services.face_recognition_client import face_recognition_client

logger = logging.getLogger(__name__)


class FaceRecognitionServiceConsumer(AsyncConsumer):
    """Background consumer listening on 'fr_requests' channel name."""

    async def recognition_forward(self, event):
        data = event.get("data", {})
        image = data.get("image")
        req_id = data.get("request_id")
        context = data.get("context", {})

        if not image or not req_id:
            return  # invalid payload, ignore

        logger.info(f"[FR_BEST] Processing request: {req_id}")
        try:
            # Determine attendance type from context
            module = context.get("module", "duty")
            attendance_type = "course_session" if module == "course_session" else "duty"

            rec = await face_recognition_client.recognize_face_simple(
                image_data=image,
            )
            result = rec.get("result", {})
            # Override attendance_type from context
            result["attendance_type"] = attendance_type

            # Additional debug details for testing
            logger.info(
                f"[FR_BEST] Detection details: person_id={result.get('person_id')}, confidence={result.get('confidence')}, attendance_type={attendance_type}, raw={result}"
            )
            success = bool(result.get("success"))
        except Exception as e:
            result = {"success": False, "error": str(e)}
            success = False

        payload = {
            "type": "fr.result",
            "success": success,
            "request_id": req_id,
            "context": context,
            "result": result,
            "timestamp": timezone.localtime().isoformat(),
        }
        logger.info(
            f"[FR_BEST] Result broadcast: success={success}, request_id={req_id}"
        )
        await self.channel_layer.group_send(f"fr_response_{req_id}", payload)
