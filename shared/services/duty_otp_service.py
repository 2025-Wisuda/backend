"""
OTP Service for Duty Attendance System.

Provides OTP generation, validation, and management specifically for duty attendance.
"""

import random
import string
from datetime import timedelta
from typing import Dict, Tuple

from django.core.cache import cache
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class DutyOTPService:
    """Service for managing OTP for duty attendance system."""

    # OTP Configuration
    OTP_LENGTH = 6
    # Set OTP expiry to 0.5 minutes (30 seconds) for rapid testing
    OTP_EXPIRY_MINUTES = 0.5
    OTP_CACHE_PREFIX = "duty_otp"
    OTP_USAGE_PREFIX = "duty_otp_used"

    @classmethod
    def generate_otp(cls) -> str:
        """Generate a random 6-digit OTP."""
        return "".join(random.choices(string.digits, k=cls.OTP_LENGTH))

    @classmethod
    def get_current_otp(cls) -> Dict:
        """
        Get or generate current OTP for the laboratory.
        Returns the same OTP for all users within the expiry period.
        """
        cache_key = f"{cls.OTP_CACHE_PREFIX}:current"
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        # Generate new OTP
        otp_code = cls.generate_otp()
        expiry_time = timezone.localtime() + timedelta(minutes=cls.OTP_EXPIRY_MINUTES)

        otp_data = {
            "code": otp_code,
            "generated_at": timezone.localtime().isoformat(),
            "expires_at": expiry_time.isoformat(),
            "remaining_seconds": cls.OTP_EXPIRY_MINUTES * 60,
        }

        # Cache for the expiry duration
        cache.set(cache_key, otp_data, timeout=int(cls.OTP_EXPIRY_MINUTES * 60))

        return otp_data

    @classmethod
    def validate_otp(cls, otp_code: str, user_id: str = None) -> Tuple[bool, str]:
        """
        Validate OTP code against current active OTP.

        Args:
            otp_code: The OTP code to validate
            user_id: Optional user ID for usage tracking

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not otp_code or len(otp_code) != cls.OTP_LENGTH:
            return False, _("OTP must be exactly 6 digits")

        if not otp_code.isdigit():
            return False, _("OTP must contain only numbers")

        # Get current OTP
        current_otp_data = cache.get(f"{cls.OTP_CACHE_PREFIX}:current")
        if not current_otp_data:
            return False, _("No active OTP found. Please get a new OTP.")

        # Validate OTP code
        if current_otp_data["code"] != otp_code:
            return False, _("Invalid OTP code")

        # Check if OTP was already used by this user (prevent replay)
        if user_id:
            usage_key = f"{cls.OTP_USAGE_PREFIX}:{user_id}:{otp_code}"
            if cache.get(usage_key):
                return False, _("OTP already used")

        return True, _("OTP validated successfully")

    @classmethod
    def mark_otp_used(
        cls, otp_code: str, user_id: str, action_type: str = "attendance"
    ):
        """
        Mark OTP as used by a specific user to prevent replay attacks.

        Args:
            otp_code: The OTP code that was used
            user_id: User who used the OTP
            action_type: Type of action (clock_in, clock_out, etc.)
        """
        usage_key = f"{cls.OTP_USAGE_PREFIX}:{user_id}:{otp_code}"
        usage_data = {
            "used_at": timezone.localtime().isoformat(),
            "action_type": action_type,
            "user_id": user_id,
        }

        # Cache usage for the same duration as OTP expiry
        cache.set(usage_key, usage_data, timeout=int(cls.OTP_EXPIRY_MINUTES * 60))

    @classmethod
    def get_otp_status(cls) -> Dict:
        """
        Get current OTP status including remaining time.
        """
        cache_key = f"{cls.OTP_CACHE_PREFIX}:current"
        cached_data = cache.get(cache_key)

        if not cached_data:
            return {"has_active_otp": False, "message": "No active OTP"}

        # Calculate remaining time
        expires_at = timezone.datetime.fromisoformat(cached_data["expires_at"])
        if timezone.is_naive(expires_at):
            expires_at = timezone.make_aware(expires_at)

        remaining_seconds = max(0, int((expires_at - timezone.localtime()).total_seconds()))

        return {
            "has_active_otp": True,
            "code": cached_data["code"],
            "expires_at": cached_data["expires_at"],
            "remaining_seconds": remaining_seconds,
            "remaining_minutes": remaining_seconds // 60,
        }

    @classmethod
    def force_new_otp(cls) -> Dict:
        """
        Force generation of new OTP (invalidates current one).
        """
        cache_key = f"{cls.OTP_CACHE_PREFIX}:current"
        cache.delete(cache_key)
        return cls.get_current_otp()
