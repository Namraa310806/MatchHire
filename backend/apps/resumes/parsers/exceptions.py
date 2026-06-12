"""Custom exceptions for resume parsing."""


class ResumeParsingError(Exception):
    """Base exception for resume parsing errors."""
    pass


class UnsupportedResumeType(ResumeParsingError):
    """Raised when the resume file type is not supported."""
    pass


class CorruptedResumeError(ResumeParsingError):
    """Raised when the resume file is corrupted or cannot be read."""
    pass
