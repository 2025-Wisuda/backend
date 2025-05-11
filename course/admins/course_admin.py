from django import forms
from django.contrib import admin
from course.models import Course
from django.contrib.auth import get_user_model
from utils import bulk_update_is_active
from rest_framework import serializers

User = get_user_model()


class CourseAdminForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        instance = self.instance or Course()
        from course.validators import validate_course_fields

        try:
            validate_course_fields(cleaned_data, instance=instance)
        except serializers.ValidationError as e:
            for error in e.detail.values():
                self.add_error(None, error)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    form = CourseAdminForm
    list_display = (
        "title",
        "start_date",
        "end_date",
        "is_active",
    )
    list_filter = ("is_active", "start_date", "end_date")
    search_fields = ("title", "description")
    ordering = ("start_date",)
    actions = ["make_inactive", "make_active"]
    fieldsets = (
        (
            "Informasi Praktikum",
            {
                "fields": (
                    "title",
                    "description",
                    "start_date",
                    "end_date",
                    "enroll_key",
                    "created_by",
                )
            },
        ),
        (
            "Peserta Praktikum",
            {
                "fields": (
                    "students",
                    "teaching_assistants",
                )
            },
        ),
        (
            "Total Peserta",
            {
                "fields": (
                    "total_students",
                    "total_teaching_assistants",
                    "total_participants",
                )
            },
        ),
        ("Tanggal Penting", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = (
        "created_by",
        "total_students",
        "total_teaching_assistants",
        "total_participants",
        "created_at",
        "updated_at",
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        elif request.user.is_staff:
            return queryset.filter(is_active=True)
        return queryset.none()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "teaching_assistants":
            kwargs["queryset"] = User.objects.filter(is_active=True, is_staff=True)
        elif db_field.name == "students":
            kwargs["queryset"] = User.objects.filter(is_active=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.save()

    def make_inactive(self, request, queryset):
        message_bit = bulk_update_is_active(queryset, active=False)
        self.message_user(request, message_bit)

    make_inactive.short_description = "Hapus"

    def make_active(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(
                request, "Hanya superuser yang dapat memulihkan jadwal.", level="error"
            )

            return
        message_bit = bulk_update_is_active(queryset, active=True)
        self.message_user(request, message_bit)

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
