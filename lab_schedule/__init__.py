"""
Lab Schedule Management Module for Laboratory Conflict Detection.

Key Business Logic:
- Centralized conflict detection across all booking types
- Pure aggregator model without approval workflows
- Cross-model validation and time slot management
- Read-only API for schedule viewing and availability checking
- Integration with all lab booking workflows for conflict prevention

Main Components:
    LabScheduleModel: Central aggregator for all lab time slots
    LabScheduleDashboardModel: Dashboard analytics and statistics
    Admin interfaces: Schedule monitoring and conflict resolution tools
"""
