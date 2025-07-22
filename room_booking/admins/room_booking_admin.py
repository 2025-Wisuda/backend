"""
Django admin configuration for Room Booking management.

Provides admin interface for room booking requests from all user types
with conditional field requirements and approval workflows.
"""

from core.enums import BookingType, UserGroup
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.urls import path
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportMixin
from shared.utils import (
    AuditFieldMixin,
    ExportOnlyMixin,
    LabEmployeePermissionMixin,
    StandardExportFormatMixin,
)
from shared.utils.admin_approval_utils import (
    create_approve_action,
    create_reject_action,
)
from shared.utils.permission_config_utils import admin_laboratory_employee_only

from ..models import RoomBookingModel
from .room_booking_resource import RoomBookingResource


class RoomBookingAdminForm(forms.ModelForm):
    class Meta:
        model = RoomBookingModel
        exclude = ["approved_by_user"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            from core.enums import ApprovalStatus

            if self.instance.approval_status != ApprovalStatus.PENDING.value:
                self.fields["approval_status"].disabled = True
                self.fields["approval_status"].help_text = (
                    "Status cannot be changed after approval/rejection"
                )

        # Filter approval status choices to only show reject and approve
        if "approval_status" in self.fields:
            from core.enums import ApprovalStatus

            self.fields["approval_status"].choices = [
                choice
                for choice in self.fields["approval_status"].choices
                if choice[0]
                in [ApprovalStatus.REJECTED.value, ApprovalStatus.APPROVED.value]
            ]

    def clean(self):
        """Bypass approval validation - handle in save_model instead."""
        # Skip ApprovalMixin validation
        return super(forms.ModelForm, self).clean()


@admin.register(RoomBookingModel)
class RoomBookingAdmin(
    StandardExportFormatMixin,
    ExportOnlyMixin,
    AuditFieldMixin,
    ExportMixin,
    admin.ModelAdmin,
):
    resource_class = RoomBookingResource
    form = RoomBookingAdminForm

    list_display = [
        "booker_name",
        "booking_type",
        "date",
        "time_display",
        "approval_status",
    ]

    list_filter = [
        "booking_type",
        "approval_status",
        "seminar_type",
    ]

    search_fields = [
        "booker__first_name",
        "booker__last_name",
        "booker__username",
        "booker__student_number",
        "booker__employee_number",
        "purpose",
        "research_title",
        "supervisor_main",
    ]

    readonly_fields = (
        "booker",
        "booking_type",
        "purpose",
        "date",
        "start_time",
        "end_time",
        "seminar_type",
        "research_title",
        "supervisor_main",
        "supervisor_secondary",
        "examiner",
        "approval_timestamp",
        "document_proof",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    )

    ordering = ["-date", "-start_time"]
    date_hierarchy = "date"

    fieldsets = (
        (
            _("Booking Information"),
            {
                "fields": (
                    "booker",
                    "booking_type",
                    "purpose",
                    "date",
                    "start_time",
                    "end_time",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Academic Details"),
            {
                "fields": (
                    "seminar_type",
                    "research_title",
                    "supervisor_main",
                    "supervisor_secondary",
                    "examiner",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Approval Information"),
            {
                "fields": (
                    "approval_status",
                    "approval_timestamp",
                    "approval_notes",
                ),
            },
        ),
        (
            _("Additional Information"),
            {
                "fields": ("document_proof",),
                "classes": ("collapse",),
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

    def booker_name(self, obj):
        """Display booker name with user identifier."""
        name = obj.booker.get_full_name() or obj.booker.username
        identifier = obj.get_user_identifier()
        return f"{name} ({identifier})"

    booker_name.short_description = _("Booker")

    def time_display(self, obj):
        """Display formatted time range."""
        if obj.start_time and obj.end_time:
            return (
                f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
            )
        return "-"

    time_display.short_description = _("Time")

    def get_fieldsets(self, request, obj=None):
        """Dynamic fieldsets berdasarkan status approval."""
        from core.enums import ApprovalStatus

        base_fieldsets = [
            (
                _("Booking Information"),
                {
                    "fields": (
                        "booker",
                        "booking_type",
                        "purpose",
                        "date",
                        "start_time",
                        "end_time",
                    ),
                    "classes": ("collapse",),
                },
            ),
            (
                _("Academic Details"),
                {
                    "fields": (
                        "seminar_type",
                        "research_title",
                        "supervisor_main",
                        "supervisor_secondary",
                        "examiner",
                    ),
                    "classes": ("collapse",),
                },
            ),
            (
                _("Approval Status"),
                {
                    "fields": ("approval_status", "approval_notes"),
                },
            ),
        ]

        if obj and obj.approval_status in [
            ApprovalStatus.APPROVED.value,
            ApprovalStatus.REJECTED.value,
        ]:
            base_fieldsets.insert(
                3,
                (
                    _("Approval Information"),
                    {
                        "fields": ("approval_timestamp",),
                    },
                ),
            )

        base_fieldsets.extend(
            [
                (
                    _("Additional Information"),
                    {
                        "fields": ("document_proof",),
                        "classes": ("collapse",),
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
            ]
        )

        return base_fieldsets

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related("booker", "approved_by_user", "created_by", "updated_by")
        )

    def save_model(self, request, obj, form, change):
        """Auto-set approval fields when technician changes status."""
        from core.enums import ApprovalStatus
        from django.contrib import messages
        from django.utils import timezone

        # Auto-set approved_by_user if status requires it but field is empty
        if (
            obj.approval_status
            in [ApprovalStatus.APPROVED.value, ApprovalStatus.REJECTED.value]
            and not obj.approved_by_user
        ):
            obj.approved_by_user = request.user

        if "approval_status" in form.changed_data:
            if obj.approval_status in [
                ApprovalStatus.APPROVED.value,
                ApprovalStatus.REJECTED.value,
            ]:
                obj.approved_by_user = request.user
                obj.approval_timestamp = timezone.localtime()
                if not obj.approval_notes:
                    status_text = (
                        _("approved")
                        if obj.approval_status == ApprovalStatus.APPROVED.value
                        else _("rejected")
                    )
                    obj.approval_notes = _("Booking {status} by technician").format(
                        status=status_text
                    )

        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        """Override form to bypass model validation for approval status changes."""
        form = super().get_form(request, obj, **kwargs)

        # Override the approve method to bypass conflict validation
        if obj and hasattr(obj, "approve"):
            original_approve = obj.approve

            def bypass_approve(approved_by, notes=None):
                """Bypass conflict validation for admin approval."""
                from core.enums import ApprovalStatus
                from django.utils import timezone

                obj.approval_status = ApprovalStatus.APPROVED.value
                obj.approved_by_user = approved_by
                obj.approval_timestamp = timezone.localtime()
                if notes:
                    obj.approval_notes = notes
                obj.save()

            obj.approve = bypass_approve

        return form

    @admin_laboratory_employee_only
    def approve_bookings(self, request, queryset):
        """Approve selected bookings - restricted to lab employees."""
        from core.enums import ApprovalStatus
        from django.utils import timezone

        approved_count = 0

        for booking in queryset:
            if booking.approval_status == ApprovalStatus.PENDING.value:
                booking.approval_status = ApprovalStatus.APPROVED.value
                booking.approved_by_user = request.user
                booking.approval_timestamp = timezone.localtime()
                if not booking.approval_notes:
                    booking.approval_notes = _("Booking approved by technician")
                booking.updated_by = request.user
                booking.save()
                approved_count += 1

        self.message_user(
            request,
            _(f"{approved_count} bookings approved successfully."),
        )

    approve_bookings.short_description = _("Approve Selected Bookings")

    @admin_laboratory_employee_only
    def reject_bookings(self, request, queryset):
        """Reject selected bookings - restricted to lab employees."""
        from core.enums import ApprovalStatus
        from django.utils import timezone

        rejected_count = 0

        for booking in queryset:
            if booking.approval_status == ApprovalStatus.PENDING.value:
                booking.approval_status = ApprovalStatus.REJECTED.value
                booking.approved_by_user = request.user
                booking.approval_timestamp = timezone.localtime()
                if not booking.approval_notes:
                    booking.approval_notes = _("Booking rejected by technician")
                booking.updated_by = request.user
                booking.save()
                rejected_count += 1

        self.message_user(
            request,
            _(f"{rejected_count} bookings rejected successfully."),
        )

    reject_bookings.short_description = _("Reject Selected Bookings")

    def get_actions(self, request):
        """Control actions - remove hard delete, add approval actions."""
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    actions = [
        "approve_bookings",
        "reject_bookings",
    ]

    def has_delete_permission(self, request, obj=None):
        """No hard delete - only soft delete via actions."""
        return False

    def has_module_permission(self, request):
        """Control module access based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_HEAD.value:
            return True
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            return True
        return False

    def has_view_permission(self, request, obj=None):
        """Control view permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_HEAD.value:
            return True
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """Control change permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_HEAD.value:
            return True
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            return True
        return False

    def has_export_permission(self, request):
        """Control export permission based on user role."""
        if request.user.is_superuser:
            return True
        elif request.user.group == UserGroup.LABORATORY_HEAD.value:
            return True
        elif request.user.group == UserGroup.LABORATORY_TECHNICIAN.value:
            return True
        return False

    def has_add_permission(self, request):
        """No add permission - edit only admin."""
        return False

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Override change_view to bypass form validation for approval."""
        from django.contrib import messages
        from django.http import Http404, HttpResponseRedirect
        from django.urls import reverse

        # Get the object
        obj = self.get_object(request, object_id)
        if obj is None:
            raise Http404(
                _("%(name)s object with primary key %(key)r does not exist.")
                % {
                    "name": self.model._meta.verbose_name,
                    "key": object_id,
                }
            )

        # Handle POST request
        if request.method == "POST":
            # Get approval_status from POST data
            approval_status = request.POST.get("approval_status")
            approval_notes = request.POST.get("approval_notes", "")

            if approval_status:
                # Update approval fields directly like actions do
                from core.enums import ApprovalStatus
                from django.utils import timezone

                obj.approval_status = approval_status
                obj.approval_notes = approval_notes

                if obj.approval_status in [
                    ApprovalStatus.APPROVED.value,
                    ApprovalStatus.REJECTED.value,
                ]:
                    obj.approved_by_user = request.user
                    obj.approval_timestamp = timezone.localtime()
                    if not obj.approval_notes:
                        status_text = (
                            _("approved")
                            if obj.approval_status == ApprovalStatus.APPROVED.value
                            else _("rejected")
                        )
                        obj.approval_notes = _("Booking {status} by technician").format(
                            status=status_text
                        )

                obj.updated_by = request.user
                obj.save()

                messages.success(
                    request,
                    _("Room booking {status} successfully.").format(
                        status=obj.approval_status
                    ),
                )
                return HttpResponseRedirect(
                    reverse("admin:room_booking_roombookingmodel_changelist")
                )

        # Use normal change_view for GET requests
        return super().change_view(request, object_id, form_url, extra_context)
