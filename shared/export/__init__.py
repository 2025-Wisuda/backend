"""
Shared export functionality for Django models.

This package provides reusable components for implementing export functionality
across different Django models with:

- Field selection with checkboxes
- Date filtering (range, month, year)  
- Multiple export formats (Excel, CSV, JSON)
- Permission checking
- Audit logging
- Responsive UI with modern styling

Components:
- BaseExportView: Generic export view class
- BaseExportForm: Generic export form class  
- ModelSpecificExportFormMixin: Helper mixin for model-specific forms
- base_export_form.html: Base template for export forms

Usage:
    from shared.export import BaseExportView, BaseExportForm
    
    class MyModelExportForm(BaseExportForm):
        FIELD_CHOICES = [
            ('name', 'Name'),
            ('email', 'Email'),
            # ... other fields
        ]
        DEFAULT_FIELDS = ['name', 'email']
    
    class MyModelExportView(BaseExportView):
        model = MyModel
        resource_class = MyModelResource
        form_class = MyModelExportForm
        template_name = 'admin/myapp/mymodel/export_form.html'
"""

from .base_export_form import BaseExportForm, ModelSpecificExportFormMixin
from .base_export_view import BaseExportView

__all__ = [
    "BaseExportView",
    "BaseExportForm",
    "ModelSpecificExportFormMixin",
]
