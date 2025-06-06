"""
Django admin configuration for Room Booking management.

Provides admin interface for room booking requests from all user types
with conditional field requirements and approval workflows.
"""

from django import forms
from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportMixin

from core.enums import BookingType, UserGroup
from shared.format.custom_xlsx_format import AutoFitXLSX
from shared.utils import create_activate_action, create_deactivate_action
from shared.utils.admin_approval_utils import (
    create_approve_action,
    create_reject_action,
)
from shared.utils.permission_config_utils import admin_laboratory_employee_only

from ..models import RoomBookingModel
from .room_booking_resource import RoomBookingResource


class RoomBookingAdminForm(forms.ModelForm):
    """
    Custom room booking admin form with conditional field requirements.
    """

    class Meta:
        model = RoomBookingModel
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = getattr(self, "_request", None)
        if request and hasattr(request, "user"):
            user = request.user

            if hasattr(user, "group"):
                if UserGroup.is_student_group(user.group):
                    self.fields["booking_type"].choices = [
                        (BookingType.SEMINAR.value, BookingType.SEMINAR.label())
                    ]
                    self.fields["booking_type"].initial = BookingType.SEMINAR.value

    def clean(self):
        """
        Validate form based on booking type and user permissions.
        """
        cleaned_data = super().clean()
        booking_type = cleaned_data.get("booking_type")
        booker = cleaned_data.get("booker")

        # Validate booking type permissions for user
        if booker and hasattr(booker, "group"):
            user_group = booker.group
            if UserGroup.is_student_group(user_group):
                if booking_type not in BookingType.student_allowed_types():
                    raise forms.ValidationError(
                        {
                            "booking_type": _(
                                "Students and assistants can only create seminar bookings."
                            )
                        }
                    )

        # Validate required fields for seminar bookings
        if booking_type == BookingType.SEMINAR.value:
            required_fields = [
                "research_title",
                "seminar_type",
                "supervisor_main",
                "examiner",
            ]
            errors = {}

            for field in required_fields:
                if not cleaned_data.get(field):
                    field_label = self.fields[field].label
                    errors[field] = _(
                        f"{field_label} is required for seminar bookings."
                    )

            if errors:
                raise forms.ValidationError(errors)

        return cleaned_data


@admin.register(RoomBookingModel)
class RoomBookingAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = RoomBookingResource
    form = RoomBookingAdminForm

    list_display = [
        "booker_name",
        "booking_type",
        "booking_date",
        "time_display",
        "booking_approval_status",
    ]

    list_filter = [
        "booking_type",
        "booking_approval_status",
        "booking_date",
        "seminar_type",
        ("booker__group", admin.ChoicesFieldListFilter),
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
        "approval_timestamp",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    )

    ordering = ["-booking_date", "-booking_start_time"]
    date_hierarchy = "booking_date"

    add_fieldsets = (
        (
            _("Booking Information"),
            {
                "fields": (
                    "booker",
                    "booking_type",
                    "purpose",
                    "booking_date",
                    "booking_start_time",
                    "booking_end_time",
                ),
                "description": _(
                    "Basic booking information required for all booking types."
                ),
            },
        ),
        (
            _("Academic Details (Required for Seminars)"),
            {
                "classes": ("wide", "collapse"),
                "fields": (
                    "seminar_type",
                    "research_title",
                    "supervisor_main",
                    "supervisor_secondary",
                    "examiner",
                ),
                "description": _(
                    "Academic information required for seminar bookings by students/assistants."
                ),
            },
        ),
        (
            _("Additional Information"),
            {
                "classes": ("wide", "collapse"),
                "fields": ("document_proof",),
                "description": _("Optional supporting documents for the booking."),
            },
        ),
    )

    fieldsets = (
        (
            _("Booking Information"),
            {
                "fields": (
                    "booker",
                    "booking_type",
                    "purpose",
                    "booking_date",
                    "booking_start_time",
                    "booking_end_time",
                )
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
                    "booking_approval_status",
                    "approved_by_user",
                    "approval_timestamp",
                    "approval_notes",
                ),
                "classes": ("collapse",),
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
        if obj.booking_start_time and obj.booking_end_time:
            return f"{obj.booking_start_time.strftime('%H:%M')} - {obj.booking_end_time.strftime('%H:%M')}"
        return "-"

    time_display.short_description = _("Time")

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related("booker", "approved_by_user", "created_by", "updated_by")
        )

    def get_fieldsets(self, request, obj=None):
        """Use different fieldsets for add vs change."""
        if obj is None:  # Adding new object
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize ForeignKey fields."""
        if db_field.name == "booker":
            # Optimize booker field queryset
            kwargs[
                "queryset"
            ] = db_field.related_model.objects.select_related().order_by(
                "first_name", "last_name"
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        """Customize form to pass request context."""
        form = super().get_form(request, obj, **kwargs)
        form._request = request  # Pass request to form for user context
        return form

    def save_model(self, request, obj, form, change):
        """Set audit fields, and auto-approve if user is a lab technician."""
        from core.enums import UserGroup

        is_technician = (
            hasattr(request.user, "group")
            and request.user.group == UserGroup.LABORATORY_TECHNICIAN
        )

        if not change:
            obj.created_by = request.user

            # Auto approve if technician is the one who created the booking
            if is_technician:
                obj.booking_approval_status = "Disetujui"
                obj.approved_by_user = request.user

        else:
            # Jika approval status diubah dan user technician, update approved_by_user
            if is_technician and "booking_approval_status" in form.changed_data:
                obj.approved_by_user = request.user

        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    @admin_laboratory_employee_only
    def approve_bookings(self, request, queryset):
        """Approve selected bookings - restricted to lab employees."""
        approved_count = 0
        for booking in queryset:
            if hasattr(booking, "approve"):
                booking.approve(request.user)
                approved_count += 1

        self.message_user(
            request,
            _(f"{approved_count} bookings approved successfully."),
        )

    approve_bookings.short_description = _("Approve Selected Bookings")

    @admin_laboratory_employee_only
    def reject_bookings(self, request, queryset):
        """Reject selected bookings - restricted to lab employees."""
        rejected_count = 0
        for booking in queryset:
            if hasattr(booking, "reject"):
                booking.reject(request.user)
                rejected_count += 1

        self.message_user(
            request,
            _(f"{rejected_count} bookings rejected successfully."),
        )

    reject_bookings.short_description = _("Reject Selected Bookings")

    @admin_laboratory_employee_only
    def activate_bookings(self, request, queryset):
        """Restore selected bookings - restricted to lab employees."""
        activate_action = create_activate_action(
            model_name="booking",
            superuser_only=False,
            verbose_name=_("Restore Selected Bookings"),
        )
        return activate_action(self, request, queryset)

    activate_bookings.short_description = _("Restore Selected Bookings")

    @admin_laboratory_employee_only
    def deactivate_bookings(self, request, queryset):
        """Delete selected bookings - restricted to lab employees."""
        deactivate_action = create_deactivate_action(
            model_name="booking",
            superuser_only=False,
            verbose_name=_("Delete Selected Bookings"),
        )
        return deactivate_action(self, request, queryset)

    deactivate_bookings.short_description = _("Delete Selected Bookings")

    def get_actions(self, request):
        """Control actions - remove hard delete, add approval actions."""
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    actions = [
        "approve_bookings",
        "reject_bookings",
        "activate_bookings",
        "deactivate_bookings",
    ]

    def get_export_formats(self):
        """Export formats available."""
        formats = super().get_export_formats()
        export_formats = [AutoFitXLSX]
        for format_cls in formats:
            if format_cls.__name__ != "XLSX":
                export_formats.append(format_cls)
        return export_formats

    def export_action(self, request, *args, **kwargs):
        """Export action - restricted to lab employees."""
        # Check permissions manually
        if not self._has_lab_employee_permission(request):
            from django.contrib import messages
            from django.shortcuts import redirect

            messages.error(request, _("Only laboratory employees can export data"))
            return redirect(request.META.get("HTTP_REFERER", "admin:index"))
        return super().export_action(request, *args, **kwargs)

    def _has_lab_employee_permission(self, request):
        """Check if user has lab employee permissions."""
        from core.enums.user_group_enum import UserGroup
        from shared.utils.permission_config_utils import has_group_permission

        allowed_groups = [
            UserGroup.LABORATORY_TECHNICIAN,
        ]
        return has_group_permission(request.user, allowed_groups)

    def get_import_formats(self):
        """Disable import - this is export-only."""
        return []

    def has_import_permission(self, request):
        """Disable import - this is export-only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """No hard delete - only soft delete via actions."""
        return False
