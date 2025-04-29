from django.contrib import admin
from import_export.admin import ImportExportMixin
from .models import LabSchedule


@admin.register(LabSchedule)
class LabScheduleAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        "activity_type",
        "schedule_date",
        "start_time",
        "end_time",
        "is_active",
    )
    list_filter = ("is_active", "activity_type", "schedule_date")
    search_fields = ("activity_description", "activity_type", "schedule_date")
    ordering = ("schedule_date", "start_time")
    actions = ["make_inactive"]
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
                )
            },
        ),
        ("Important Dates", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_by", "created_at", "updated_at")

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.save()
