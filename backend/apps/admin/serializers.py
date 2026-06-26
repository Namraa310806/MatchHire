from rest_framework import serializers

from apps.admin.models import ModerationLog
from apps.applications.models import Application
from apps.jobs.models import Job
from apps.resumes.models import Resume
from apps.users.models import User


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin user management"""
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "role",
            "is_active",
            "is_staff",
            "is_verified",
            "date_joined",
            "updated_at",
        )
        read_only_fields = ("id", "is_staff", "is_verified", "date_joined", "updated_at")


class AdminUserUpdateSerializer(serializers.Serializer):
    """Serializer for admin user updates"""
    is_active = serializers.BooleanField(required=False)
    role = serializers.ChoiceField(choices=User.Roles.choices, required=False)
    reason = serializers.CharField(required=False, allow_blank=True)


class AdminJobSerializer(serializers.ModelSerializer):
    """Serializer for admin job management"""
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


class AdminJobUpdateSerializer(serializers.Serializer):
    """Serializer for admin job updates"""
    status = serializers.ChoiceField(choices=Job.JobStatus.choices, required=False)
    reason = serializers.CharField(required=False, allow_blank=True)


class AdminResumeSerializer(serializers.ModelSerializer):
    """Serializer for admin resume management"""
    candidate_id = serializers.UUIDField(source="user.id", read_only=True)
    candidate_email = serializers.EmailField(source="user.email", read_only=True)
    candidate_name = serializers.CharField(source="user.full_name", read_only=True)
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)

    class Meta:
        model = Resume
        fields = (
            "id",
            "candidate_id",
            "candidate_email",
            "candidate_name",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "candidate_id",
            "candidate_email",
            "candidate_name",
            "is_active",
            "created_at",
            "updated_at",
        )


class AdminResumeUpdateSerializer(serializers.Serializer):
    """Serializer for admin resume updates"""
    is_active = serializers.BooleanField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True)


class AdminApplicationSerializer(serializers.ModelSerializer):
    """Serializer for admin application management (read-only)"""
    job_id = serializers.UUIDField(source="job.id", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)
    job_company = serializers.CharField(source="job.company_name", read_only=True)
    recruiter_id = serializers.UUIDField(source="job.recruiter.id", read_only=True)
    recruiter_email = serializers.EmailField(source="job.recruiter.email", read_only=True)
    candidate_id = serializers.UUIDField(source="candidate.id", read_only=True)
    candidate_email = serializers.EmailField(source="candidate.email", read_only=True)
    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)

    class Meta:
        model = Application
        fields = (
            "id",
            "job_id",
            "job_title",
            "job_company",
            "recruiter_id",
            "recruiter_email",
            "candidate_id",
            "candidate_email",
            "candidate_name",
            "resume_version_id",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "job_id",
            "job_title",
            "job_company",
            "recruiter_id",
            "recruiter_email",
            "candidate_id",
            "candidate_email",
            "candidate_name",
            "resume_version_id",
            "status",
            "created_at",
            "updated_at",
        )


class ModerationLogSerializer(serializers.ModelSerializer):
    """Serializer for moderation logs"""
    admin_email = serializers.EmailField(source="admin.email", read_only=True)

    class Meta:
        model = ModerationLog
        fields = (
            "id",
            "admin_email",
            "action",
            "resource_type",
            "resource_id",
            "reason",
            "metadata",
            "created_at",
        )
        read_only_fields = (
            "id",
            "admin_email",
            "action",
            "resource_type",
            "resource_id",
            "reason",
            "metadata",
            "created_at",
        )


class AdminDashboardSerializer(serializers.Serializer):
    """Serializer for admin dashboard statistics"""
    total_users = serializers.IntegerField(read_only=True)
    total_candidates = serializers.IntegerField(read_only=True)
    total_recruiters = serializers.IntegerField(read_only=True)
    active_users = serializers.IntegerField(read_only=True)
    inactive_users = serializers.IntegerField(read_only=True)
    total_jobs = serializers.IntegerField(read_only=True)
    active_jobs = serializers.IntegerField(read_only=True)
    draft_jobs = serializers.IntegerField(read_only=True)
    closed_jobs = serializers.IntegerField(read_only=True)
    total_resumes = serializers.IntegerField(read_only=True)
    total_applications = serializers.IntegerField(read_only=True)
    total_interviews = serializers.IntegerField(read_only=True)
    total_notifications = serializers.IntegerField(read_only=True)
