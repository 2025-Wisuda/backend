"""
Django admin configuration for Duty Attendance management.

Provides admin interface for duty attendance records with role-based access control
and collapsible sections for better organization.
"""

from core.enums import UserGroup
from django.contrib import admin
from django.db.models import Q
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from shared.utils import AuditFieldMixin

from ..models import DutyAttendanceModel


class DutyAttendanceFilter(admin.SimpleListFilter):
    """Filter duty attendance by month."""

    title = _("Month")
    parameter_name = "month"

    def lookups(self, request, model_admin):
        """Return month options for filter."""
        from datetime import datetime, timedelta

        # Get last 12 months
        months = []
        today = timezone.localtime().date()

        for i in range(12):
            month_date = today.replace(day=1) - timedelta(days=30 * i)
            month_name = month_date.strftime("%B %Y")
            month_value = month_date.strftime("%Y-%m")
            months.append((month_value, month_name))

        return months

    def queryset(self, request, queryset):
        """Filter queryset by selected month."""
        if self.value():
            year, month = self.value().split("-")
            return queryset.filter(date__year=int(year), date__month=int(month))
        return queryset


@admin.register(DutyAttendanceModel)
class DutyAttendanceAdmin(AuditFieldMixin, admin.ModelAdmin):
    """
    Admin interface for duty attendance records with collapsible sections.
    """

    list_display = [
        "laboratory_assistant",
        "date",
        "status_display",
        "clock_in_display",
        "clock_out_display",
    ]

    list_filter = [
        DutyAttendanceFilter,
        "status",
        "laboratory_assistant",
    ]

    search_fields = [
        "laboratory_assistant__first_name",
        "laboratory_assistant__last_name",
        "laboratory_assistant__username",
    ]

    readonly_fields = (
        "laboratory_assistant",
        "date",
        "start_time",
        "end_time",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    )

    ordering = ["-date", "-start_time"]

    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "laboratory_assistant",
                    "date",
                    "start_time",
                    "end_time",
                ),
                "description": _("Duty schedule information and assigned assistant."),
                "classes": ("collapse",),

            },
        ),
        (
            _("Attendance Details"),
            {
                "fields": (
                    "status",
                    "clock_in_time",
                    "clock_out_time",
                ),
                "description": _("Attendance status and time tracking information."),
            },
        ),
        (
            _("Important Dates"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Audit Info"),
            {
                "fields": ("created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        """
        Optimize queryset with select_related and filter by current date backwards.
        """
        today = timezone.localtime().date()
        qs = (
            super()
            .get_queryset(request)
            .select_related("laboratory_assistant", "created_by", "updated_by")
            .filter(date__lte=today)  # Only show today and past records
            .order_by("-date", "-start_time")
        )
        return qs

    def time_display(self, obj):
        """Display formatted time range."""
        if obj.start_time and obj.end_time:
            return (
                f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
            )
        return "-"

    time_display.short_description = _("Time")

    def clock_in_display(self, obj):
        """Display clock in time with formatting."""
        if obj.clock_in_time:
            return obj.clock_in_time.strftime("%d %B %Y, %H.%M")
        return "-"

    clock_in_display.short_description = _("Clock In Time")

    def clock_out_display(self, obj):
        """Display clock out time with formatting."""
        if obj.clock_out_time:
            return obj.clock_out_time.strftime("%d %B %Y, %H.%M")
        return "-"

    clock_out_display.short_description = _("Clock Out Time")

    def status_display(self, obj):
        """Display status with color coding."""
        status_colors = {
            "Hadir": "#34d399",
            "Terlambat": "#fbbf24",
            "Tidak Hadir": "#f87171",
            "Belum Hadir": "#94a3b8",
        }
        color = status_colors.get(obj.status, "#94a3b8")
        return mark_safe(
            f'<span style="color: {color}; font-weight: 600;">{obj.status}</span>'
        )

    status_display.short_description = _("Status")

    def has_module_permission(self, request):
        """Control module access based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group in UserGroup.laboratory_staff_employee_groups():
            return True
        return False

    def has_view_permission(self, request, obj=None):
        """Control view permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group in UserGroup.laboratory_staff_employee_groups():
            return True
        return False

    def has_add_permission(self, request):
        """No add permission - records are auto-generated."""
        return False

    def has_change_permission(self, request, obj=None):
        """Control change permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        """No delete permission - records are auto-generated."""
        return False
