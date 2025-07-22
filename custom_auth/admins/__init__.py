"""
Custom Auth Admin Interface

Enhanced Django admin interface for user and group management.

This package provides:
- Enhanced user admin with role-based field organization
- Export functionality with filtering and customization
- Group management with permission control
- Audit trail display and management
- Laboratory-specific access controls

Admin Features:
- User management with role-based validation
- Bulk operations (activate/deactivate users)
- Advanced export with field selection and filtering
- Group/permission management (read-only for non-superusers)
- Responsive design with enhanced UX

Security:
- Laboratory employee access control
- Superuser-only sensitive operations
- Audit trail for all modifications
- Safe bulk operations with confirmations
"""

from .user_admin import UserAdmin
from .user_resource import UserResource

__all__ = [
    "UserAdmin",
    "UserResource",
]
