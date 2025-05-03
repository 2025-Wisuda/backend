from django.contrib import admin
from schedule.models import DutyDate


@admin.register(DutyDate)
class DutyDateAdmin(admin.ModelAdmin):
    list_display = ("duty_date", "schedule")
    list_filter = ("schedule",)
    search_fields = ("duty_date", "schedule__days")
    ordering = ("duty_date", "schedule")
    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.save()

    def has_delete_permission(self, request, obj=None):
        return False
