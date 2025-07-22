"""
Base export view for reusable model export functionality.

Provides a generic export system that can be extended for any Django model
with django-import-export support.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Type

from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from import_export.formats import base_formats
from import_export.resources import ModelResource

from shared.format.custom_xlsx_format import AutoFitXLSX


class BaseExportView:
    """
    Base export view with filtering and field selection capabilities.

    This class provides a reusable foundation for model exports with:
    - Date filtering (range, month, year)
    - Custom field filtering
    - Field selection with checkboxes
    - Multiple export formats
    - Permission checking
    - Audit logging

    To use this class, inherit from it and set the required attributes:
    - model: The Django model to export
    - resource_class: The django-import-export resource class
    - form_class: The form class for filtering/field selection
    - template_name: The template for the export form
    """

    # Required attributes to be set by subclasses
    model: Type = None
    resource_class: Type[ModelResource] = None
    form_class: Type = None
    template_name: str = None

    # Optional attributes that can be overridden
    permission_required: str = None
    permission_check_method: str = None
    export_filename_prefix: str = "export"

    def __init__(self, admin_instance=None):
        """Initialize with optional admin instance for permission checking."""
        self.admin = admin_instance
        self._validate_configuration()

    def _validate_configuration(self):
        """Validate that required attributes are set."""
        required_attrs = ["model", "resource_class", "form_class", "template_name"]
        for attr in required_attrs:
            if getattr(self, attr) is None:
                raise ImproperlyConfigured(
                    f"{self.__class__.__name__} is missing required attribute: {attr}"
                )

    def export_action(self, request, queryset=None):
        """
        Main export action handler.

        Handles both GET (show form) and POST (process export) requests.
        """

        # Check permissions
        if not self._check_permissions(request):
            messages.error(request, _("You don't have permission to export this data"))
            return redirect(request.META.get("HTTP_REFERER", "admin:index"))

        if request.method == "POST":
            form = self.form_class(request.POST)
            if form.is_valid():
                try:
                    response = self._process_export(request, form)

                    # For AJAX requests, we need to handle this differently
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        # Store the file data temporarily and return success
                        # The frontend will handle the actual download
                        return response
                    else:
                        return response

                except Exception as e:
                    # Handle export errors gracefully
                    import logging

                    logger = logging.getLogger(__name__)
                    error_message = (
                        str(e) if str(e) else _("An error occurred during export")
                    )

                    # Log error for debugging
                    logger.error(
                        f"Export error for user {request.user.username}: {error_message}"
                    )

                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse(
                            {"success": False, "error": error_message}, status=400
                        )
                    else:
                        # For non-AJAX requests, render form with error
                        form = self.form_class(request.POST)
                        form.add_error(None, error_message)
            else:
                # Form validation errors - handled by JavaScript, no need for Django messages
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse(
                        {
                            "success": False,
                            "error": _("Please correct the form errors and try again"),
                            "form_errors": form.errors,
                        },
                        status=400,
                    )
        else:
            form = self.form_class()

        # Render the export form
        context = self._get_template_context(request, form)
        return render(request, self.template_name, context)

    def _check_permissions(self, request) -> bool:
        """
        Check if user has permission to export.

        Override this method or set permission_check_method to customize
        permission checking logic.
        """
        if self.permission_check_method and self.admin:
            # Use custom permission check method from admin
            method = getattr(self.admin, self.permission_check_method, None)
            if method:
                return method(request)

        if self.permission_required:
            return request.user.has_perm(self.permission_required)

        # Default: check if user has view permission for the model
        if self.admin:
            return self.admin.has_view_permission(request)

        return True

    def _get_template_context(self, request, form) -> Dict[str, Any]:
        """Get template context for rendering the export form."""
        return {
            "form": form,
            "title": _(f"Export {self.model._meta.verbose_name_plural} with Filters"),
            "opts": self.model._meta,
            "app_label": self.model._meta.app_label,
            "has_view_permission": (
                self.admin.has_view_permission(request) if self.admin else True
            ),
            "has_add_permission": False,
            "has_change_permission": False,
            "has_delete_permission": False,
            "cancel_url": self._get_cancel_url(),
            "site_title": "Django administration",
            "site_header": "Django administration",
            "site_url": "/",
            "index_title": "Site administration",
            "available_apps": [],
        }

    def _get_cancel_url(self) -> str:
        """Get URL to redirect to when canceling export."""
        if self.model:
            app_label = self.model._meta.app_label
            model_name = self.model._meta.model_name
            try:
                return reverse(f"admin:{app_label}_{model_name}_changelist")
            except:
                pass
        return reverse("admin:index")

    def _process_export(self, request, form):
        """Process the actual export with filters applied."""

        # Get base queryset
        queryset = self._get_base_queryset(request)

        # Apply filters based on form data
        queryset = self._apply_filters(queryset, form.cleaned_data)

        # Get export format
        file_format = form.cleaned_data.get("format", "xlsx")

        # Get selected fields for export
        selected_fields = form.cleaned_data.get("selected_fields", [])

        # Create resource instance with selected fields
        resource = self._create_filtered_resource(selected_fields)

        # Allow subclasses to customize the resource further
        resource = self._customize_resource_for_export(resource, form.cleaned_data)

        # Export data
        dataset = resource.export(queryset)

        # Get format instance
        format_instance = self._get_format_instance(file_format)

        # Generate response
        export_data = format_instance.export_data(dataset)
        content_type = format_instance.get_content_type()

        # Create filename with timestamp and filters
        filename = self._generate_filename(form.cleaned_data, file_format)

        response = HttpResponse(export_data, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        # Log export action
        self._log_export_action(request, queryset.count(), form.cleaned_data)

        return response

    def _get_base_queryset(self, request):
        """Get the base queryset for export."""
        if self.admin:
            return self.admin.get_queryset(request)
        return self.model.objects.all()

    def _create_filtered_resource(self, selected_fields):
        """Create a resource instance with only selected fields."""
        from import_export import resources

        # Create a dynamic resource class with only selected fields
        class DynamicResource(self.resource_class):
            class Meta:
                model = self.resource_class._meta.model
                fields = selected_fields
                export_order = selected_fields

        return DynamicResource()

    def _customize_resource_for_export(self, resource, form_data):
        """
        Hook for subclasses to customize the resource for export.

        Args:
            resource: The resource instance created by _create_filtered_resource
            form_data: The cleaned form data from the export form

        Returns:
            The customized resource instance
        """
        # Default implementation does nothing - subclasses can override
        return resource

    def _apply_filters(self, queryset, filters):
        """
        Apply filters to the queryset.

        Override this method to implement custom filtering logic.
        Default implementation handles common date filtering patterns.
        """

        # Date range filtering for created_at
        if filters.get("created_at_from"):
            queryset = queryset.filter(created_at__date__gte=filters["created_at_from"])

        if filters.get("created_at_to"):
            queryset = queryset.filter(created_at__date__lte=filters["created_at_to"])

        # Month filtering
        if filters.get("created_at_month"):
            queryset = queryset.filter(created_at__month=filters["created_at_month"])

        # Year filtering
        if filters.get("created_at_year"):
            queryset = queryset.filter(created_at__year=filters["created_at_year"])

        # Additional model-specific filters should be implemented in subclasses
        return self._apply_custom_filters(queryset, filters)

    def _apply_custom_filters(self, queryset, filters):
        """
        Apply model-specific filters.

        Override this method in subclasses to add custom filtering logic.
        """
        return queryset

    def _get_format_instance(self, file_format):
        """Get the appropriate format instance."""
        format_map = {
            "xlsx": AutoFitXLSX(),
            "xls": base_formats.XLS(),
            "csv": base_formats.CSV(),
            "json": base_formats.JSON(),
        }

        return format_map.get(file_format, AutoFitXLSX())

    def _generate_filename(self, filters, file_format):
        """
        Generate descriptive filename based on filters.

        Override this method to customize filename generation.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename_parts = [self.export_filename_prefix]

        # Add date range to filename
        if filters.get("created_at_from") and filters.get("created_at_to"):
            from_str = filters["created_at_from"].strftime("%Y%m%d")
            to_str = filters["created_at_to"].strftime("%Y%m%d")
            filename_parts.append(f"from_{from_str}_to_{to_str}")
        elif filters.get("created_at_from"):
            from_str = filters["created_at_from"].strftime("%Y%m%d")
            filename_parts.append(f"from_{from_str}")
        elif filters.get("created_at_to"):
            to_str = filters["created_at_to"].strftime("%Y%m%d")
            filename_parts.append(f"until_{to_str}")

        # Add month/year info
        if filters.get("created_at_month") and filters.get("created_at_year"):
            filename_parts.append(
                f'{filters["created_at_year"]}_month_{filters["created_at_month"]}'
            )
        elif filters.get("created_at_year"):
            filename_parts.append(f'year_{filters["created_at_year"]}')
        elif filters.get("created_at_month"):
            month_names = {
                "1": "jan",
                "2": "feb",
                "3": "mar",
                "4": "apr",
                "5": "may",
                "6": "jun",
                "7": "jul",
                "8": "aug",
                "9": "sep",
                "10": "oct",
                "11": "nov",
                "12": "dec",
            }
            month_name = month_names.get(
                filters["created_at_month"], filters["created_at_month"]
            )
            filename_parts.append(f"month_{month_name}")

        # Add custom filename parts
        filename_parts.extend(self._get_custom_filename_parts(filters))

        filename_parts.append(timestamp)

        return f'{"_".join(filename_parts)}.{file_format}'

    def _get_custom_filename_parts(self, filters) -> list:
        """
        Get custom filename parts based on filters.

        Override this method to add model-specific filename parts.
        """
        return []

    def _log_export_action(self, request, record_count, filters):
        """Log the export action for audit purposes (backend logging only)."""
        import logging

        logger = logging.getLogger(__name__)

        filter_info = []

        # Standard date filter logging
        if filters.get("created_at_from") or filters.get("created_at_to"):
            date_range = []
            if filters.get("created_at_from"):
                date_range.append(f"from {filters['created_at_from']}")
            if filters.get("created_at_to"):
                date_range.append(f"to {filters['created_at_to']}")
            filter_info.append(" ".join(date_range))

        if filters.get("created_at_month"):
            filter_info.append(f"month {filters['created_at_month']}")

        if filters.get("created_at_year"):
            filter_info.append(f"year {filters['created_at_year']}")

        # Add custom filter logging
        filter_info.extend(self._get_custom_filter_info(filters))

        filter_text = f" with filters: {', '.join(filter_info)}" if filter_info else ""

        # Only log to backend, no user-facing messages (handled by JavaScript)
        logger.info(
            f"User {request.user.username} exported {record_count} {self.model._meta.verbose_name} records{filter_text}"
        )

    def _get_custom_filter_info(self, filters) -> list:
        """
        Get custom filter information for logging.

        Override this method to add model-specific filter logging.
        """
        return []
