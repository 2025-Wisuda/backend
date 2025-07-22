"""
Custom Authentication Module

Laboratory management system's custom authentication and user management module.

This module extends Django's built-in authentication with laboratory-specific features:

Key Features:
- Extended user model with role-based validation
- Student/Staff identification number management
- Face recognition integration for attendance
- Comprehensive admin interface with export functionality
- RESTful API for user management and authentication
- JWT-based authentication with secure token management

Module Structure:
- models/: Extended user model with laboratory-specific fields
- rest/: RESTful API implementation (filters, schemas, serializers, views, urls)
- admins/: Enhanced Django admin interface with export capabilities
- management/: Django management commands
- migrations/: Database schema migrations
"""
