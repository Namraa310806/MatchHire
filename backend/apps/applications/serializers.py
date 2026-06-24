from rest_framework import serializers

from .models import Application, ApplicationStatusHistory
from .services.workflow import ApplicationWorkflowService


class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ["resume_version_id"]


class ApplicationListSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)
    candidate_email = serializers.CharField(source="candidate.email", read_only=True)
    candidate_id = serializers.UUIDField(source="candidate.id", read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "job_title",
            "candidate_name",
            "candidate_email",
            "candidate_id",
            "resume_version_id",
            "status",
            "created_at",
            "updated_at",
        ]


class ApplicationDetailSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)
    candidate_email = serializers.CharField(source="candidate.email", read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "job_id",
            "job_title",
            "candidate_id",
            "candidate_name",
            "candidate_email",
            "resume_version_id",
            "status",
            "created_at",
            "updated_at",
        ]


class ApplicationStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Application.ApplicationStatus.choices)

    def validate_status(self, value):
        """Validate the status field"""
        if not Application.ApplicationStatus.choices:
            raise serializers.ValidationError("Invalid status.")
        return value

    def validate(self, attrs):
        """Validate status transition"""
        # Get the current status from the instance if available
        if self.instance:
            old_status = self.instance.status
            new_status = attrs["status"]
            
            if not ApplicationWorkflowService.validate_transition(old_status, new_status):
                raise serializers.ValidationError("Invalid status transition.")
        
        return attrs


class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    changed_by = serializers.EmailField(source="changed_by.email", read_only=True)

    class Meta:
        model = ApplicationStatusHistory
        fields = [
            "old_status",
            "new_status",
            "changed_by",
            "changed_at",
            "notes",
        ]
