from rest_framework import serializers


class RecruiterDashboardSerializer(serializers.Serializer):
    """Serializer for recruiter dashboard analytics"""
    total_jobs = serializers.IntegerField()
    active_jobs = serializers.IntegerField()
    closed_jobs = serializers.IntegerField()
    total_applications = serializers.IntegerField()
    submitted_applications = serializers.IntegerField()
    under_review_applications = serializers.IntegerField()
    shortlisted_applications = serializers.IntegerField()
    rejected_applications = serializers.IntegerField()
    hired_applications = serializers.IntegerField()
    scheduled_interviews = serializers.IntegerField()
    completed_interviews = serializers.IntegerField()
    cancelled_interviews = serializers.IntegerField()


class CandidateDashboardSerializer(serializers.Serializer):
    """Serializer for candidate dashboard analytics"""
    total_applications = serializers.IntegerField()
    submitted = serializers.IntegerField()
    under_review = serializers.IntegerField()
    shortlisted = serializers.IntegerField()
    rejected = serializers.IntegerField()
    hired = serializers.IntegerField()
    scheduled_interviews = serializers.IntegerField()
    completed_interviews = serializers.IntegerField()
    cancelled_interviews = serializers.IntegerField()
    total_matches = serializers.IntegerField()
    average_match_score = serializers.FloatField()


class JobAnalyticsSerializer(serializers.Serializer):
    """Serializer for job analytics"""
    job_id = serializers.UUIDField()
    total_applications = serializers.IntegerField()
    submitted = serializers.IntegerField()
    under_review = serializers.IntegerField()
    shortlisted = serializers.IntegerField()
    rejected = serializers.IntegerField()
    hired = serializers.IntegerField()
    conversion_rate = serializers.FloatField()


class TopCandidateSerializer(serializers.Serializer):
    """Serializer for top matched candidates"""
    candidate_id = serializers.UUIDField()
    candidate_name = serializers.CharField()
    match_score = serializers.FloatField()
    matched_skills_count = serializers.IntegerField()
    total_required_skills = serializers.IntegerField()
