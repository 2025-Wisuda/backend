"""Course session API serializers with status management and validation."""

from rest_framework import serializers

from custom_auth.models import CustomUserModel
from custom_auth.rest.serializers import UserListSerializer

from ...models import CourseModel, CourseSessionModel


class CourseSessionListSerializer(serializers.ModelSerializer):
    """Course session list with essential fields only."""

    class Meta:
        model = CourseSessionModel
        fields = [
            "id",
            "title",
            "type",
            "date",
            "start_time",
            "end_time",
            "status",
        ]


class CourseSessionDetailSerializer(serializers.ModelSerializer):
    """Course session detail with full management capabilities."""

    teaching_assistants = UserListSerializer(many=True, read_only=True)
    teaching_assistant_ids = serializers.PrimaryKeyRelatedField(
        queryset=CustomUserModel.objects.filter(is_active=True),
        many=True,
        write_only=True,
        source="teaching_assistants",
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = CourseSessionModel
        fields = [
            "id",
            "title",
            "description",
            "type",
            "date",
            "start_time",
            "end_time",
            "status",
            "teaching_assistants",
            "teaching_assistant_ids",
        ]

        read_only_fields = [
                        "status",

        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set queryset for teaching_assistant_ids based on course
        course = self.context.get("course")
        if course:
            self.fields["teaching_assistant_ids"].queryset = (
                course.teaching_assistants.filter(is_active=True)
            )
        else:
            # If no course in context, allow all active users (will be validated later)
            from custom_auth.models import CustomUserModel

            self.fields["teaching_assistant_ids"].queryset = (
                CustomUserModel.objects.filter(is_active=True)
            )

    def validate(self, data):
        """Validate session data."""
        course = self.context.get("course")
        date = data.get("date")

        # Validate session is within course period
        if course and date:
            if date < course.start_date:
                raise serializers.ValidationError(
                    {"date": "Session date cannot be before course start date."}
                )
            elif date > course.end_date:
                raise serializers.ValidationError(
                    {"date": "Session date cannot be after course end date."}
                )

        return data

    def validate_teaching_assistant_ids(self, value):
        """Validate teaching assistants are assigned to the course."""
        course = self.context.get("course")

        if course and value:
            course_ta_ids = set(course.teaching_assistants.values_list("id", flat=True))
            session_ta_ids = set(ta.id for ta in value)

            if not session_ta_ids.issubset(course_ta_ids):
                raise serializers.ValidationError(
                    "All teaching assistants must be assigned to the course first."
                )

        return value
