from django.contrib.auth import get_user_model
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

User = get_user_model()


class BaseUserSerializer(serializers.ModelSerializer):
    group = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_group(self, obj):
        group = obj.groups.first()
        return group.name if group else None

    class Meta:
        model = User
        fields = ["group"]


class ProfileSerializer(BaseUserSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta(BaseUserSerializer.Meta):
        fields = [
            "id",
            "password",
            "last_login",
            "is_superuser",
            "username",
            "student_id",
            "employee_id",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
            "date_joined",
            "face_image",
            "face_uploaded",
            "avatar",
            "group",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "last_login",
            "is_superuser",
            "username",
            "is_active",
            "is_staff",
            "date_joined",
            "face_uploaded",
            "group",
            "created_at",
            "updated_at",
        ]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserListSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ["id", "username", "first_name", "last_name", "avatar", "group"]


class UserDetailSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "student_id",
            "employee_id",
            "is_active",
            "avatar",
            "group",
        ]


class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]
