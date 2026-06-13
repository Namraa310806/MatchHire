import mimetypes
from django.db import transaction
from rest_framework import serializers

from .models import Resume, ParsedResume, ResumeVersion
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
        """Get the current version data"""
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
        """Get the current version data"""
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
        read_only_fields = ("id", "created_at", "updated_at", "current_version")

    def get_current_version(self, obj):
        """Get the current version data"""
        try:
            current_version = obj.versions.get(is_current=True)
            return ResumeVersionSerializer(current_version).data
        except ResumeVersion.DoesNotExist:
            return None


class ParsedResumeSerializer(serializers.ModelSerializer):
    """Serializer for parsed resume data (without full raw text)"""
    resume_version_id = serializers.UUIDField(source="resume_version.id", read_only=True)
    resume_id = serializers.UUIDField(source="resume_version.resume.id", read_only=True)
    version_number = serializers.IntegerField(source="resume_version.version_number", read_only=True)
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
        read_only_fields = ("resume_version_id", "resume_id", "version_number", "status", "text_length", "parsed_at")

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
    parsed_resume_id = serializers.UUIDField(source="parsed_resume.id", read_only=True, allow_null=True)
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
