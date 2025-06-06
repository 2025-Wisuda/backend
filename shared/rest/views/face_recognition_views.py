"""
Face Recognition API Views.

Provides REST API endpoints for face recognition operations
that can be used across different modules.
"""

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shared.rest.serializers.face_recognition_serializers import (
    FaceRecognitionProcessSerializer,
    FaceRecognitionResultSerializer,
    FaceRecognitionStatsSerializer,
    FaceRegistrationResultSerializer,
    FaceRegistrationSerializer,
    FaceVerificationResultSerializer,
    FaceVerificationSerializer,
    UserWithoutFaceDataSerializer,
)
from shared.services import get_face_recognition_service

User = get_user_model()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def process_face_recognition(request):
    """
    Process face recognition for an image.

    This endpoint can be used by any module that needs face recognition.
    """
    serializer = FaceRecognitionProcessSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    image = serializer.validated_data["image"]
    context = serializer.validated_data.get("context", {})
    min_confidence = serializer.validated_data.get("min_confidence")

    # Add request user to context
    context["request_user_id"] = request.user.id

    # Get face recognition service
    service = get_face_recognition_service(min_confidence=min_confidence)

    # Process the image
    result = service.process_face_image(image, context)

    # Serialize the result
    result_serializer = FaceRecognitionResultSerializer(result)

    return Response(
        {
            "success": True,
            "message": _("Face recognition processed successfully"),
            "data": result_serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_user_face(request):
    """
    Register a face image for a user.
    """
    serializer = FaceRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user_id = serializer.validated_data["user_id"]
    image = serializer.validated_data["image"]

    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        return Response(
            {"success": False, "message": _("User not found or inactive")},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Get face recognition service
    service = get_face_recognition_service()

    # Register the face
    result = service.register_user_face(user, image)

    # Serialize the result
    result_serializer = FaceRegistrationResultSerializer(result)

    return Response(
        {
            "success": result["success"],
            "message": result["message"],
            "data": result_serializer.data,
        },
        status=status.HTTP_200_OK if result["success"] else status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_user_face(request):
    """
    Verify if a face image matches a registered user.
    """
    serializer = FaceVerificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user_id = serializer.validated_data["user_id"]
    image = serializer.validated_data["image"]

    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        return Response(
            {"success": False, "message": _("User not found or inactive")},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Get face recognition service
    service = get_face_recognition_service()

    # Verify the face
    result = service.verify_user_face(user, image)

    # Serialize the result
    result_serializer = FaceVerificationResultSerializer(result)

    return Response(
        {
            "success": result["success"],
            "message": _("Face verification completed"),
            "data": result_serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def identify_user_from_face(request):
    """
    Identify a user from their face image.
    """
    serializer = FaceRecognitionProcessSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    image = serializer.validated_data["image"]
    min_confidence = serializer.validated_data.get("min_confidence")

    # Get face recognition service
    service = get_face_recognition_service(min_confidence=min_confidence)

    # Identify the user
    identified_user = service.identify_user_from_face(image)

    if identified_user:
        return Response(
            {
                "success": True,
                "message": _("User identified successfully"),
                "data": {
                    "identified_user": {
                        "id": identified_user.id,
                        "username": identified_user.username,
                        "full_name": identified_user.get_full_name(),
                        "email": identified_user.email,
                    }
                },
            },
            status=status.HTTP_200_OK,
        )
    else:
        return Response(
            {
                "success": False,
                "message": _("Could not identify user from face image"),
                "data": {"identified_user": None},
            },
            status=status.HTTP_200_OK,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_face_recognition_stats(request):
    """
    Get face recognition statistics.
    """
    service = get_face_recognition_service()
    stats = service.get_face_recognition_stats()

    result_serializer = FaceRecognitionStatsSerializer(stats)

    return Response(
        {
            "success": True,
            "message": _("Face recognition statistics retrieved"),
            "data": result_serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_users_without_face_data(request):
    """
    Get users who haven't set up face recognition yet.
    """
    service = get_face_recognition_service()
    users = service.get_users_without_face_data()

    result_serializer = UserWithoutFaceDataSerializer(users, many=True)

    return Response(
        {
            "success": True,
            "message": _("Users without face data retrieved"),
            "data": result_serializer.data,
        },
        status=status.HTTP_200_OK,
    )
