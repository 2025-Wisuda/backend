from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from import_export.admin import ImportExportMixin
from .models import User
from .resources import UserResource

@admin.register(User)
class UserAdmin(ImportExportMixin, BaseUserAdmin):
    resource_class = UserResource
    model = User
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'student_id', 'employee_id', 'is_staff', 'is_active'
    )
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('username', 'email', 'student_id', 'employee_id')
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Information', {'fields': (
            'first_name', 'last_name', 'email', 'student_id', 'employee_id',
            'avatar', 'face_image', 'face_uploaded'
        )}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )