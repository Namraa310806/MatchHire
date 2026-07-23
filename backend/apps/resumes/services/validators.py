import os
import mimetypes
from django.core.exceptions import ValidationError


# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}

# Dangerous extensions to reject
DANGEROUS_EXTENSIONS = {".exe", ".js", ".dll", ".bat", ".zip", ".sh", ".cmd", ".msi"}

# Maximum file size: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB in bytes


def validate_resume_file(file):
    """
    Validate a resume file before upload.

    Checks:
    1. File exists
    2. Size <= 10MB
    3. Extension not dangerous
    4. Extension allowed
    5. MIME type allowed
    6. File signature matches extension (prevents extension spoofing)

    Raises ValidationError on failure.
    """
    # Check if file exists
    if not file or not hasattr(file, "name"):
        raise ValidationError("No file provided.")

    # Check file size
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(
            f"File size exceeds maximum limit of 10 MB. "
            f"Your file is {file.size / (1024 * 1024):.2f} MB."
        )

    # Get file extension
    _, ext = os.path.splitext(file.name.lower())

    # Reject dangerous extensions
    if ext in DANGEROUS_EXTENSIONS:
        raise ValidationError(f"Dangerous file extension '{ext}' is not allowed.")

    # Validate extension
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Invalid file extension '{ext}'. "
            f"Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}."
        )

    # Validate MIME type
    mime_type, _ = mimetypes.guess_type(file.name)
    if mime_type and mime_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"Invalid MIME type '{mime_type}'. "
            f"Allowed types: {', '.join(ALLOWED_MIME_TYPES)}."
        )

    # Read file signature to verify actual file type
    # This prevents file extension spoofing (e.g., virus.exe renamed to resume.pdf)
    file.seek(0)
    header = file.read(8)
    file.seek(0)

    # PDF signature: %PDF
    if ext == ".pdf":
        if not header.startswith(b"%PDF"):
            raise ValidationError(
                "Invalid PDF file. File signature does not match PDF format."
            )

    # DOCX signature: PK (ZIP archive)
    elif ext == ".docx":
        if not header.startswith(b"PK"):
            raise ValidationError(
                "Invalid DOCX file. File signature does not match DOCX format."
            )

    # TXT files should be plain text
    elif ext == ".txt":
        # Try to decode as UTF-8 to verify it's text
        file.seek(0)
        try:
            file.read(1024).decode("utf-8")
            file.seek(0)
        except UnicodeDecodeError:
            raise ValidationError(
                "Invalid text file. File does not appear to be plain text."
            )
