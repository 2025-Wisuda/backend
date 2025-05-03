from rest_framework import serializers
from schedule.models import DutyDate


class DutyDateNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyDate
        fields = ["id", "duty_date"]
