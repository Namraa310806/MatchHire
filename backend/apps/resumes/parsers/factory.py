"""Factory for creating appropriate resume parsers based on MIME type."""

from .base import BaseResumeParser
from .pdf_parser import PDFResumeParser
from .docx_parser import DOCXResumeParser
from .exceptions import UnsupportedResumeType


class ResumeParserFactory:
    """Factory for creating resume parsers based on MIME type."""

    # MIME type to parser mapping
    PARSER_MAPPING = {
        "application/pdf": PDFResumeParser,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DOCXResumeParser,
    }

    @classmethod
    def get_parser(cls, mime_type: str) -> BaseResumeParser:
        """
        Get the appropriate parser for a given MIME type.

        Args:
            mime_type: The MIME type of the resume file

        Returns:
            An instance of the appropriate parser

        Raises:
            UnsupportedResumeType: If the MIME type is not supported
        """
        parser_class = cls.PARSER_MAPPING.get(mime_type)

        if parser_class is None:
            raise UnsupportedResumeType(
                f"Unsupported resume MIME type: {mime_type}. "
                f"Supported types: {', '.join(cls.PARSER_MAPPING.keys())}"
            )

        return parser_class()

    @classmethod
    def get_supported_mime_types(cls) -> list[str]:
        """
        Get list of supported MIME types.

        Returns:
            List of supported MIME types
        """
        return list(cls.PARSER_MAPPING.keys())
