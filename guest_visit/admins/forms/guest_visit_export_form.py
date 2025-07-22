"""
Guest Visit Export Form for Django admin.

Provides filtering options for exporting guest visit data with:
- Date filtering (date range, month, year)
- Visitor type filtering
- Host filtering
- Field selection with checkboxes
"""

from core.enums import Month, VisitorIdentityType
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
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
        "date",
        "start_time",
        "end_time",
        "visitor_name",
        "identity_type",
        "purpose",
        "created_at",
        "created_by",
    ]

    def get_template_name(self):
        """Return custom template for better UI."""
        return "admin/guest_visit/guestvisitmodel/export_form.html"

    def _setup_custom_fields(self):
        """Setup guest visit specific fields with proper Django admin styling."""
        # Date range filters
        self.fields["visit_date_from"] = forms.DateField(
            required=False,
            widget=forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "vDateField",
                    "style": "width: 200px; height: 35px;",
                }
            ),
            label=_("From Date"),
            help_text=_("Filter visits from this date"),
        )

        self.fields["visit_date_to"] = forms.DateField(
            required=False,
            widget=forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "vDateField",
                    "style": "width: 200px; height: 35px;",
                }
            ),
            label=_("To Date"),
            help_text=_("Filter visits until this date"),
        )

        # Month filter
        month_choices = [("", _("All Months"))]
        month_choices.extend(Month.choices(include_all=False))
        self.fields["visit_month"] = forms.ChoiceField(
            choices=month_choices,
            required=False,
            widget=forms.Select(
                attrs={"class": "vTextField", "style": "width: 200px; height: 35px;"}
            ),
            label=_("Month"),
            help_text=_("Filter by specific month"),
        )

        # Year filter
        self.fields["visit_year"] = forms.IntegerField(
            required=False,
            widget=forms.NumberInput(
                attrs={
                    "class": "vIntegerField",
                    "style": "width: 200px; height: 35px;",
                    "min": "2020",
                    "max": "2030",
                    "placeholder": _("Year"),
                }
            ),
            label=_("Year"),
            help_text=_("Filter by specific year"),
        )

        # Identity type filter
        identity_type_choices = [("", _("All Identity Types"))]
        identity_type_choices.extend(VisitorIdentityType.choices())
        self.fields["visitor_identity_type"] = forms.ChoiceField(
            choices=identity_type_choices,
            required=False,
            widget=forms.Select(
                attrs={"class": "vTextField", "style": "width: 200px; height: 35px;"}
            ),
            label=_("Identity Type"),
            help_text=_("Filter by visitor identity type"),
        )

        # Created By filter - this shows who created the record, not the visitor
        created_by_users = (
            User.objects.filter(guest_visits_as_visitor__isnull=False, is_active=True)
            .distinct()
            .order_by("first_name", "last_name")
        )

        created_by_choices = [("", _("All Users"))]
        created_by_choices.extend(
            [
                (str(user.id), f"{user.first_name} {user.last_name}")
                for user in created_by_users
            ]
        )

        self.fields["host_user"] = forms.ChoiceField(
            choices=created_by_choices,
            required=False,
            widget=forms.Select(
                attrs={"class": "vTextField", "style": "width: 200px; height: 35px;"}
            ),
            label=_("Created By"),
            help_text=_("Filter by user who created the visit record"),
        )

        # Format selection
        self.fields["format"] = forms.ChoiceField(
            choices=self.FORMAT_CHOICES,
            initial="xlsx",
            widget=forms.RadioSelect(attrs={"class": "format-selection-radio"}),
            label=_("Export Format"),
            help_text=_("Choose the export file format"),
        )

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
