# Custom Authentication Module

## Overview

The `custom_auth` module is a comprehensive user management and authentication system designed specifically for laboratory management. It extends Django's built-in authentication with laboratory-specific features including role-based user validation, face recognition integration, and advanced admin capabilities.

## Architecture

### Model Layer
- **CustomUserModel**: Extended AbstractUser with laboratory-specific fields
  - UUID primary key for enhanced security
  - Role-based identifier validation (student_number/employee_number)
  - Face recognition support for attendance tracking
  - Audit trail with created_by/updated_by tracking
  - Profile image and avatar support

### REST API Layer
```
rest/
├── filters/           # Django-filters for queryset filtering
├── schemas/           # OpenAPI documentation schemas
├── serializers/       # DRF serializers for data validation
├── views/            # ViewSets for API endpoints
└── urls/             # URL routing configuration
```

#### Key Features:
- **Authentication**: JWT-based with secure token management
- **User Management**: CRUD operations with filtering and search
- **Profile Management**: Self-service user profile updates
- **Role-based Access**: Different serializer levels for security

### Admin Interface
```
admins/
├── forms/            # Export forms with custom filtering
├── views/            # Enhanced admin views with export capability
├── user_admin.py     # Main user admin configuration
├── group_admin.py    # Group management admin
└── admin_config.py   # Central admin configuration
```

#### Admin Features:
- Enhanced user management with role-based field organization
- Advanced export functionality with filtering
- Group/permission management (controlled access)
- Audit trail display and bulk operations
- Laboratory employee access controls

## Key Components

### User Model Validation
The model implements sophisticated validation rules:
- **Staff groups**: Require employee_number, prohibit student_number
- **Student groups**: Require student_number, prohibit employee_number
- **Group field**: Mandatory for all users
- **Image validation**: For avatar and face_image fields

### Authentication Flow
1. **Login**: Username/password → JWT access/refresh tokens
2. **API Access**: Use access token in Authorization header
3. **Token Refresh**: Automatic refresh when access token expires
4. **Logout**: Blacklist refresh token for security

### Export System
- **Field Selection**: Choose specific fields for export
- **Group Filtering**: Filter by user roles/groups
- **Security**: Excludes superusers from exports
- **Custom Filenames**: Generated based on applied filters

## API Endpoints

### Authentication
- `POST /auth/login` - Obtain JWT tokens
- `POST /auth/refresh-token` - Refresh access token
- `POST /auth/change-password` - Change user password
- `POST /auth/logout` - Invalidate refresh token

### User Management
- `GET /users` - List users with filtering and search
- `GET /users/{id}` - Retrieve user details
- `GET /users/me` - Current user profile
- `PATCH /users/me/update` - Update current user profile

## Security Features

### Access Control
- **Laboratory Employee Only**: Admin access restricted to lab staff
- **Role-based Fields**: Different field access based on user role
- **Audit Trail**: Track all user modifications
- **Superuser Protection**: Prevent export/modification of admin accounts

### Data Validation
- **Password Strength**: Django's built-in password validators
- **Email Validation**: Format and uniqueness checks
- **Image Validation**: File type and size validation
- **Role Consistency**: Enforce identifier requirements per role

## Usage Examples

### API Usage
```python
# Login and get tokens
response = requests.post('/auth/login', {
    'username': 'user@example.com',
    'password': 'secure_password'
})
tokens = response.json()

# Use access token for API calls
headers = {'Authorization': f"Bearer {tokens['access']}"}
users = requests.get('/users', headers=headers)

# Update profile
profile_data = {'first_name': 'John', 'last_name': 'Doe'}
requests.patch('/users/me/update', json=profile_data, headers=headers)
```

### Admin Export
1. Navigate to User admin changelist
2. Click "Export Users" button
3. Select fields and apply filters
4. Download formatted export file

## Configuration

### Settings Requirements
```python
# Required in Django settings
AUTH_USER_MODEL = 'custom_auth.CustomUserModel'

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# File Upload Settings
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### URL Configuration
```python
# In main urls.py
urlpatterns = [
    path('api/v1/', include('custom_auth.urls')),
]
```

## Extension Points

### Custom Validation
Extend model validation by overriding `clean()` method:
```python
def clean(self):
    super().clean()
    # Add custom validation logic
```

### Additional Fields
Add laboratory-specific fields by extending the model:
```python
class CustomUserModel(AbstractUser):
    # Existing fields...
    lab_access_level = models.CharField(...)
    equipment_certifications = models.ManyToManyField(...)
```

### Custom Admin Actions
Add bulk operations in admin:
```python
@admin.action(description='Custom bulk action')
def custom_bulk_action(modeladmin, request, queryset):
    # Implementation
```

## Maintenance

### Regular Tasks
- Monitor user activity logs
- Clean up expired JWT tokens
- Backup user profile images
- Review and update user roles
- Audit access permissions

### Security Monitoring
- Failed login attempts
- Unusual API access patterns
- Admin action logs
- Export activity tracking

## Dependencies

- Django >= 3.2
- djangorestframework >= 3.12
- djangorestframework-simplejwt >= 4.6
- django-filter >= 2.4
- drf-spectacular >= 0.20
- Pillow >= 8.0 (for image handling)

## Testing

The module includes comprehensive test coverage for:
- Model validation rules
- API endpoint functionality
- Authentication flow
- Admin interface operations
- Export functionality
- Security controls

Run tests with:
```bash
python manage.py test custom_auth
```
