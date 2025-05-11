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
        "activity_description",
        "schedule_date",
        "start_time",
        "end_time",
        "approval_status",
        "is_active",
    )
    list_filter = (
        "is_active",
        "activity_type",
        "schedule_date",
        "approval_status",
    )
    search_fields = ("activity_description", "activity_type", "schedule_date")
    ordering = ("schedule_date", "start_time")
    fieldsets = (
        (
            "Detail Jadwal",
            {
                "fields": (
                    "activity_type",
                    "activity_description",
                    "schedule_date",
                    "start_time",
                    "end_time",
                    "created_by",
                )
            },
        ),
        (
            "Detail Persetujuan",
            {
                "fields": (
                    "approval_status",
                    "approved_by",
                    "approval_time",
                )
            },
        ),
        ("Tanggal Penting", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = (
        "activity_type",
        "activity_description",
        "schedule_date",
        "start_time",
        "end_time",
        "created_by",
        "approved_by",
        "approval_time",
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

    def has_add_permission(self, request):
        return False

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
