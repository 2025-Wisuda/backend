"""
Course admin configuration.
Imports all admin classes for the course app.
"""

# Import all admin classes - they are auto-registered via @admin.register decorators
from .admins import (
    CourseAdmin,
    CourseResource,
    CourseSessionAdmin,
    CourseSessionAttendanceAdmin,
    CourseSessionResource,
)

# All admin classes are registered within their respective files
