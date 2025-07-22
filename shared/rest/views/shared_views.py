"""
Shared REST API views.

Common views that are shared across multiple apps.
"""

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from core.enums import UserGroup
from shared.presenter import ResponsePresenter
from shared.services.duty_otp_service import DutyOTPService


@api_view(['GET'])
@permission_classes([AllowAny])  # Allow access without authentication for admin panel
def get_current_otp(request):
    """Get current OTP for admin/lab staff use - no auth required for admin panel."""
    
    otp_data = DutyOTPService.get_current_otp()
    
    return ResponsePresenter.success_response(
        message="Current OTP retrieved successfully",
        data=otp_data
    )


# COMMENTED OUT TO PREVENT FRAUD - NO MANUAL OTP GENERATION/RESET
# @api_view(['POST'])  
# @permission_classes([AllowAny])  # Allow access without authentication for admin panel
# def generate_new_otp(request):
#     """Force generate new OTP for admin use - no auth required for admin panel."""
#     
#     otp_data = DutyOTPService.force_new_otp()
#     
#     return ResponsePresenter.success_response(
#         message="New OTP generated successfully",
#         data=otp_data
#     )


# COMMENTED OUT TO PREVENT FRAUD - NO MANUAL OTP STATUS CHECK
# @api_view(['GET'])
# @permission_classes([AllowAny])  # Allow access without authentication for admin panel
# def get_otp_status(request):
#     """Get OTP status for monitoring - no auth required for admin panel."""
#     
#     status_data = DutyOTPService.get_otp_status()
#     
#     return ResponsePresenter.success_response(
#         message="OTP status retrieved successfully", 
#         data=status_data
#     ) 