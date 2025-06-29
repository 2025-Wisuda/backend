"""
Guest Visit Export Form for Django admin.

Provides filtering options for exporting guest visit data with:
- Date filtering (date range, month, year)
- Visitor type filtering
- Host filtering
- Field selection with checkboxes
"""

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from core.enums import Month, VisitorIdentityType
from shared.export import BaseExportForm, ModelSpecificExportFormMixin

from ...models import GuestVisitModel
from ..guest_visit_resource import GuestVisitResource

User = get_user_model()


class GuestVisitExportForm(BaseExportForm, ModelSpecificExportFormMixin):
    """
    Guest Visit-specific export form with filtering and field selection.

    Features:
    - Visit date filtering (range, month, year) 
    - Visitor identity type filtering
    - Host user filtering
    - Field selection with checkboxes
    """

    # Disable generic date filtering - use visit_date filtering instead
    SHOW_DATE_FILTERING = False

    # Field selection - from GuestVisitResource
    FIELD_CHOICES = [
        (field, _(field.replace("_", " ").title()))
        for field in GuestVisitResource.EXPORT_FIELDS
    ]

    # Default selected fields for user convenience
    DEFAULT_FIELDS = [
        "visit_date",
        "start_time",
        "end_time",
        "visitor_name", 
        "visitor_identity_type",
        "purpose",
        "host_user",
    ]

    def _setup_custom_fields(self):
        """Setup guest visit specific fields."""
        # Add visit date range filtering
        self.fields["visit_date_from"] = forms.DateField(
            required=False,
            widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            label=_("Visit Date From"),
            help_text=_("Filter visits from this date"),
        )

        self.fields["visit_date_to"] = forms.DateField(
            required=False,
            widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            label=_("Visit Date To"),
            help_text=_("Filter visits until this date"),
        )

        # Add visit month/year filtering using Month enum
        self.add_choice_filter(
            "visit_month", Month.choices(include_all=True), _("Visit Month")
        )

        self.fields["visit_year"] = forms.IntegerField(
            required=False,
            widget=forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "2020",
                    "max": "2030",
                    "placeholder": _("Year"),
                }
            ),
            label=_("Visit Year"),
            help_text=_("Filter by specific year"),
        )

        # Add visitor identity type filtering
        identity_type_choices = [("", _("All Identity Types"))]
        identity_type_choices.extend(VisitorIdentityType.choices())
        self.add_choice_filter(
            "visitor_identity_type", 
            identity_type_choices, 
            _("Visitor Identity Type")
        )

        # Add host user filtering (only active users who have hosted visits)
        host_users = User.objects.filter(
            hosted_guest_visits__isnull=False,
            is_active=True
        ).distinct().order_by("first_name", "last_name")

        host_choices = [("", _("All Hosts"))]
        host_choices.extend([
            (str(user.id), f"{user.first_name} {user.last_name}")
            for user in host_users
        ])
        
        self.add_choice_filter("host_user", host_choices, _("Host User"))

    def _clean_custom(self, cleaned_data):
        """Custom validation for guest visit export form."""
        # Validate visit date range
        visit_from = cleaned_data.get("visit_date_from")
        visit_to = cleaned_data.get("visit_date_to")

        if visit_from and visit_to and visit_from > visit_to:
            raise forms.ValidationError(
                {"visit_date_to": _("Visit end date must be after start date")}
            )

        return cleaned_data

    def _get_custom_filter_summary(self, data):
        """
        Get summary of applied custom filters for display.
        """
        summary = []

        # Visit date range filters
        visit_from = data.get("visit_date_from")
        visit_to = data.get("visit_date_to")
        if visit_from and visit_to:
            summary.append(f"Visit Date: {visit_from} to {visit_to}")
        elif visit_from:
            summary.append(f"Visit Date: from {visit_from}")
        elif visit_to:
            summary.append(f"Visit Date: until {visit_to}")

        # Visit month filter
        visit_month = data.get("visit_month")
        if visit_month:
            month_name = Month.get_month_name(int(visit_month))
            if month_name:
                summary.append(f"Visit Month: {month_name}")

        # Visit year filter
        visit_year = data.get("visit_year")
        if visit_year:
            summary.append(f"Visit Year: {visit_year}")

        # Visitor identity type filter
        identity_type = data.get("visitor_identity_type")
        if identity_type:
            summary.append(f"Identity Type: {identity_type}")

        # Host user filter
        host_user_id = data.get("host_user")
        if host_user_id:
            try:
                host_user = User.objects.get(id=host_user_id)
                summary.append(f"Host: {host_user.first_name} {host_user.last_name}")
            except User.DoesNotExist:
                pass

        return summary 