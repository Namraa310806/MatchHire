from django.db import transaction
from django.db.models import Q

from ..models import Resume, ResumeVersion, ParsedResume


class ResumeVersioningService:
    """Service for managing resume versioning and history."""

    @staticmethod
    @transaction.atomic
    def create_version(
        resume: Resume,
        file,
        original_filename: str,
        stored_filename: str,
        file_size: int,
        mime_type: str,
        change_reason: str = None
    ) -> ResumeVersion:
        """
        Create a new version for a resume.

        Automatically increments version number and sets as current.
        Deactivates previous current version.

        Args:
            resume: The Resume instance to version
            file: The uploaded file object
            original_filename: The original filename from the upload
            stored_filename: The unique stored filename
            file_size: The size of the file in bytes
            mime_type: The MIME type of the file
            change_reason: Optional reason for the version change

        Returns:
            The newly created ResumeVersion instance
        """
        # Get the highest version number for this resume
        last_version = ResumeVersion.objects.filter(resume=resume).order_by('-version_number').first()
        next_version_number = (last_version.version_number + 1) if last_version else 1

        # Deactivate all current versions for this resume
        ResumeVersion.objects.filter(resume=resume, is_current=True).update(is_current=False)

        # Create new version with all required fields
        version = ResumeVersion.objects.create(
            resume=resume,
            file=file,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_size=file_size,
            mime_type=mime_type,
            version_number=next_version_number,
            is_current=True,
            change_reason=change_reason,
        )

        return version

    @staticmethod
    def get_current_version(resume: Resume) -> ResumeVersion:
        """
        Get the current version of a resume.
        
        Args:
            resume: The Resume instance
            
        Returns:
            The current ResumeVersion instance
            
        Raises:
            ResumeVersion.DoesNotExist: If no current version exists
        """
        return ResumeVersion.objects.get(resume=resume, is_current=True)

    @staticmethod
    @transaction.atomic
    def rollback_version(resume: Resume, version_id: str) -> ResumeVersion:
        """
        Rollback to a specific version of a resume.
        
        Deactivates the current version and activates the specified version.
        
        Args:
            resume: The Resume instance
            version_id: The UUID of the version to rollback to
            
        Returns:
            The activated ResumeVersion instance
            
        Raises:
            ResumeVersion.DoesNotExist: If the version doesn't exist or doesn't belong to this resume
        """
        # Get the version to rollback to
        target_version = ResumeVersion.objects.get(id=version_id, resume=resume)
        
        # Deactivate all current versions for this resume
        ResumeVersion.objects.filter(resume=resume, is_current=True).update(is_current=False)
        
        # Activate the target version
        target_version.is_current = True
        target_version.save()
        
        return target_version

    @staticmethod
    def get_version_history(resume: Resume) -> list[ResumeVersion]:
        """
        Get all versions for a resume, ordered newest first.
        
        Args:
            resume: The Resume instance
            
        Returns:
            QuerySet of ResumeVersion instances ordered by version_number descending
        """
        return ResumeVersion.objects.filter(resume=resume).order_by('-version_number')

    @staticmethod
    def link_parsed_resume(version: ResumeVersion, parsed_resume: ParsedResume) -> None:
        """
        Link a ParsedResume to a ResumeVersion.
        
        Args:
            version: The ResumeVersion instance
            parsed_resume: The ParsedResume instance to link
        """
        version.parsed_resume = parsed_resume
        version.save()
