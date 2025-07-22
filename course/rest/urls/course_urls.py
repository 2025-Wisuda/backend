"""
URL configuration for course REST API endpoints.

This module provides URL routing for course and course session viewsets
using nested routing for better API structure following industry standards.
Also includes attendance management endpoints nested under sessions.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from ..views import CourseSessionAttendanceViewSet, CourseSessionViewSet, CourseViewSet

# Main router for courses
router = DefaultRouter(trailing_slash=False)
router.register(r"courses", CourseViewSet, basename="courses")

# Nested router for course sessions
courses_router = routers.NestedDefaultRouter(router, r"courses", lookup="course")
courses_router.register(r"sessions", CourseSessionViewSet, basename="course-sessions")

# Nested router for session attendance
sessions_router = routers.NestedDefaultRouter(
    courses_router, r"sessions", lookup="session"
)
sessions_router.register(
    r"attendances", CourseSessionAttendanceViewSet, basename="session-attendance"
)

# Combine all URLs
urlpatterns = (
    router.urls
    + courses_router.urls
    + sessions_router.urls
)
