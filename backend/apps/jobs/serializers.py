from rest_framework import serializers
from rest_framework.validators import ValidationError

from .models import Job


class JobCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a job (recruiter only)"""
    class Meta:
        model = Job
        fields = (
            "title",
            "company_name",
            "location",
            "employment_type",
            "experience_level",
            "description",
            "requirements",
            "responsibilities",
            "salary_min",
            "salary_max",
            "currency",
            "is_remote",
            "status",
        )
        read_only_fields = ("id", "created_at", "updated_at", "closed_at")

    def validate_title(self, value):
        if not value or not value.strip():
            raise ValidationError("Title is required.")
        return value

    def validate_description(self, value):
        if not value or not value.strip():
            raise ValidationError("Description is required.")
        return value

    def validate(self, attrs):
        if attrs.get("salary_min") and attrs.get("salary_max"):
            if attrs["salary_min"] > attrs["salary_max"]:
                raise ValidationError(
                    {"salary_min": "salary_min must be less than or equal to salary_max"}
                )
        return attrs

    def create(self, validated_data):
        validated_data["recruiter"] = self.context["request"].user
        return super().create(validated_data)


class JobUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a job (recruiter only)"""
    class Meta:
        model = Job
        fields = (
            "title",
            "company_name",
            "location",
            "employment_type",
            "experience_level",
            "description",
            "requirements",
            "responsibilities",
            "salary_min",
            "salary_max",
            "currency",
            "is_remote",
            "status",
        )
        read_only_fields = ("id", "recruiter", "created_at", "updated_at", "closed_at")

    def validate(self, attrs):
        salary_min = attrs.get("salary_min", self.instance.salary_min)
        salary_max = attrs.get("salary_max", self.instance.salary_max)
        if salary_min and salary_max and salary_min > salary_max:
            raise ValidationError(
                {"salary_min": "salary_min must be less than or equal to salary_max"}
            )
        return attrs


class JobDetailSerializer(serializers.ModelSerializer):
    """Serializer for job detail view"""
    recruiter_id = serializers.UUIDField(source="recruiter.id", read_only=True)
    recruiter_email = serializers.EmailField(source="recruiter.email", read_only=True)

    class Meta:
        model = Job
        fields = (
            "id",
            "recruiter_id",
            "recruiter_email",
            "title",
            "company_name",
            "location",
            "employment_type",
            "experience_level",
            "description",
            "requirements",
            "responsibilities",
            "salary_min",
            "salary_max",
            "currency",
            "is_remote",
            "status",
            "created_at",
            "updated_at",
            "closed_at",
        )
        read_only_fields = (
            "id",
            "recruiter_id",
            "recruiter_email",
            "created_at",
            "updated_at",
            "closed_at",
        )


class JobListSerializer(serializers.ModelSerializer):
    """Serializer for job list view"""
    recruiter_id = serializers.UUIDField(source="recruiter.id", read_only=True)
    recruiter_email = serializers.EmailField(source="recruiter.email", read_only=True)

    class Meta:
        model = Job
        fields = (
            "id",
            "recruiter_id",
            "recruiter_email",
            "title",
            "company_name",
            "location",
            "employment_type",
            "experience_level",
            "status",
            "is_remote",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "recruiter_id",
            "recruiter_email",
            "created_at",
            "updated_at",
        )
