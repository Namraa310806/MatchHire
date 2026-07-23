from rest_framework import serializers

from .models import Interview, InterviewStatusHistory
from .services.workflow import InterviewWorkflowService


class InterviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = [
            "scheduled_at",
            "duration_minutes",
            "interview_type",
            "meeting_link",
            "location",
            "notes",
        ]

    def validate(self, attrs):
        """Validate interview-specific rules"""
        interview_type = attrs.get("interview_type")
        meeting_link = attrs.get("meeting_link")
        location = attrs.get("location")
        duration_minutes = attrs.get("duration_minutes")

        # VIDEO interviews require meeting_link
        if interview_type == Interview.InterviewType.VIDEO and not meeting_link:
            raise serializers.ValidationError(
                {"meeting_link": "meeting_link is required for VIDEO interviews."}
            )

        # ONSITE interviews require location
        if interview_type == Interview.InterviewType.ONSITE and not location:
            raise serializers.ValidationError(
                {"location": "location is required for ONSITE interviews."}
            )

        # duration_minutes must be positive
        if duration_minutes and duration_minutes <= 0:
            raise serializers.ValidationError(
                {"duration_minutes": "duration_minutes must be greater than 0."}
            )

        return attrs


class InterviewListSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(
        source="application.candidate.full_name", read_only=True
    )
    candidate_email = serializers.CharField(
        source="application.candidate.email", read_only=True
    )
    job_title = serializers.CharField(source="application.job.title", read_only=True)

    class Meta:
        model = Interview
        fields = [
            "id",
            "application_id",
            "candidate_name",
            "candidate_email",
            "job_title",
            "scheduled_at",
            "duration_minutes",
            "interview_type",
            "meeting_link",
            "location",
            "status",
            "created_at",
            "updated_at",
        ]


class InterviewDetailSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(
        source="application.candidate.full_name", read_only=True
    )
    candidate_email = serializers.CharField(
        source="application.candidate.email", read_only=True
    )
    candidate_id = serializers.UUIDField(
        source="application.candidate.id", read_only=True
    )
    job_title = serializers.CharField(source="application.job.title", read_only=True)
    job_id = serializers.UUIDField(source="application.job.id", read_only=True)
    created_by_email = serializers.CharField(source="created_by.email", read_only=True)

    class Meta:
        model = Interview
        fields = [
            "id",
            "application_id",
            "candidate_id",
            "candidate_name",
            "candidate_email",
            "job_id",
            "job_title",
            "scheduled_at",
            "duration_minutes",
            "interview_type",
            "meeting_link",
            "location",
            "notes",
            "status",
            "created_by_email",
            "created_at",
            "updated_at",
        ]


class InterviewStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Interview.InterviewStatus.choices)

    def validate_status(self, value):
        """Validate the status field"""
        if not Interview.InterviewStatus.choices:
            raise serializers.ValidationError("Invalid status.")
        return value

    def validate(self, attrs):
        """Validate status transition"""
        # Get the current status from the instance if available
        if self.instance:
            old_status = self.instance.status
            new_status = attrs["status"]

            if not InterviewWorkflowService.validate_transition(old_status, new_status):
                raise serializers.ValidationError("Invalid status transition.")

        return attrs


class InterviewStatusHistorySerializer(serializers.ModelSerializer):
    changed_by = serializers.EmailField(source="changed_by.email", read_only=True)

    class Meta:
        model = InterviewStatusHistory
        fields = [
            "old_status",
            "new_status",
            "changed_by",
            "changed_at",
            "notes",
        ]
