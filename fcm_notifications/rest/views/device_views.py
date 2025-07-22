"""
Device Management Views - Essential endpoints only
"""

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from shared.presenter import ResponsePresenter

from ...models import FCMDeviceModel
from ...services import FCMService
from ..schemas.device_schema import (
    device_list_schema,
    device_register_schema,
    device_send_test_schema,
    unregister_device_schema,
)
from ..serializers import (
    FCMDeviceSerializer,
    RegisterDeviceResponseSerializer,
    SendTestNotificationResponseSerializer,
)


class DeviceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for FCM device management endpoints (list, register, send test notification).
    """

    serializer_class = FCMDeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FCMDeviceModel.objects.filter(user=self.request.user)

    @extend_schema(exclude=True)
    def retrieve(self, request, *args, **kwargs):
        return ResponsePresenter.bad_request_response(message="Not implemented.")

    @device_list_schema
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return ResponsePresenter.success_response(
            message="Devices retrieved successfully",
            data={"devices": serializer.data, "count": queryset.count()},
        )

    @device_register_schema
    @action(detail=False, methods=["post"], url_path="register-device")
    def register_device(self, request):
        token = request.data.get("token")
        device_type = request.data.get("device_type", "android")
        device_name = request.data.get("device_name")
        if not token:
            return ResponsePresenter.bad_request_response(message="Token is required")
        # Gunakan helper model agar device selalu aktif dan policy konsisten
        device = FCMDeviceModel.register_device(
            user=request.user,
            token=token,
            device_type=device_type,
            device_name=device_name,
        )
        serializer = RegisterDeviceResponseSerializer({"device_id": device.id})
        return ResponsePresenter.created_response(
            message="Device registered successfully",
            data=serializer.data,
        )

    @unregister_device_schema
    @action(detail=False, methods=["post"], url_path="unregister-device")
    def unregister_device(self, request):
        token = request.data.get("token")
        if not token:
            return ResponsePresenter.bad_request_response(message="Token is required")

        # INDUSTRY BEST PRACTICE: Deactivate instead of delete
        # This preserves audit trail and allows for better token management
        devices = FCMDeviceModel.objects.filter(
            user=request.user, registration_token=token
        )

        if devices.exists():
            # Deactivate all devices with this token for this user
            devices.update(is_active=False)
            return ResponsePresenter.success_response(
                message="Device unregistered successfully"
            )
        else:
            return ResponsePresenter.bad_request_response(message="Device not found")

    @device_send_test_schema
    @action(detail=False, methods=["post"], url_path="send-test")
    def send_test_notification(self, request):
        title = (
            request.data.get("title")
            or request.query_params.get("title")
            or "Test Notification"
        )
        body = (
            request.data.get("body")
            or request.query_params.get("body")
            or "This is a test notification"
        )
        fcm_service = FCMService()
        result = fcm_service.test_notification(
            user=request.user, test_message=f"{title}: {body}"
        )
        serializer = SendTestNotificationResponseSerializer({"success": bool(result)})
        if result:
            return ResponsePresenter.success_response(
                message="Test notification sent successfully",
                data=serializer.data,
            )
        else:
            return ResponsePresenter.internal_server_error_response(
                message="Failed to send test notification"
            )
