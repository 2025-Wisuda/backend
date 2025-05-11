from django import forms
from django.contrib import admin
from schedule.models import DutySchedule
from schedule.serializers import DutyScheduleDetailSerializer
from rest_framework import serializers
from schedule.utils import generate_duty_dates
from utils import bulk_update_is_active
from django.contrib.auth import get_user_model

User = get_user_model()


class DutyScheduleAdminForm(forms.ModelForm):
    class Meta:
        model = DutySchedule
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        instance = self.instance or DutySchedule()
        serializer = DutyScheduleDetailSerializer(
            instance=instance, data=cleaned_data, partial=True
        )

        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            for error in e.detail.values():
                self.add_error(None, error)


@admin.register(DutySchedule)
class DutyScheduleAdmin(admin.ModelAdmin):
    form = DutyScheduleAdminForm
    list_display = (
        "days",
        "get_teaching_assistants",
        "is_active",
    )
    list_filter = (
        "is_active",
        "days",
    )
    search_fields = ("days", "teaching_assistants")
    ordering = ("start_date", "start_time")
    actions = ["make_inactive", "make_active"]
    fieldsets = (
        (
            "Informasi Jadwal Piket",
            {
                "fields": (
                    "days",
                    "start_date",
                    "end_date",
                    "start_time",
                    "end_time",
                    "teaching_assistants",
                )
            },
        ),
        ("Tanggal Penting", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        elif request.user.is_staff:
            return queryset.filter(is_active=True)
        return queryset.none()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "teaching_assistants":
            kwargs["queryset"] = User.objects.filter(is_staff=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def make_inactive(self, request, queryset):
        message_bit = bulk_update_is_active(queryset, active=False)
        self.message_user(request, message_bit)

    make_inactive.short_description = "Hapus"

    def make_active(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(
                request, "Only superusers can perform this action.", level="error"
            )
            return
        message_bit = bulk_update_is_active(queryset, active=True)
        self.message_user(request, message_bit)

    make_active.short_description = "Pulihkan"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.save()
            generate_duty_dates(obj)

    def assign_duty_dates(self):
        generate_duty_dates(self)

    def get_teaching_assistants(self, obj):
        return ", ".join([str(user) for user in obj.teaching_assistants.all()])

    get_teaching_assistants.short_description = "Asisten"

    def has_delete_permission(self, request, obj=None):
        return False
