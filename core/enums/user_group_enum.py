from enum import Enum

from django.utils.translation import gettext_lazy as _


class UserGroup(str, Enum):
    """
    Enumeration of user groups in the laboratory management system.
    Stores group names in Indonesian for consistent DB storage.
    """

    LABORATORY_HEAD = "Kepala Laboratorium"
    LABORATORY_TECHNICIAN = "Teknisi Laboratorium"
    LABORATORY_ASSISTANT = "Asisten Laboratorium"
    LECTURER = "Dosen"
    STUDENT = "Mahasiswa"

    @classmethod
    def choices(cls):
        """
        Return list of (value, label) tuples for Django model field choices.
        Both are Indonesian strings stored in the database.
        """
        return [(item.value, item.value) for item in cls]

    @classmethod
    def staff_groups(cls):
        """
        Return list of staff group values.
        Staff groups: Laboratory Head, Laboratory Technician, Lecturer
        """
        return [
            cls.LABORATORY_HEAD.value,
            cls.LABORATORY_TECHNICIAN.value,
            cls.LECTURER.value,
        ]

    @classmethod
    def student_groups(cls):
        """
        Return list of student group values.
        Student groups: Laboratory Assistant, Student
        """
        return [
            cls.LABORATORY_ASSISTANT.value,
            cls.STUDENT.value,
        ]

    @classmethod
    def laboratory_staff_employee_groups(cls):
        """
        Return list of employee groups that are considered laboratory staff.
        Includes Laboratory Head, Technician, and Assistant.
        """
        return [
            cls.LABORATORY_HEAD.value,
            cls.LABORATORY_TECHNICIAN.value,
        ]

    @classmethod
    def is_laboratory_staff_employee_group(cls, group_value):
        """
        Check if a group value is a laboratory staff employee group.
        """
        return group_value in cls.laboratory_staff_employee_groups()

    @classmethod
    def is_staff_group(cls, group_value):
        """
        Check if a group value is a staff group.
        """
        return group_value in cls.staff_groups()

    @classmethod
    def is_student_group(cls, group_value):
        """
        Check if a group value is a student group.
        """
        return group_value in cls.student_groups()

    @classmethod
    def is_admin_staff_groups(cls):
        """
        Return list of groups that should have is_staff=True in Django admin.
        Includes Laboratory Assistant for admin access purposes.
        """
        return [
            cls.LABORATORY_HEAD.value,
            cls.LABORATORY_TECHNICIAN.value,
            cls.LABORATORY_ASSISTANT.value,
        ]

    def display_label(self):
        """
        Return translated label for display in admin or API according to current language.
        """
        return _(self.value)
