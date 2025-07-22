"""
User Views

ViewSet for user management operations with role-based access control.
Provides CRUD operations, filtering, search, and profile management.

Features:
- List users with filtering and search
- Retrieve user details
- Profile management (self-service)
- Optimized queries with select_related

Permissions:
- List/Retrieve: Authenticated users
- Profile operations: Self-service only
"""

from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import GenericViewSet
from shared.presenter import ResponsePresenter

from ..filters.user_filters import UserFilter
from ..schemas import (  # user_detail_schema,
    update_user_profile_schema,
    user_list_schema,
    user_profile_schema,
)
from ..serializers import (
    UserDetailSerializer,
    UserListSerializer,
    UserProfileSerializer,
)

User = get_user_model()


class UserViewSet(mixins.ListModelMixin, GenericViewSet):
    """
    ViewSet for user management operations.

    Features:
    - List users with filtering and search
    - Retrieve user details
    - Profile management (self-service)
    - Optimized queries with select_related

    Permissions:
    - List/Retrieve: Authenticated users
    - Profile operations: Self-service only
    """

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = UserFilter
    search_fields = ["username", "first_name", "last_name"]

    def get_queryset(self):
        """
        Optimized queryset with data visibility controls.

        Profile endpoints: Self-service only
        General endpoints: Active users with optimized joins
        """
        if self.action in ["profile"]:
            return User.objects.filter(id=self.request.user.id)
        queryset = User.objects.filter(is_active=True)
        queryset = queryset.select_related("created_by", "updated_by")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return UserListSerializer
        elif self.action == "retrieve":
            return UserDetailSerializer
        elif self.action == "profile":
            return UserProfileSerializer
        return UserDetailSerializer

    @user_list_schema
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return ResponsePresenter.success_response(
            message="Users retrieved successfully", data=serializer.data
        )

    # @user_detail_schema
    # def retrieve(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance)
    #     return ResponsePresenter.success_response(
    #         message="User details retrieved successfully", data=serializer.data
    #     )

    @update_user_profile_schema
    @action(detail=False, methods=["get", "patch"], url_path="me")
    def profile(self, request):
        """
        User profile management endpoint.

        GET: Returns authenticated user's profile information
        PATCH: Updates current user profile with restricted field access

        Sensitive fields (group, staff status) are read-only for updates.
        """
        if request.method == "GET":
            serializer = self.get_serializer(request.user)
            return ResponsePresenter.success_response(
                message="Profile retrieved successfully", data=serializer.data
            )

        elif request.method == "PATCH":
            try:
                serializer = self.get_serializer(
                    request.user, data=request.data, partial=True
                )
                if serializer.is_valid():
                    updated_user = serializer.save(updated_by=request.user)
                    # Return fresh data from database
                    fresh_serializer = self.get_serializer(updated_user)
                    return ResponsePresenter.success_response(
                        message="Profile updated successfully",
                        data=fresh_serializer.data,
                    )
                return ResponsePresenter.bad_request_response(
                    message="Failed to update profile", errors=serializer.errors
                )
            except Exception as e:
                return ResponsePresenter.bad_request_response(
                    message="An error occurred while updating profile",
                    errors={"detail": str(e)},
                )
