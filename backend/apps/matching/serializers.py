from rest_framework import serializers

from .models import JobMatch


class JobMatchSerializer(serializers.ModelSerializer):
    """Serializer for job match details"""
    job_id = serializers.UUIDField(source="job.id", read_only=True)
    candidate_id = serializers.UUIDField(source="candidate.id", read_only=True)

    class Meta:
        model = JobMatch
        fields = (
            "id",
            "job_id",
            "candidate_id",
            "match_score",
            "skills_score",
            "experience_score",
            "education_score",
            "matched_skills_count",
            "total_required_skills",
            "explanation",
            "calculated_at",
        )
        read_only_fields = (
            "id",
            "job_id",
            "candidate_id",
            "match_score",
            "skills_score",
            "experience_score",
            "education_score",
            "matched_skills_count",
            "total_required_skills",
            "explanation",
            "calculated_at",
        )


class JobRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for job recommendations for candidates"""
    job_id = serializers.UUIDField(source="job.id", read_only=True)
    title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company_name", read_only=True)
    location = serializers.CharField(source="job.location", read_only=True)
    employment_type = serializers.CharField(source="job.employment_type", read_only=True)
    experience_level = serializers.CharField(source="job.experience_level", read_only=True)

    class Meta:
        model = JobMatch
        fields = (
            "job_id",
            "title",
            "company_name",
            "location",
            "employment_type",
            "experience_level",
            "match_score",
        )
        read_only_fields = (
            "job_id",
            "title",
            "company_name",
            "location",
            "employment_type",
            "experience_level",
            "match_score",
        )


class CandidateMatchSerializer(serializers.ModelSerializer):
    """Serializer for candidate matches for recruiters with explanation"""
    candidate_id = serializers.UUIDField(source="candidate.id", read_only=True)
    candidate_email = serializers.EmailField(source="candidate.email", read_only=True)
    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)

    class Meta:
        model = JobMatch
        fields = (
            "candidate_id",
            "candidate_email",
            "candidate_name",
            "match_score",
            "skills_score",
            "experience_score",
            "education_score",
            "explanation",
        )
        read_only_fields = (
            "candidate_id",
            "candidate_email",
            "candidate_name",
            "match_score",
            "skills_score",
            "experience_score",
            "education_score",
            "explanation",
        )
