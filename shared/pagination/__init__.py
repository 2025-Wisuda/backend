"""
Shared Pagination Module for Django REST Framework

This module provides customized pagination utilities for Django REST Framework
API endpoints. It ensures consistent paginated responses across all list views
with enhanced metadata and client-friendly pagination information.

What: Custom pagination class for DRF list views with enhanced response format
Why: Standardizes pagination across all API endpoints and provides rich metadata
How: Import CustomPagination and set as pagination_class in your DRF views

Main Components:
- CustomPagination: Enhanced DRF PageNumberPagination with metadata and configuration

Key Features:
- Consistent paginated response format across all API endpoints
- Configurable page size with client-controlled pagination
- Rich pagination metadata including total counts and navigation links
- Default page size of 10 items with maximum of 100 items per page
- URL-based page size parameter for flexible client control
- Integration with ResponsePresenter for consistent API responses
- Support for large dataset pagination with performance optimizations

Response Format:
{
    "status": "success",
    "message": "Data retrieved successfully",
    "data": {
        "results": [...],       // Paginated items
        "count": 150,           // Total number of items
        "next": "http://...",   // Next page URL or null
        "previous": "http://...", // Previous page URL or null
        "page_size": 10,        // Current page size
        "current_page": 1,      // Current page number
        "total_pages": 15       // Total number of pages
    }
}

Configuration:
- Default page size: 10 items
- Maximum page size: 100 items
- Page size parameter: 'page_size' (URL query parameter)
- Page parameter: 'page' (URL query parameter)

Usage Examples:
    from shared.pagination import CustomPagination
    from rest_framework.generics import ListAPIView
    
    class CourseListView(ListAPIView):
        queryset = Course.objects.all()
        serializer_class = CourseSerializer
        pagination_class = CustomPagination
    
    # API calls with pagination:
    # GET /api/courses/                    # Default: page 1, 10 items
    # GET /api/courses/?page=2             # Page 2, 10 items
    # GET /api/courses/?page_size=25       # Page 1, 25 items
    # GET /api/courses/?page=3&page_size=50 # Page 3, 50 items

ViewSet Integration:
    from rest_framework.viewsets import ModelViewSet
    
    class UserViewSet(ModelViewSet):
        queryset = User.objects.all()
        serializer_class = UserSerializer
        pagination_class = CustomPagination
        
        def list(self, request, *args, **kwargs):
            # CustomPagination automatically handles pagination
            return super().list(request, *args, **kwargs)

Client-Side Usage:
    // JavaScript example for consuming paginated API
    async function fetchCourses(page = 1, pageSize = 10) {
        const response = await fetch(
            `/api/courses/?page=${page}&page_size=${pageSize}`
        );
        const data = await response.json();
        
        if (data.status === 'success') {
            return {
                items: data.data.results,
                totalCount: data.data.count,
                currentPage: data.data.current_page,
                totalPages: data.data.total_pages,
                hasNext: !!data.data.next,
                hasPrevious: !!data.data.previous
            };
        }
    }

Benefits:
- Consistent pagination experience across all API endpoints
- Client-friendly response format with rich metadata
- Configurable page sizes for different use cases
- Performance optimization for large datasets
- Easy integration with existing DRF views and viewsets
- Standard URL parameters for predictable API behavior
- Comprehensive pagination information for UI development
"""

from .custom_pagination import CustomPagination

__all__ = ["CustomPagination"]
