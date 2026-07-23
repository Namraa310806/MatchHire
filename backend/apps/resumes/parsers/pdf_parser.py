"""PDF resume parser using PyPDF2."""

from pathlib import Path

import PyPDF2

from .base import BaseResumeParser
from .exceptions import CorruptedResumeError
from .utils import normalize_resume_text


class PDFResumeParser(BaseResumeParser):
    """Parser for PDF resume files."""

    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Normalized text extracted from the PDF

        Raises:
            CorruptedResumeError: If the PDF is corrupted or cannot be read
        """
        path = Path(file_path)

        if not path.exists():
            raise CorruptedResumeError(f"PDF file not found: {file_path}")

        try:
            with open(path, "rb") as file:
                reader = PyPDF2.PdfReader(file)

                # Check if PDF is empty
                if len(reader.pages) == 0:
                    raise CorruptedResumeError("PDF file is empty (no pages)")

                text_parts = []
                for page in reader.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    except Exception:
                        # Continue with other pages if one fails
                        continue

                if not text_parts:
                    raise CorruptedResumeError("No text could be extracted from PDF")

                raw_text = "\n".join(text_parts)

                # Normalize the text
                return normalize_resume_text(raw_text)

        except PyPDF2.PdfReadError as e:
            raise CorruptedResumeError(f"Corrupted PDF file: {str(e)}")
        except Exception as e:
            raise CorruptedResumeError(f"Error reading PDF file: {str(e)}")
