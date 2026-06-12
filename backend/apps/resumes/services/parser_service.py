"""Service for parsing resume files."""

from django.utils import timezone

from apps.resumes.models import Resume, ParsedResume
from apps.resumes.parsers import ResumeParserFactory, CorruptedResumeError, UnsupportedResumeType


class ResumeParserService:
    """Service for parsing resume files and storing extracted text."""

    @staticmethod
    def parse_resume(resume: Resume) -> ParsedResume:
        """
        Parse a resume file and extract raw text.

        Args:
            resume: The Resume instance to parse

        Returns:
            The created or updated ParsedResume instance

        Raises:
            UnsupportedResumeType: If the resume MIME type is not supported
            CorruptedResumeError: If the resume file is corrupted
        """
        # Get the appropriate parser for the resume MIME type
        parser = ResumeParserFactory.get_parser(resume.mime_type)
        
        # Get the file path
        file_path = resume.file.path
        
        # Extract text from the file
        raw_text = parser.extract_text(file_path)
        
        # Get or create ParsedResume record
        parsed_resume, created = ParsedResume.objects.get_or_create(
            resume=resume,
            defaults={
                "raw_text": raw_text,
                "status": ParsedResume.ParseStatus.SUCCESS,
                "parsed_at": timezone.now(),
            }
        )
        
        # If updating an existing record
        if not created:
            parsed_resume.raw_text = raw_text
            parsed_resume.status = ParsedResume.ParseStatus.SUCCESS
            parsed_resume.parsed_at = timezone.now()
            parsed_resume.error_message = None
            parsed_resume.save()
        
        return parsed_resume

    @staticmethod
    def mark_as_failed(resume: Resume, error_message: str) -> ParsedResume:
        """
        Mark a resume parsing as failed.

        Args:
            resume: The Resume instance that failed to parse
            error_message: The error message describing the failure

        Returns:
            The created or updated ParsedResume instance with FAILED status
        """
        parsed_resume, created = ParsedResume.objects.get_or_create(
            resume=resume,
            defaults={
                "status": ParsedResume.ParseStatus.FAILED,
                "error_message": error_message,
                "parsed_at": timezone.now(),
            }
        )
        
        if not created:
            parsed_resume.status = ParsedResume.ParseStatus.FAILED
            parsed_resume.error_message = error_message
            parsed_resume.parsed_at = timezone.now()
            parsed_resume.save()
        
        return parsed_resume
