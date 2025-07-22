"""
Face Recognition WebSocket Client Service for Main Backend.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

import websockets
from django.conf import settings

logger = logging.getLogger(__name__)


class FaceRecognitionClient:
    """
    WebSocket client for communicating with face recognition service.
    """

    def __init__(self):
        # Get configuration from settings
        self.ws_url = getattr(
            settings,
            "FACE_RECOGNITION_WS_URL",
            "ws://localhost:8000/ws/backend-communication/",
        )
        self.auth_token = getattr(
            settings, "FACE_RECOGNITION_AUTH_TOKEN", "backend-service-token"
        )
        self.websocket = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5

    async def connect(self):
        """Establish WebSocket connection to face recognition service."""
        try:
            # For websockets 15.0.1, use additional_headers instead of extra_headers
            self.websocket = await websockets.connect(
                self.ws_url,
                additional_headers={"Authorization": self.auth_token},
                ping_interval=40,
                ping_timeout=40,
                max_size=None,  # disable message size limit for large base64 images
            )

            self.is_connected = True
            self.reconnect_attempts = 0
            logger.info(f"[FR_BEST] Connected to face recognition service")

        except Exception as e:
            logger.error(f"[FR_BEST] Connection failed: {str(e)}")
            self.is_connected = False
            raise

    async def disconnect(self):
        """Disconnect from face recognition service."""
        try:
            if self.websocket:
                await self.websocket.close()
            self.is_connected = False
            logger.info("[FR_BEST] Disconnected from face recognition service")
        except Exception as e:
            logger.error(f"[FR_BEST] Disconnect error: {str(e)}")

    async def _ensure_connected(self):
        """Ensure connection is established, reconnect if necessary."""
        if not self.is_connected:
            if self.reconnect_attempts < self.max_reconnect_attempts:
                try:
                    await self.connect()
                except Exception as e:
                    self.reconnect_attempts += 1
                    logger.warning(
                        f"[FR_BEST] Reconnect attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} failed"
                    )
                    if self.reconnect_attempts >= self.max_reconnect_attempts:
                        raise Exception("Max reconnection attempts reached")
                    await asyncio.sleep(2)  # Wait before retry
                    await self._ensure_connected()
            else:
                raise Exception(
                    "Not connected to face recognition service and max reconnection attempts reached"
                )

    async def _wait_for_final_response(
        self, request_id: str, timeout: int = 30
    ) -> Dict[str, Any]:
        """Wait until we receive the final face_recognition_result for the given request_id."""
        try:
            # Keep consuming messages until timeout reached or desired message arrived
            end_time = asyncio.get_event_loop().time() + timeout
            while True:
                remaining = end_time - asyncio.get_event_loop().time()
                if remaining <= 0:
                    raise asyncio.TimeoutError()
                try:
                    # Wait only for the remaining time
                    raw_msg = await asyncio.wait_for(
                        self.websocket.recv(), timeout=remaining
                    )
                except asyncio.TimeoutError:
                    raise
                msg = json.loads(raw_msg)

                # Ignore messages without request_id or for different requests
                if msg.get("request_id") != request_id:
                    continue

                # Return immediately if this is the final result
                if (
                    msg.get("type") == "face_recognition_result"
                    or msg.get("type") == "attendance_result"
                ):
                    return msg

                # Otherwise it's an interim update, keep waiting (e.g., processing_started)
        except asyncio.TimeoutError:
            logger.error(f"[FR_BEST] Request timeout: {request_id}")
            return {
                "type": "error",
                "request_id": request_id,
                "result": {
                    "success": False,
                    "error": "Request timeout",
                    "person_id": None,
                    "confidence": 0.0,
                },
            }
        except Exception as e:
            logger.error(f"[FR_BEST] Response error: {str(e)}")
            return {
                "type": "error",
                "request_id": request_id,
                "result": {
                    "success": False,
                    "error": str(e),
                    "person_id": None,
                    "confidence": 0.0,
                },
            }

    async def recognize_face_simple(
        self, image_data: str, timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Simple face recognition - only send image, get back person info.

        Args:
            image_data: Base64 encoded image
            timeout: Request timeout in seconds

        Returns:
            Dictionary containing recognition results
        """
        try:
            await self._ensure_connected()

            request_id = f"req_simple_{int(time.time())}"

            request = {
                "type": "attendance_request",
                "request_id": request_id,
                "image_data": image_data,
                "attendance_type": "duty",  # Default
                "user_id": 0,  # Default
            }

            # Send request
            await self.websocket.send(json.dumps(request))
            logger.info(f"[FR_BEST] Sent recognition request: {request_id}")

            # Wait for the final result, ignore interim messages
            response = await self._wait_for_final_response(request_id, timeout)
            return response

        except Exception as e:
            logger.error(f"[FR_BEST] Recognition failed: {str(e)}")
            return {
                "type": "error",
                "request_id": f"req_simple_{int(time.time())}",
                "result": {
                    "success": False,
                    "error": str(e),
                    "person_id": None,
                    "confidence": 0.0,
                },
            }

    async def recognize_face(
        self, image_data: str, attendance_type: str, user_id: int, timeout: int = 2400
    ) -> Dict[str, Any]:
        """
        Send face recognition request and wait for response.

        Args:
            image_data: Base64 encoded image
            attendance_type: Type of attendance (duty, course_session, guest_visit)
            user_id: User ID for the request
            timeout: Request timeout in seconds

        Returns:
            Dictionary containing recognition results
        """
        try:
            await self._ensure_connected()

            request_id = f"req_{user_id}_{int(time.time())}"

            request = {
                "type": "attendance_request",
                "request_id": request_id,
                "image_data": image_data,
                "attendance_type": attendance_type,
                "user_id": user_id,
            }

            # Send request
            await self.websocket.send(json.dumps(request))
            logger.info(f"[FR_BEST] Sent recognition request: {request_id}")

            # Wait for the final result, ignore interim messages
            response = await self._wait_for_final_response(request_id, timeout)
            return response

        except Exception as e:
            logger.error(f"[FR_BEST] Recognition failed: {str(e)}")
            return {
                "type": "error",
                "request_id": f"req_{user_id}_{int(time.time())}",
                "result": {
                    "success": False,
                    "error": str(e),
                    "person_id": None,
                    "confidence": 0.0,
                },
            }

    async def add_person_embedding(
        self, person_id: str, image_data: str
    ) -> Dict[str, Any]:
        """
        Add person embedding to face recognition database.

        Args:
            person_id: Unique identifier for the person
            image_data: Base64 encoded image

        Returns:
            Dictionary containing operation result
        """
        try:
            await self._ensure_connected()

            request = {
                "type": "add_person_embedding",
                "person_id": person_id,
                "image_data": image_data,
            }

            await self.websocket.send(json.dumps(request))
            response_raw = await self.websocket.recv()
            response = json.loads(response_raw)

            logger.info(f"[FR_BEST] Added person embedding: {person_id}")
            return response

        except Exception as e:
            logger.error(f"[FR_BEST] Add embedding failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def remove_person_embedding(self, person_id: str) -> Dict[str, Any]:
        """
        Remove person embedding from face recognition database.

        Args:
            person_id: Unique identifier for the person

        Returns:
            Dictionary containing operation result
        """
        try:
            await self._ensure_connected()

            request = {"type": "remove_person_embedding", "person_id": person_id}

            await self.websocket.send(json.dumps(request))
            response_raw = await self.websocket.recv()
            response = json.loads(response_raw)

            logger.info(f"[FR_BEST] Removed person embedding: {person_id}")
            return response

        except Exception as e:
            logger.error(f"[FR_BEST] Remove embedding failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def sync_embeddings(self, embeddings_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync embeddings with face recognition service.

        Args:
            embeddings_data: Dictionary of person_id -> embedding data

        Returns:
            Dictionary containing sync result
        """
        try:
            await self._ensure_connected()

            request = {"type": "sync_embeddings", "embeddings": embeddings_data}

            await self.websocket.send(json.dumps(request))
            response_raw = await self.websocket.recv()
            response = json.loads(response_raw)

            logger.info(f"[FR_BEST] Synced embeddings: {len(embeddings_data)} persons")
            return response

        except Exception as e:
            logger.error(f"[FR_BEST] Sync embeddings failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_connection_status(self) -> Dict[str, Any]:
        """Get connection status."""
        return {
            "connected": self.is_connected,
            "ws_url": self.ws_url,
            "reconnect_attempts": self.reconnect_attempts,
            "max_reconnect_attempts": self.max_reconnect_attempts,
        }


# Global instance for the application
face_recognition_client = FaceRecognitionClient()
