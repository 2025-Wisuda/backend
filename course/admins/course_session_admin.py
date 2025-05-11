from django import forms
from django.contrib import admin
from course.models import CourseSession, Course
from course.serializers import CourseSessionDetailSerializer
from django.contrib.auth import get_user_model
from utils import bulk_update_is_active
from rest_framework import serializers
from schedule.models import LabSchedule
from schedule.validators import validate_lab_schedule_fields
from django.utils import timezone

User = get_user_model()


class CourseSessionAdminForm(forms.ModelForm):
    class Meta:
        model = CourseSession
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        serializer = CourseSessionDetailSerializer(
            instance=self.instance,
            data={
                **cleaned_data,
                "course": (
                    cleaned_data["course"].id if cleaned_data.get("course") else None
                ),
                "teaching_assistants": [
                    ta.id for ta in cleaned_data.get("teaching_assistants", [])
                ],
            },
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        lab_schedule_data = {
            "activity_type": LabSchedule.ActivityType.PRACTICUM,
            "activity_description": f"{cleaned_data.get('title')}",
            "schedule_date": cleaned_data.get("session_date"),
            "start_time": cleaned_data.get("start_time"),
            "end_time": cleaned_data.get("end_time"),
        }
        try:
            validate_lab_schedule_fields(lab_schedule_data)
        except serializers.ValidationError as e:
            raise forms.ValidationError(e.detail)
        return cleaned_data


@admin.register(CourseSession)
class CourseSessionAdmin(admin.ModelAdmin):
    form = CourseSessionAdminForm
    list_display = (
        "title",
        "course",
        "session_date",
        "start_time",
        "end_time",
        "status",
        "is_active",
    )
    list_filter = ("status", "session_date", "is_active")
    search_fields = ("title", "course__title")
    ordering = ("session_date", "course__title", "status")
    actions = ["make_inactive", "make_active"]
    fieldsets = (
        (
            "Informasi Pertemuan Praktikum",
            {
                "fields": (
                    "title",
                    "course",
                    "session_date",
                    "start_time",
                    "end_time",
                    "status",
                    "teaching_assistants",
                    "created_by",
                )
            },
        ),
        ("Tanggal Penting", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_by", "created_at", "updated_at")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        elif request.user.is_staff:
            return queryset.filter(is_active=True)
        return queryset.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "course":
            kwargs["queryset"] = Course.objects.filter(is_active=True)
        elif db_field.name == "teaching_assistants":
            kwargs["queryset"] = User.objects.filter(is_active=True, is_staff=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            obj.save()
            lab_schedule_data = {
                "activity_type": LabSchedule.ActivityType.PRACTICUM,
                "activity_description": f"{obj.title}",
                "schedule_date": obj.session_date,
                "start_time": obj.start_time,
                "end_time": obj.end_time,
                "created_by": request.user,
            }
            if request.user.is_staff or request.user.is_superuser:
                lab_schedule_data.update(
                    {
                        "approval_status": LabSchedule.ApprovalStatus.APPROVED,
                        "approved_by": request.user,
                        "approval_time": timezone.now(),
                    }
                )
            validate_lab_schedule_fields(lab_schedule_data)
            lab_schedule = LabSchedule.objects.create(**lab_schedule_data)
            obj.lab_schedule = lab_schedule
            obj.save()
        else:
            old_obj = CourseSession.objects.get(pk=obj.pk)
            obj.save()
            if obj.lab_schedule:
                obj.lab_schedule.activity_description = obj.title
                obj.lab_schedule.schedule_date = obj.session_date
                obj.lab_schedule.start_time = obj.start_time
                obj.lab_schedule.end_time = obj.end_time
                obj.lab_schedule.save()

    def make_inactive(self, request, queryset):
        lab_schedules = LabSchedule.objects.filter(course_session__in=queryset)
        lab_schedules.update(is_active=False)
        message = bulk_update_is_active(queryset, active=False)
        self.message_user(request, message)

    def make_active(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(
                request, "Hanya superuser yang dapat memulihkan jadwal.", level="error"
            )
            return
        lab_schedules = LabSchedule.objects.filter(course_session__in=queryset)
        lab_schedules.update(is_active=True)
        message = bulk_update_is_active(queryset, active=True)
        self.message_user(request, message)

    make_inactive.short_description = "Hapus"
    make_active.short_description = "Pulihkan"

    def get_teaching_assistants(self, obj):
        teaching_assistants = obj.teaching_assistants.all()
        return ", ".join(
            [
                (
                    f"{user.first_name} {user.last_name}"
                    if user.first_name and user.last_name
                    else user.username
                )
                for user in teaching_assistants
            ]
        )

    get_teaching_assistants.short_description = "Asisten"

    def has_delete_permission(self, request, obj=None):
        return False
