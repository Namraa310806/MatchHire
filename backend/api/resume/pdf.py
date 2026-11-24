"""PDF validation and text extraction for resumes.

Validation is strict and does not trust file extensions, MIME headers, or
client-supplied metadata. PyMuPDF (fitz) is used for structural validation
and text extraction. No OCR is performed in this phase.
"""

from dataclasses import dataclass

import pymupdf
from django.conf import settings

PDF_MAGIC = b"%PDF-"


class ResumeValidationError(Exception):
    """Permanent validation failure; the file can never be processed.

    Attributes:
        code: Stable machine-readable error category safe to expose.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class PdfDocument:
    """Result of successfully opening and scanning a resume PDF."""

    page_count: int
    text: str
    has_text_layer: bool


def validate_pdf_bytes(data: bytes) -> None:
    """Validate raw bytes as a readable, unencrypted PDF.

    Raises:
        ResumeValidationError: On any permanent validation failure.
    """
    if not data:
        raise ResumeValidationError("empty_file", "Uploaded file is empty.")

    max_bytes = settings.RESUME_MAX_UPLOAD_BYTES
    if len(data) > max_bytes:
        raise ResumeValidationError(
            "file_too_large", f"File exceeds the maximum allowed size of {max_bytes} bytes."
        )

    if not data.startswith(PDF_MAGIC):
        raise ResumeValidationError("invalid_pdf", "File is not a valid PDF document.")

    _open_and_check(data)


def extract_text(data: bytes) -> PdfDocument:
    """Extract text from validated PDF bytes.

    Raises:
        ResumeValidationError: If the document cannot be opened or is encrypted.
    """
    doc = _open_and_check(data)
    try:
        page_count = doc.page_count
        parts: list[str] = []
        for i in range(page_count):
            parts.append(doc.load_page(i).get_text("text"))
        text = "\n".join(parts)
    finally:
        doc.close()

    min_length = settings.RESUME_MIN_TEXT_LENGTH
    has_text_layer = len(text.strip()) >= min_length

    return PdfDocument(page_count=page_count, text=text, has_text_layer=has_text_layer)


def _open_and_check(data: bytes) -> pymupdf.Document:
    """Open PDF bytes with PyMuPDF and verify readability.

    Raises:
        ResumeValidationError: On corrupt or encrypted documents.
    """
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ResumeValidationError("corrupt_pdf", "PDF document is corrupt or unreadable.") from exc

    try:
        if doc.needs_pass or doc.is_encrypted:
            doc.close()
            raise ResumeValidationError(
                "encrypted_pdf", "Password-protected PDFs are not supported."
            )
        if doc.page_count == 0:
            doc.close()
            raise ResumeValidationError("empty_pdf", "PDF document has no pages.")
        # Force a light parse of the first page to surface structural errors
        _ = doc[0].get_text("text")
    except ResumeValidationError:
        raise
    except Exception as exc:
        doc.close()
        raise ResumeValidationError(
            "corrupt_pdf", "PDF document is corrupt or unreadable."
        ) from exc

    return doc
