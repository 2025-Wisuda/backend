"""
Lab Schedule Dashboard Admin Interface.

Provides dashboard analytics and visualization for laboratory scheduling data.
Virtual admin interface that appears in sidebar for easy access to scheduling statistics.
"""

import json
from datetime import timedelta

from core.enums import UserGroup
from django.contrib import admin
from django.db.models import Count
from django.shortcuts import render
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..models import LabScheduleModel
from ..models.lab_schedule_dashboard_model import LabScheduleDashboardModel


class LabScheduleDashboardAdmin(admin.ModelAdmin):
    """
    Admin for LabScheduleDashboardModel (virtual model) to show dashboard chart in sidebar only.
    """

    def get_model_perms(self, request):
        # Only show in sidebar, no add/change/delete/list
        return {"view": True}

    def has_module_permission(self, request):
        """Control module access based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group in UserGroup.laboratory_staff_employee_groups():
            return True
        elif request.user.group == UserGroup.LABORATORY_ASSISTANT.value:
            return True
        return False

    def has_view_permission(self, request, obj=None):
        """Control view permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group in UserGroup.laboratory_staff_employee_groups():
            return True
        elif request.user.group == UserGroup.LABORATORY_ASSISTANT.value:
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
        # Add your dashboard context
        today = timezone.localtime().date()
        monthly_data = [
            {
                "month": (today.replace(day=1) - timedelta(days=30 * i)).strftime(
                    "%b %Y"
                ),
                "count": LabScheduleModel.objects.filter(
                    date__month=(today.month - i) % 12
                ).count(),
            }
            for i in range(6)
        ][::-1]
        activity_data = list(
            LabScheduleModel.objects.values("type")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )
        upcoming_schedules = LabScheduleModel.objects.filter(
            date__range=[today, today + timedelta(days=7)]
        ).order_by("date", "start_time")[:3]
        weekday_data = list(
            LabScheduleModel.objects.extra({"weekday": "WEEKDAY(date)"})
            .values("weekday")
            .annotate(count=Count("id"))
        )
        # Map weekday number to name (0=Monday, 6=Sunday in Django, but MySQL WEEKDAY: 0=Monday, 6=Sunday)
        weekday_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for item in weekday_data:
            item["day"] = weekday_map[item["weekday"]]
        weekday_data = [
            {
                "day": weekday_map[i],
                "count": next(
                    (x["count"] for x in weekday_data if x["weekday"] == i), 0
                ),
            }
            for i in range(7)
        ]
        source_data = list(
            LabScheduleModel.objects.values("source_model")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        context.update(
            {
                "monthly_data": json.dumps(monthly_data),
                "activity_data": json.dumps(activity_data),
                "upcoming_schedules": list(upcoming_schedules),
                "total_schedules": LabScheduleModel.objects.count(),
                "weekday_data": json.dumps(weekday_data),
                "source_data": json.dumps(source_data),
            }
        )
        return render(request, "admin/lab_schedule/dashboard.html", context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "dashboard/",
                self.admin_site.admin_view(self.dashboard_view),
                name="lab_schedule_dashboard",
            ),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        from django.shortcuts import redirect

        return redirect("../")


admin.site.register(LabScheduleDashboardModel, LabScheduleDashboardAdmin)
