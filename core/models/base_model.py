"""
Abstract base model providing common fields for all models.

Includes:
- UUID primary key (`id`)
- Active status flag (`is_active`)
- Audit trail fields (`created_by`, `created_at`, `updated_by`, `updated_at`)

This base class is intended to be inherited by other models to ensure consistent tracking 
of creation and modification metadata across the application.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_("ID")
    )
    is_active = models.BooleanField(
        default=True,
        null=False,
        blank=False,
        verbose_name=_("Is Active"),
        help_text=_("Indicates whether this record is active or not"),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_%(class)s_set",
        verbose_name=_("Created By"),
        help_text=_("User who created this record"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("Timestamp when this record was created"),
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_%(class)s_set",
        verbose_name=_("Updated By"),
        help_text=_("User who last updated this record"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Timestamp when this record was last updated"),
    )

    class Meta:
        abstract = True
