from django import forms
from django.contrib import admin
from schedule.models import LabSchedule
from schedule.serializers import LabScheduleDetailSerializer
from rest_framework import serializers
from datetime import datetime
from utils import bulk_update_is_active


class LabScheduleAdminForm(forms.ModelForm):
    class Meta:
        model = LabSchedule
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        instance = self.instance or LabSchedule()
        serializer = LabScheduleDetailSerializer(
            instance=instance, data=cleaned_data, partial=True
        )

        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            for error in e.detail.values():
                self.add_error(None, error)


@admin.register(LabSchedule)
class LabScheduleAdmin(admin.ModelAdmin):
    form = LabScheduleAdminForm
    list_display = (
        "activity_type",
        "schedule_date",
        "start_time",
        "end_time",
        "is_active",
        "approval_status",
    )
    list_filter = (
        "is_active",
        "activity_type",
        "schedule_date",
        "approval_status",
    )
    search_fields = ("activity_description", "activity_type", "schedule_date")
    ordering = ("schedule_date", "start_time")
    actions = ["make_inactive", "make_active"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "activity_type",
                    "activity_description",
                    "schedule_date",
                    "start_time",
                    "end_time",
                    "created_by",
                    "is_active",
                    "approval_status",
                    "approved_by",
                    "approval_time",
                )
            },
        ),
        ("Important Dates", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = (
        "created_by",
        "created_at",
        "updated_at",
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(is_active=True)

    def make_inactive(self, request, queryset):
        message_bit = bulk_update_is_active(queryset, active=False)
        self.message_user(request, message_bit)

    make_inactive.short_description = "Tandai tidak aktif (Hapus)"

    def make_active(self, request, queryset):
        message_bit = bulk_update_is_active(queryset, active=True)
        self.message_user(request, message_bit)

    make_active.short_description = "Tandai aktif (Pulihkan)"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        if not change and (request.user.is_staff or request.user.is_superuser):
            obj.approval_status = "diterima"
            obj.approved_by = request.user
            obj.approval_time = datetime.now()
        obj.save()

    def has_delete_permission(self, request, obj=None):
        return False
