from drf_spectacular.utils import OpenApiParameter, extend_schema
from shared.schemas import ResponseSchema

from ..serializers.fcm_device_serializer import (
    FCMDeviceSerializer,
    RegisterDeviceResponseSerializer,
    SendTestNotificationResponseSerializer,
)

device_list_schema = extend_schema(
    responses=ResponseSchema.get_response_schema(
        FCMDeviceSerializer, name="DeviceListResponse"
    ),
    summary="List FCM devices",
    description="Retrieve a list of FCM devices registered for the current user.",
    tags=["Notification"],
)

device_register_schema = extend_schema(
    request=None,
    responses=ResponseSchema.get_response_schema(
        RegisterDeviceResponseSerializer, name="RegisterDeviceResponse"
    ),
    parameters=[
        OpenApiParameter(
            "token", type=str, description="FCM device token", required=True
        ),
        OpenApiParameter(
            "device_type",
            type=str,
            description="Device type (android/ios)",
            required=False,
        ),
    ],
    summary="Register FCM device",
    description="Register a new FCM device for the current user.",
    tags=["Notification"],
)

device_send_test_schema = extend_schema(
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Notification title",
                    "example": "Test Notification",
                },
                "body": {
                    "type": "string",
                    "description": "Notification body",
                    "example": "This is a test notification",
                },
            },
        }
    },
    responses=ResponseSchema.get_response_schema(
        SendTestNotificationResponseSerializer, name="SendTestNotificationResponse"
    ),
    summary="Send test notification",
    description="Send a test push notification to all devices of the current user.",
    tags=["Notification"],
)

unregister_device_schema = extend_schema(
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "FCM registration token to unregister",
                },
            },
            "required": ["token"],
        }
    },
    responses=ResponseSchema.get_response_schema(
        FCMDeviceSerializer, name="UnregisterDeviceResponse"
    ),
    summary="Unregister FCM device",
    description="Unregister (delete) an FCM device for the current user by token.",
    tags=["Notification"],
)
