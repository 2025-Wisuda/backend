"""Expose selected admin components for external use."""

from .admins.lab_allocation_admin import LabAllocationAdmin

__all__ = [
    "LabAllocationAdmin",
]
