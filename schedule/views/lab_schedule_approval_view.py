from datetime import datetime
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from schedule.models import LabSchedule
from schedule.serializers import LabScheduleApprovalSerializer


class LabScheduleApprovalViewSet(viewsets.ModelViewSet):
    queryset = LabSchedule.objects.prefetch_related(
        "created_by",
        "approved_by",
    ).all()
    serializer_class = LabScheduleApprovalSerializer

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        if not request.user.is_staff and not request.user.is_superuser:
            raise PermissionDenied(
                "You do not have permission to update the approval status."
            )

        if instance.approval_status != "menunggu":
            raise PermissionDenied(
                "Only schedules with 'menunggu' status can be updated."
            )

        status = request.data.get("approval_status")
        if status not in ["ditolak", "diterima"]:
            raise PermissionDenied("Approval status must be 'ditolak' or 'diterima'.")

        if status == "diterima":
            instance.approved_by = request.user
            instance.approval_time = datetime.now()
        else:
            instance.approved_by = None
            instance.approval_time = None

        instance.approval_status = status
        instance.save()

        return super().partial_update(request, *args, **kwargs)
