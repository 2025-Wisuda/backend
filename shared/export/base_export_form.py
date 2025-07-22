"""
Base export form for reusable field selection and filtering functionality.

Provides a generic form foundation that can be extended for any model
with customizable field selection and filtering options.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from core.enums import Month


class BaseExportForm(forms.Form):
    """
    Base export form with common filtering and field selection.

    This class provides a foundation for export forms with:
    - Date filtering (range, month, year)
    - Format selection
    - Field selection with checkboxes
    - Form validation

    To use this class, inherit from it and:
    1. Set FIELD_CHOICES with your model's fields
    2. Set DEFAULT_FIELDS with default field selection
    3. Override _get_custom_filters() to add model-specific filters
    4. Override clean() to add custom validation if needed
    """

    # To be overridden by subclasses
    FIELD_CHOICES = []
    DEFAULT_FIELDS = []
    SHOW_DATE_FILTERING = True  # Can be set to False in subclasses

    # Export format choices
    FORMAT_CHOICES = [
        ("xlsx", _("Excel (.xlsx)")),
        ("csv", _("CSV")),
        ("json", _("JSON")),
    ]

    # Common date filtering fields
    created_at_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label=_("Created From"),
        help_text=_("Filter records created from this date"),
    )

    created_at_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label=_("Created To"),
        help_text=_("Filter records created until this date"),
    )

    # Month filtering - using Month enum for consistency
    created_at_month = forms.ChoiceField(
        choices=Month.choices(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        label=_("Month"),
        help_text=_("Filter by specific month"),
    )

    # Year filtering (will be populated dynamically)
    created_at_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "2020",
                "max": "2030",
                "placeholder": _("Year"),
            }
        ),
        label=_("Year"),
        help_text=_("Filter by specific year"),
    )

    # Export format selection
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        initial="xlsx",
        widget=forms.RadioSelect(attrs={"class": "format-selection-radio"}),
        label=_("Export Format"),
        help_text=_("Choose the export file format"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_field_selection()
        self._setup_date_filtering()
        self._setup_custom_fields()
        
    def _setup_date_filtering(self):
        """Setup or remove date filtering fields based on SHOW_DATE_FILTERING."""
        if not self.SHOW_DATE_FILTERING:
            # Remove date filtering fields if not needed
            fields_to_remove = ['created_at_from', 'created_at_to', 'created_at_month', 'created_at_year']
            for field_name in fields_to_remove:
                if field_name in self.fields:
                    del self.fields[field_name]

    def _setup_field_selection(self):
        """Setup field selection based on FIELD_CHOICES and DEFAULT_FIELDS."""
        if self.FIELD_CHOICES:
            self.fields["selected_fields"] = forms.MultipleChoiceField(
                choices=self.FIELD_CHOICES,
                initial=self.DEFAULT_FIELDS,
                widget=forms.CheckboxSelectMultiple(
                    attrs={"class": "field-selection-checkboxes"}
                ),
                label=_("Fields to Export"),
                help_text=_("Select which fields to include in the export"),
                required=True,
            )

    def _setup_custom_fields(self):
        """
        Setup model-specific fields.

        Override this method in subclasses to add custom form fields.
        """
        pass

    def clean(self):
        """Validate form data with common validation rules."""
        cleaned_data = super().clean()

        # Validate date range
        from_date = cleaned_data.get("created_at_from")
        to_date = cleaned_data.get("created_at_to")

        if from_date and to_date and from_date > to_date:
            raise forms.ValidationError(
                {"created_at_to": _("End date must be after start date")}
            )

        # Validate field selection
        selected_fields = cleaned_data.get("selected_fields")
        if "selected_fields" in self.fields and not selected_fields:
            raise forms.ValidationError(
                {"selected_fields": _("Please select at least one field to export")}
            )

        # Custom validation
        return self._clean_custom(cleaned_data)

    def _clean_custom(self, cleaned_data):
        """
        Custom validation logic.

        Override this method in subclasses to add model-specific validation.
        """
        return cleaned_data

    def get_filter_summary(self):
        """
        Get a human-readable summary of applied filters.

        Useful for displaying filter information in templates or logs.
        """
        if not self.is_valid():
            return ""

        filters = []
        data = self.cleaned_data

        # Date range
        if data.get("created_at_from") and data.get("created_at_to"):
            filters.append(
                f"Date: {data['created_at_from']} to {data['created_at_to']}"
            )
        elif data.get("created_at_from"):
            filters.append(f"From: {data['created_at_from']}")
        elif data.get("created_at_to"):
            filters.append(f"Until: {data['created_at_to']}")

        # Month/Year
        if data.get("created_at_month"):
            month_name = dict(self.MONTH_CHOICES)[data["created_at_month"]]
            filters.append(f"Month: {month_name}")

        if data.get("created_at_year"):
            filters.append(f"Year: {data['created_at_year']}")

        # Custom filters
        filters.extend(self._get_custom_filter_summary(data))

        return "; ".join(filters) if filters else "No filters applied"

    def _get_custom_filter_summary(self, data):
        """
        Get custom filter summary.

        Override this method in subclasses to add model-specific filter summaries.
        """
        return []


class ModelSpecificExportFormMixin:
    """
    Mixin to help create model-specific export forms.

    Provides helper methods for common field types and patterns.
    """

    @classmethod
    def create_field_choices_from_model(
        cls, model, exclude_fields=None, include_relations=False
    ):
        """
        Create field choices from a Django model.

        Args:
            model: Django model class
            exclude_fields: List of field names to exclude
            include_relations: Whether to include foreign key relations

        Returns:
            List of (field_name, field_verbose_name) tuples
        """
        exclude_fields = exclude_fields or []
        choices = []

        for field in model._meta.get_fields():
            # Skip excluded fields
            if field.name in exclude_fields:
                continue

            # Skip reverse relations unless explicitly included
            if hasattr(field, "related_model") and not include_relations:
                continue

            # Skip many-to-many fields (complex to export)
            if hasattr(field, "many_to_many") and field.many_to_many:
                continue

            verbose_name = getattr(
                field, "verbose_name", field.name.replace("_", " ").title()
            )
            choices.append((field.name, _(verbose_name)))

        return choices

    def add_choice_filter(self, field_name, choices, label=None, required=False):
        """Add a choice field filter to the form."""
        if not label:
            label = field_name.replace("_", " ").title()

        self.fields[field_name] = forms.ChoiceField(
            choices=[("", f"All {label}")] + list(choices),
            required=required,
            widget=forms.Select(attrs={"class": "form-control"}),
            label=_(label),
            help_text=_(f"Filter by {label.lower()}"),
        )

    def add_boolean_filter(self, field_name, label=None):
        """Add a boolean field filter to the form."""
        if not label:
            label = field_name.replace("_", " ").title()

        self.fields[field_name] = forms.ChoiceField(
            choices=[
                ("", f"All {label}"),
                ("true", "Yes"),
                ("false", "No"),
            ],
            required=False,
            widget=forms.Select(attrs={"class": "form-control"}),
            label=_(label),
            help_text=_(f"Filter by {label.lower()}"),
        )

    def add_text_filter(self, field_name, label=None):
        """Add a text field filter to the form."""
        if not label:
            label = field_name.replace("_", " ").title()

        self.fields[field_name] = forms.CharField(
            required=False,
            widget=forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": f"Search {label.lower()}...",
                }
            ),
            label=_(label),
            help_text=_(f"Filter by {label.lower()}"),
        )
