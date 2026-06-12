"""DOCX resume parser using python-docx."""

from pathlib import Path

import docx

from .base import BaseResumeParser
from .exceptions import CorruptedResumeError
from .utils import normalize_resume_text


class DOCXResumeParser(BaseResumeParser):
    """Parser for DOCX resume files."""

    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a DOCX file.

        Args:
            file_path: Path to the DOCX file

        Returns:
            Normalized text extracted from the DOCX

        Raises:
            CorruptedResumeError: If the DOCX is corrupted or cannot be read
        """
        path = Path(file_path)
        
        if not path.exists():
            raise CorruptedResumeError(f"DOCX file not found: {file_path}")
        
        try:
            doc = docx.Document(path)
            
            # Extract text from paragraphs
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            if not text_parts:
                raise CorruptedResumeError("No text could be extracted from DOCX")
            
            raw_text = "\n".join(text_parts)
            
            # Normalize the text
            return normalize_resume_text(raw_text)
            
        except docx.opc.exceptions.PackageNotFoundError as e:
            raise CorruptedResumeError(f"Corrupted DOCX file: {str(e)}")
        except Exception as e:
            raise CorruptedResumeError(f"Error reading DOCX file: {str(e)}")
