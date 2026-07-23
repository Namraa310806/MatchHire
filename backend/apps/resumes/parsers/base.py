"""Base parser for resume text extraction."""

from abc import ABC, abstractmethod


class BaseResumeParser(ABC):
    """Abstract base class for resume parsers."""

    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """
        Extract raw text from a resume file.

        Args:
            file_path: Path to the resume file

        Returns:
            Raw text extracted from the resume

        Raises:
            CorruptedResumeError: If the file is corrupted or cannot be read
        """
        pass
