import mimetypes
from rest_framework import serializers

from .models import (
    Resume,
    ParsedResume,
    ResumeVersion,
    StructuredResume,
    ResumeSkill,
    ResumeEducation,
    ResumeExperience,
    ResumeProject,
    ResumeCertification,
)
from .services.storage import ResumeStorageService
from .services.validators import validate_resume_file
from .services.versioning import ResumeVersioningService


class ResumeUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        """Validate the uploaded file using the validator service"""
        validate_resume_file(value)
        return value

    def create(self, validated_data):
        """Create a new resume version with the uploaded file"""
        file = validated_data["file"]
        user = self.context["request"].user

        # Get or create Resume container for the user
        resume, created = Resume.objects.get_or_create(user=user)

        # Generate unique filename
        stored_filename = ResumeStorageService.generate_unique_filename(file.name)

        # Get MIME type
        mime_type, _ = mimetypes.guess_type(file.name)

        # Create version using the versioning service (single source of truth)
        change_reason = "Initial upload" if created else "Updated resume"
        resume_version = ResumeVersioningService.create_version(
            resume=resume,
            file=file,
            original_filename=file.name,
            stored_filename=stored_filename,
            file_size=file.size,
            mime_type=mime_type,
            change_reason=change_reason,
        )

        return resume_version


class ResumeListSerializer(serializers.ModelSerializer):
    """Serializer for listing resumes (shows current version data)"""

    current_version = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = (
            "id",
            "created_at",
            "updated_at",
            "current_version",
        )
        read_only_fields = ("id", "created_at", "updated_at", "current_version")

    def get_current_version(self, obj):
        """
        Get the current version data.

        PERFORMANCE OPTIMIZATION: Use prefetched data if available to avoid N+1 queries.
        The view should prefetch current versions with Prefetch object.
        """
        # Check if data was prefetched by the view
        if hasattr(obj, "current_version_prefetch") and obj.current_version_prefetch:
            current_version = obj.current_version_prefetch[0]
            return ResumeVersionSerializer(current_version).data

        # Fallback to query (should not happen with proper optimization)
        try:
            current_version = obj.versions.get(is_current=True)
            return ResumeVersionSerializer(current_version).data
        except ResumeVersion.DoesNotExist:
            return None


class ResumeDetailSerializer(serializers.ModelSerializer):
    """Serializer for resume detail view (shows current version data)"""

    current_version = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = (
            "id",
            "created_at",
            "updated_at",
            "current_version",
        )
        read_only_fields = ("id", "created_at", "updated_at", "current_version")

    def get_current_version(self, obj):
        """
        Get the current version data.

        PERFORMANCE OPTIMIZATION: Use prefetched data if available to avoid N+1 queries.
        The view should prefetch current versions with Prefetch object.
        """
        # Check if data was prefetched by the view
        if hasattr(obj, "current_version_prefetch") and obj.current_version_prefetch:
            current_version = obj.current_version_prefetch[0]
            return ResumeVersionSerializer(current_version).data

        # Fallback to query (should not happen with proper optimization)
        try:
            current_version = obj.versions.get(is_current=True)
            return ResumeVersionSerializer(current_version).data
        except ResumeVersion.DoesNotExist:
            return None


class ResumeActivationSerializer(serializers.ModelSerializer):
    """Serializer for resume activation response (shows current version data)"""

    current_version = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = (
            "id",
            "created_at",
            "updated_at",
            "current_version",
        )

    def get_current_version(self, obj: Resume) -> dict:
        """
        Get the current version data.

        PERFORMANCE OPTIMIZATION: Use prefetched data if available to avoid N+1 queries.
        The view should prefetch current versions with Prefetch object.
        """
        # Check if data was prefetched by the view
        if hasattr(obj, "current_version_prefetch") and obj.current_version_prefetch:
            current_version = obj.current_version_prefetch[0]
            return ResumeVersionSerializer(current_version).data

        # Fallback to query (should not happen with proper optimization)
        try:
            current_version = obj.versions.get(is_current=True)
            return ResumeVersionSerializer(current_version).data
        except ResumeVersion.DoesNotExist:
            return None


class ParsedResumeSerializer(serializers.ModelSerializer):
    """Serializer for parsed resume data (without full raw text)"""

    resume_version_id = serializers.UUIDField(
        source="resume_version.id", read_only=True
    )
    resume_id = serializers.UUIDField(source="resume_version.resume.id", read_only=True)
    version_number = serializers.IntegerField(
        source="resume_version.version_number", read_only=True
    )
    text_length = serializers.SerializerMethodField()

    class Meta:
        model = ParsedResume
        fields = (
            "resume_version_id",
            "resume_id",
            "version_number",
            "status",
            "text_length",
            "parsed_at",
        )
        read_only_fields = (
            "resume_version_id",
            "resume_id",
            "version_number",
            "status",
            "text_length",
            "parsed_at",
        )

    def get_text_length(self, obj):
        """Get the length of the raw text"""
        return len(obj.raw_text) if obj.raw_text else 0


class ParseResumeResponseSerializer(serializers.Serializer):
    """Serializer for parse resume endpoint response"""

    resume_version_id = serializers.UUIDField()
    resume_id = serializers.UUIDField()
    status = serializers.CharField()
    text_length = serializers.IntegerField()


class ResumeVersionSerializer(serializers.ModelSerializer):
    """Serializer for resume version data"""

    resume_id = serializers.UUIDField(source="resume.id", read_only=True)
    parsed_resume_id = serializers.UUIDField(
        source="parsed_resume.id", read_only=True, allow_null=True
    )
    filename = serializers.CharField(source="original_filename", read_only=True)

    class Meta:
        model = ResumeVersion
        fields = (
            "id",
            "resume_id",
            "version_number",
            "created_at",
            "is_current",
            "change_reason",
            "parsed_resume_id",
            "filename",
            "file_size",
            "mime_type",
            "uploaded_at",
        )
        read_only_fields = (
            "id",
            "resume_id",
            "version_number",
            "created_at",
            "is_current",
            "parsed_resume_id",
            "filename",
            "file_size",
            "mime_type",
            "uploaded_at",
        )


class RollbackResponseSerializer(serializers.Serializer):
    """Serializer for rollback endpoint response"""

    resume_id = serializers.UUIDField()
    current_version = serializers.IntegerField()


class ResumeSkillSerializer(serializers.ModelSerializer):
    """Serializer for resume skill"""

    class Meta:
        model = ResumeSkill
        fields = (
            "id",
            "name",
        )
        read_only_fields = ("id",)


class ResumeEducationSerializer(serializers.ModelSerializer):
    """Serializer for resume education"""

    class Meta:
        model = ResumeEducation
        fields = (
            "id",
            "institution",
            "degree",
            "field_of_study",
            "start_year",
            "end_year",
            "description",
        )
        read_only_fields = ("id",)


class ResumeExperienceSerializer(serializers.ModelSerializer):
    """Serializer for resume experience"""

    class Meta:
        model = ResumeExperience
        fields = (
            "id",
            "company",
            "job_title",
            "start_date",
            "end_date",
            "description",
        )
        read_only_fields = ("id",)


class ResumeProjectSerializer(serializers.ModelSerializer):
    """Serializer for resume project"""

    class Meta:
        model = ResumeProject
        fields = (
            "id",
            "title",
            "description",
            "github_url",
            "project_url",
        )
        read_only_fields = ("id",)


class ResumeCertificationSerializer(serializers.ModelSerializer):
    """Serializer for resume certification"""

    class Meta:
        model = ResumeCertification
        fields = (
            "id",
            "name",
            "issuer",
            "issue_date",
        )
        read_only_fields = ("id",)


class StructuredResumeSerializer(serializers.ModelSerializer):
    """Serializer for structured resume"""

    resume_version_id = serializers.UUIDField(
        source="resume_version.id", read_only=True
    )
    resume_id = serializers.UUIDField(source="resume_version.resume.id", read_only=True)
    version_number = serializers.IntegerField(
        source="resume_version.version_number", read_only=True
    )
    skills = ResumeSkillSerializer(many=True, read_only=True)
    education = ResumeEducationSerializer(many=True, read_only=True)
    experience = ResumeExperienceSerializer(many=True, read_only=True)
    projects = ResumeProjectSerializer(many=True, read_only=True)
    certifications = ResumeCertificationSerializer(many=True, read_only=True)

    class Meta:
        model = StructuredResume
        fields = (
            "id",
            "resume_version_id",
            "resume_id",
            "version_number",
            "full_name",
            "email",
            "phone",
            "location",
            "summary",
            "linkedin_url",
            "github_url",
            "portfolio_url",
            "skills",
            "education",
            "experience",
            "projects",
            "certifications",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "resume_version_id",
            "resume_id",
            "version_number",
            "created_at",
            "updated_at",
        )


class ExtractResumeResponseSerializer(serializers.Serializer):
    """Serializer for extract resume endpoint response"""

    structured_resume_id = serializers.UUIDField()
    resume_version_id = serializers.UUIDField()
    resume_id = serializers.UUIDField()
    status = serializers.CharField()


class ResumeSearchResultSerializer(serializers.Serializer):
    """Serializer for resume search results"""

    resume_id = serializers.UUIDField(source="resume_version.resume.id", read_only=True)
    resume_version_id = serializers.UUIDField(
        source="resume_version.id", read_only=True
    )
    candidate_name = serializers.CharField(source="full_name", read_only=True)
    location = serializers.CharField(read_only=True)
    skills = serializers.SerializerMethodField()
    experience_count = serializers.SerializerMethodField()
    education_count = serializers.SerializerMethodField()
    project_count = serializers.SerializerMethodField()
    certification_count = serializers.SerializerMethodField()

    def get_skills(self, obj):
        """
        Get list of skill names.

        PERFORMANCE NOTE: This method requires prefetch_related('skills') on the queryset
        to avoid N+1 queries. The ResumeSearchService already includes this optimization.
        """
        return [skill.name for skill in obj.skills.all()]

    def get_experience_count(self, obj):
        """
        Get count of experience entries.

        PERFORMANCE NOTE: This method requires prefetch_related('experience') on the queryset
        to avoid N+1 queries. The ResumeSearchService already includes this optimization.
        """
        return obj.experience.count()

    def get_education_count(self, obj):
        """
        Get count of education entries.

        PERFORMANCE NOTE: This method requires prefetch_related('education') on the queryset
        to avoid N+1 queries. The ResumeSearchService already includes this optimization.
        """
        return obj.education.count()

    def get_project_count(self, obj):
        """
        Get count of project entries.

        PERFORMANCE NOTE: This method requires prefetch_related('projects') on the queryset
        to avoid N+1 queries. The ResumeSearchService already includes this optimization.
        """
        return obj.projects.count()

    def get_certification_count(self, obj):
        """
        Get count of certification entries.

        PERFORMANCE NOTE: This method requires prefetch_related('certifications') on the queryset
        to avoid N+1 queries. The ResumeSearchService already includes this optimization.
        """
        return obj.certifications.count()


class CandidateProfileSerializer(serializers.ModelSerializer):
    """Serializer for candidate profile with current resume data"""

    candidate_id = serializers.UUIDField(source="user.id", read_only=True)
    candidate_email = serializers.EmailField(source="user.email", read_only=True)
    candidate_name = serializers.CharField(source="user.full_name", read_only=True)
    structured_resume = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = (
            "id",
            "candidate_id",
            "candidate_email",
            "candidate_name",
            "structured_resume",
        )

    def get_structured_resume(self, obj):
        """Get the current version's structured resume"""
        try:
            current_version = obj.versions.get(is_current=True)
            try:
                structured_resume = current_version.structured_resume
                return StructuredResumeSerializer(structured_resume).data
            except StructuredResume.DoesNotExist:
                return None
        except ResumeVersion.DoesNotExist:
            return None
