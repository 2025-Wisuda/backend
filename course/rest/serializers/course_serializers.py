"""Course API serializers with enrollment validation."""

import json

from rest_framework import serializers

from custom_auth.models import CustomUserModel
from custom_auth.rest.serializers import UserListSerializer

from ...models import CourseModel


class FlexibleManyToManyField(serializers.Field):
    """
    Custom field that can handle many-to-many relationships with flexible input:
    1. JSON strings from FormData: '["uuid1","uuid2"]'
    2. Regular arrays: ["uuid1","uuid2"] 
    3. Single values: "uuid1"
    4. Empty arrays: "[]" or []
    """
    
    def __init__(self, **kwargs):
        self.queryset = kwargs.pop('queryset')
        super().__init__(**kwargs)
    
    def to_internal_value(self, data):
        # Handle string inputs (from FormData)
        if isinstance(data, str):
            try:
                # Handle empty arrays
                if data.strip() == "[]" or data.strip() == "":
                    return []
                
                # Try to parse as JSON
                parsed_data = json.loads(data)
                if isinstance(parsed_data, list):
                    # It's a JSON array - validate each UUID
                    return self._validate_uuids(parsed_data)
                else:
                    # It's a single value wrapped in JSON
                    return self._validate_uuids([parsed_data])
                    
            except (json.JSONDecodeError, ValueError):
                # Not valid JSON, treat as single UUID string
                if data.strip():
                    return self._validate_uuids([data.strip()])
                else:
                    return []
        
        # Handle list inputs (normal case)
        elif isinstance(data, list):
            return self._validate_uuids(data)
        
        # Handle single value inputs
        elif data is not None:
            return self._validate_uuids([data])
        
        # Handle None/empty
        else:
            return []
    
    def _validate_uuids(self, uuid_list):
        """Validate list of UUIDs and return model instances."""
        if not uuid_list:
            return []
        
        try:
            # Get all instances at once for efficiency
            instances = list(self.queryset.filter(id__in=uuid_list))
            
            # Check if all UUIDs were found
            found_ids = {str(instance.id) for instance in instances}
            for uuid_str in uuid_list:
                if str(uuid_str) not in found_ids:
                    raise serializers.ValidationError(f"Invalid pk \"{uuid_str}\" - object does not exist.")
            
            return instances
            
        except Exception as e:
            if isinstance(e, serializers.ValidationError):
                raise
            raise serializers.ValidationError(f"Invalid UUID format: {str(e)}")
    
    def to_representation(self, value):
        """Convert instances to UUIDs for representation."""
        if hasattr(value, 'all'):
            return [str(instance.id) for instance in value.all()]
        return [str(instance.id) for instance in value]


class CourseListSerializer(serializers.ModelSerializer):
    """Course list with session counts and minimal data."""

    total_sessions = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()
    total_teaching_assistants = serializers.SerializerMethodField()
    has_enrollment = serializers.SerializerMethodField()    
    is_enrollment_open = serializers.SerializerMethodField()
    is_participant = serializers.SerializerMethodField()

    class Meta:
        model = CourseModel
        fields = [
            "id",
            "title",
            "description",
            "start_date",
            "end_date",
            "total_sessions",
            "image",
            "has_enrollment",            
            "is_enrollment_open",
            "is_participant",
            "total_students",
            "total_teaching_assistants",

        ]

        read_only_fields = [
            "id",
            "title",
            "description",
            "start_date",
            "end_date",
            "total_sessions",
            "image",
            "has_enrollment",
            "is_enrollment_open",
            "is_participant",
            "total_students",
            "total_teaching_assistants",
        ]
        
    def get_is_participant(self, obj):
        """Check if the user is a participant in this course."""
        request = self.context.get("request")
        if not request or not hasattr(request, 'user') or not request.user:
            return False
        user = request.user
        return obj.students.filter(id=user.id).exists() or obj.teaching_assistants.filter(id=user.id).exists()

    def get_total_sessions(self, obj):
        """Get total number of sessions for this course."""
        return obj.sessions.filter(is_active=True).count()
    
    def get_total_students(self, obj):
        """Get real-time count of enrolled students."""
        return obj.students.filter(is_active=True).count()
    
    def get_total_teaching_assistants(self, obj):
        """Get real-time count of assigned teaching assistants."""
        return obj.teaching_assistants.filter(is_active=True).count()
    
    def get_has_enrollment(self, obj):
        """Check if course has enrollment key (without exposing the key)."""
        return bool(obj.enroll_key and obj.enroll_key.strip())
    
    def get_is_enrollment_open(self, obj):
        """Check if enrollment is currently open."""
        from datetime import date

        return (
            self.get_has_enrollment(obj)
            and obj.is_active
            and obj.start_date >= date.today()
        )

class CourseDetailSerializer(serializers.ModelSerializer):
    """Course management with enrollment keys and session data."""

    # Input fields (write-only) - can handle JSON strings from FormData
    student_ids = FlexibleManyToManyField(
        queryset=CustomUserModel.objects.filter(is_active=True), 
        required=False,
        write_only=True,
        source='students',
        help_text="List of student UUIDs to enroll (accepts JSON string or array)"
    )
    teaching_assistant_ids = FlexibleManyToManyField(
        queryset=CustomUserModel.objects.filter(is_active=True), 
        required=False,
        write_only=True,
        source='teaching_assistants',
        help_text="List of teaching assistant UUIDs to assign (accepts JSON string or array)"
    )

    # Output fields (read-only) - return full user objects
    students = serializers.SerializerMethodField(read_only=True)
    teaching_assistants = serializers.SerializerMethodField(read_only=True)

    enroll_key = serializers.CharField(
        max_length=50,
        required=False,
        write_only=True,
        help_text="Enrollment key for course enrollment (write-only for security)",
    )

    recent_sessions = serializers.SerializerMethodField()
    total_sessions = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()
    total_teaching_assistants = serializers.SerializerMethodField()
    has_enrollment = serializers.SerializerMethodField()
    is_enrollment_open = serializers.SerializerMethodField()
    is_participant = serializers.SerializerMethodField()

    class Meta:
        model = CourseModel
        fields = [
            "id",
            "title",
            "description",
            "start_date",
            "end_date",
            # Input fields
            "student_ids",
            "teaching_assistant_ids",
            # Output fields
            "students",
            "teaching_assistants",
            "total_students",
            "total_teaching_assistants",
            "total_sessions",
            "enroll_key",
            "has_enrollment",
            "is_enrollment_open",
            "image",
            "recent_sessions",
            "is_participant",
            "created_by",            
        ]
        read_only_fields = [
            "id",
            "students",
            "teaching_assistants", 
            "total_students",
            "total_teaching_assistants",
            "total_sessions",
            "recent_sessions",
            "has_enrollment",
            "is_enrollment_open",
            "is_participant",
            "created_by",            
        ]

    def get_students(self, obj):
        """Get full student objects for response."""
        return UserListSerializer(obj.students.filter(is_active=True), many=True).data

    def get_teaching_assistants(self, obj):
        """Get full teaching assistant objects for response."""
        return UserListSerializer(obj.teaching_assistants.filter(is_active=True), many=True).data

    def get_recent_sessions(self, obj):
        """Get all sessions for this course."""
        sessions = obj.sessions.filter(is_active=True).order_by(
            "-date", "-start_time"
        )

        from .course_session_serializers import CourseSessionListSerializer

        return CourseSessionListSerializer(sessions, many=True).data

    def get_total_sessions(self, obj):
        """Get total number of sessions for this course."""
        return obj.sessions.filter(is_active=True).count()

    def get_total_students(self, obj):
        """Get real-time count of enrolled students."""
        return obj.students.filter(is_active=True).count()
    
    def get_total_teaching_assistants(self, obj):
        """Get real-time count of assigned teaching assistants."""
        return obj.teaching_assistants.filter(is_active=True).count()

    def get_has_enrollment(self, obj):
        """Check if course has enrollment key (without exposing the key)."""
        return bool(obj.enroll_key and obj.enroll_key.strip())

    def get_is_enrollment_open(self, obj):
        """Check if enrollment is currently open."""
        from datetime import date

        return (
            self.get_has_enrollment(obj)
            and obj.is_active
            and obj.start_date >= date.today()
        )

    def validate(self, data):
        """Validate course data."""
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {"end_date": "End date must be equal to or after start date."}
            )

        return data

    def get_is_participant(self, obj):
        """Check if the user is a participant in this course."""
        request = self.context.get("request")
        if not request or not hasattr(request, 'user') or not request.user:
            return False
        user = request.user
        return obj.students.filter(id=user.id).exists() or obj.teaching_assistants.filter(id=user.id).exists()

    def create(self, validated_data):
        """Custom create to handle many-to-many fields properly."""
        # Extract many-to-many fields (source mapping handles the field names)
        students = validated_data.pop('students', [])
        teaching_assistants = validated_data.pop('teaching_assistants', [])
        
        # Create the course instance
        course = super().create(validated_data)
        
        # Set many-to-many relationships
        course.students.set(students)
        course.teaching_assistants.set(teaching_assistants)
        
        return course

    def update(self, instance, validated_data):
        """Custom update to handle many-to-many fields properly."""
        # Extract many-to-many fields (source mapping handles the field names)
        students = validated_data.pop('students', None)
        teaching_assistants = validated_data.pop('teaching_assistants', None)
        
        # Update regular fields
        instance = super().update(instance, validated_data)
        
        # Update many-to-many fields if provided
        if students is not None:
            instance.students.set(students)
        
        if teaching_assistants is not None:
            instance.teaching_assistants.set(teaching_assistants)
        
        return instance

    def to_representation(self, instance):
        """Override to include created_by user details."""
        data = super().to_representation(instance)
        
        # Include created_by user details
        if hasattr(instance, 'created_by') and instance.created_by:
            data['created_by'] = UserListSerializer(instance.created_by).data
            
        return data

class CourseEnrollSerializer(serializers.Serializer):
    """Course enrollment with key validation."""

    enroll_key = serializers.CharField(
        max_length=50,
        help_text="Enrollment key provided by the instructor",
    )

    def validate_enroll_key(self, value):
        """Validate that enrollment key exists and course is active."""
        try:
            course = CourseModel.objects.get(enroll_key=value, is_active=True)
        except CourseModel.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid enrollment key or course is not active."
            )

        self.context["course"] = course
        return value
