from rest_framework import serializers

from .models import Application


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
