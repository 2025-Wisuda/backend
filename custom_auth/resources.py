from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from django.contrib.auth.models import Group
from django.utils.text import slugify
from .models import User

class UserResource(resources.ModelResource):
    group = fields.Field(
        column_name='group',
        attribute='groups',
        widget=ForeignKeyWidget(Group, 'name')
    )

    class Meta:
        model = User
        import_id_fields = []  
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'student_id', 'employee_id', 'is_active', 'is_staff',
            'is_superuser', 'date_joined', 'last_login',
            'avatar', 'face_image', 'face_uploaded', 'group'
        )

    def skip_row(self, instance, original, row, import_validation_errors=None):
        first_name = row.get('first_name', '').strip()
        last_name = row.get('last_name', '').strip()
        return not first_name or not last_name

    def before_import_row(self, row, **kwargs):
        first_name = str(row.get('first_name', '')).strip().lower()
        last_name = str(row.get('last_name', '')).strip().lower()
        student_id = str(row.get('student_id', '')).strip()
        employee_id = str(row.get('employee_id', '')).strip()

        base_username = f"{first_name[0]}{last_name}".replace(' ', '')
        username = slugify(base_username)

        suffix = ''
        extra_index = 2

        while User.objects.filter(username=username + suffix).exists():
            suffix = ''
            if student_id and len(student_id) >= extra_index:
                suffix = student_id[:extra_index]
            elif employee_id and len(employee_id) >= extra_index:
                suffix = employee_id[:extra_index]
            else:
                suffix = str(extra_index - 1)
            extra_index += 1

        final_username = username + suffix
        row['username'] = final_username
        row['password'] = final_username
