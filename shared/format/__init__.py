"""
Shared format package for data export and file formatting utilities.

This package provides custom formatters and export utilities for generating
professional-looking files from application data. It extends Django's
built-in formatting capabilities with enhanced styling, internationalization
support, and automatic formatting features.

Main Components:
- AutoFitXLSX: Enhanced Excel export format with auto-fitting columns and styling

Key Features:
- Professional Excel exports with automatic column width adjustment
- Enhanced header styling for better readability
- International character support for multilingual data
- Fallback mechanisms for robust error handling
- Configurable padding and width constraints
- Logging and debugging support for export operations

Export Capabilities:
- XLSX files with auto-fitted columns based on content
- Bold, centered headers for professional appearance
- Intelligent width calculation considering character types
- Support for non-ASCII characters with proper spacing
- Maximum and minimum width constraints for optimal display

Usage Examples:
    from shared.format import AutoFitXLSX
    from django_import_export import Dataset
    
    # Create dataset from model data
    dataset = Dataset()
    dataset.headers = ['Name', 'Email', 'Created At']
    dataset.append(['John Doe', 'john@example.com', '2025-01-01'])
    dataset.append(['Jane Smith', 'jane@example.com', '2025-01-02'])
    
    # Export with auto-fit formatting
    formatter = AutoFitXLSX()
    xlsx_data = formatter.export_data(dataset)
    
    # Save to file or return as HTTP response
    with open('export.xlsx', 'wb') as f:
        f.write(xlsx_data)

Integration with Django Import-Export:
    from import_export import resources
    from shared.format import AutoFitXLSX
    
    class UserResource(resources.ModelResource):
        class Meta:
            model = User
            formats = [AutoFitXLSX]  # Use custom format
    
    # In views or admin
    resource = UserResource()
    dataset = resource.export()
    xlsx_data = AutoFitXLSX().export_data(dataset)

AutoFitXLSX Features:
- Automatic column width calculation based on content length
- Enhanced width calculation for international characters (CJK, Arabic, etc.)
- Professional header styling with bold fonts and center alignment
- Configurable minimum width (10 characters) and maximum width (60 characters)
- Padding adjustment (4 characters) for better readability
- Error handling with fallback to standard XLSX export
- Debug logging for troubleshooting width calculations

Character Handling:
- ASCII characters: Standard width calculation
- Non-ASCII characters: 30% width increase for proper display
- CJK characters: Properly accommodated with enhanced spacing
- Unicode support: Full internationalization compatibility

Error Handling:
- Graceful fallback to standard XLSX export on formatting errors
- Comprehensive error logging for debugging
- Maintains data integrity even when styling fails
- Non-blocking errors that don't prevent data export

Benefits:
- Professional-looking Excel exports without manual formatting
- Improved readability with auto-fitted columns
- Consistent styling across all exports
- International character support for global applications
- Robust error handling for production environments
- Easy integration with existing Django Import-Export workflows
"""

from .custom_xlsx_format import AutoFitXLSX

__all__ = ["AutoFitXLSX"]
