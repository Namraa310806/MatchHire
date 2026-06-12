import mimetypes
from rest_framework import serializers

from .models import Resume
from .services.storage import ResumeStorageService
from .services.validators import validate_resume_file


class ResumeUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        """Validate the uploaded file using the validator service"""
        validate_resume_file(value)
        return value

    def create(self, validated_data):
        """Create a new resume with the uploaded file"""
        file = validated_data["file"]
        user = self.context["request"].user
        
        # Generate unique filename
        stored_filename = ResumeStorageService.generate_unique_filename(file.name)
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(file.name)
        
        # Deactivate existing active resumes for this user
        Resume.objects.filter(user=user, is_active=True).update(is_active=False)
        
        # Create resume record - Django's FileField will handle file saving
        resume = Resume.objects.create(
            user=user,
            original_filename=file.name,
            stored_filename=stored_filename,
            file=file,  # Django's FileField will save this
            file_size=file.size,
            mime_type=mime_type,
            is_active=True,  # New resume becomes active
        )
        
        return resume


class ResumeSerializer(serializers.ModelSerializer):
    """Serializer for resume display"""
    filename = serializers.CharField(source="original_filename", read_only=True)
    
    class Meta:
        model = Resume
        fields = (
            "id",
            "filename",
            "file_size",
            "uploaded_at",
            "is_active",
        )
        read_only_fields = ("id", "filename", "file_size", "uploaded_at", "is_active")
