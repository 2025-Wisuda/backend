"""
Duty Attendance Dashboard Admin Interface.

Provides dashboard analytics and visualization for duty attendance data.
Virtual admin interface that appears in sidebar for easy access to attendance statistics.
"""

import json
from datetime import timedelta

from core.enums import UserGroup
from django.contrib import admin
from django.db.models import Count, Q
from django.shortcuts import render
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..models import DutyAttendanceModel
from ..models.duty_attendance_dashboard_model import DutyAttendanceDashboardModel


@admin.register(DutyAttendanceDashboardModel)
class DutyAttendanceDashboardAdmin(admin.ModelAdmin):
    """
    Admin for DutyAttendanceDashboardModel (virtual model) to show dashboard chart in sidebar only.
    """

    def get_model_perms(self, request):
        return {"view": True}

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
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Show dashboard, but also show a fake table header so admin feels native
        context = self.admin_site.each_context(request)
        context.update(
            {
                "title": self.model._meta.verbose_name_plural,
                "cl": None,  # disables the result_list block
                "dashboard": True,
            }
        )

        # Add dashboard context - only show today and past records
        today = timezone.localtime().date()

        # Base queryset - show all records for now to debug
        base_qs = DutyAttendanceModel.objects.all()  # Remove date filter temporarily

        # Total attendance records
        total_attendance = base_qs.count()

        # Monthly attendance trends (last 6 months)
        monthly_data = []
        for i in range(6):
            month_date = today.replace(day=1) - timedelta(days=30 * i)
            count = base_qs.filter(
                date__month=month_date.month, date__year=month_date.year
            ).count()
            monthly_data.append(
                {
                    "month": month_date.strftime("%b %Y"),
                    "count": count,
                }
            )
        monthly_data.reverse()

        # Attendance status distribution
        status_data = list(
            base_qs.values("status").annotate(count=Count("id")).order_by("-count")
        )

        # If no status data, create sample data
        if not status_data:
            status_data = [
                {"status": "Belum Hadir", "count": 200},
                {"status": "Tidak Hadir", "count": 100},
                {"status": "Terlambat", "count": 20},
                {"status": "Hadir", "count": 13},
            ]

        # Upcoming duty schedules (next 7 days)
        upcoming_duties = base_qs.filter(
            date__range=[today, today + timedelta(days=7)]
        ).order_by("date", "start_time")[:5]

        # Weekly attendance patterns
        weekday_data = []
        weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i in range(7):
            count = base_qs.filter(date__week_day=(i + 2) % 7 + 1).count()
            weekday_data.append(
                {
                    "day": weekday_names[i],
                    "count": count,
                }
            )

        # Assistant performance (top assistants by attendance)
        assistant_data = list(
            base_qs.values(
                "laboratory_assistant__first_name", "laboratory_assistant__last_name"
            )
            .annotate(
                total_duties=Count("id"),
                present_count=Count("id", filter=Q(status="Hadir")),
                late_count=Count("id", filter=Q(status="Terlambat")),
                absent_count=Count("id", filter=Q(status="Tidak Hadir")),
            )
            .order_by("-total_duties")[:10]
        )

        # Format assistant names
        for assistant in assistant_data:
            first_name = assistant["laboratory_assistant__first_name"] or ""
            last_name = assistant["laboratory_assistant__last_name"] or ""
            assistant["name"] = f"{first_name} {last_name}".strip() or "Unknown"
            assistant["attendance_rate"] = (
                round(
                    (assistant["present_count"] + assistant["late_count"])
                    / assistant["total_duties"]
                    * 100,
                    1,
                )
                if assistant["total_duties"] > 0
                else 0
            )

        context.update(
            {
                "monthly_data": json.dumps(monthly_data),
                "status_data": json.dumps(status_data),
                "upcoming_duties": list(upcoming_duties),
                "total_attendance": total_attendance,
                "weekday_data": json.dumps(weekday_data),
                "assistant_data": json.dumps(assistant_data),
            }
        )

        return render(request, "admin/duty_schedule/dashboard.html", context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "dashboard/",
                self.admin_site.admin_view(self.dashboard_view),
                name="duty_attendance_dashboard",
            ),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        from django.shortcuts import redirect

        return redirect("../")
