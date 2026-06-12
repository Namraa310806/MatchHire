import os
from django.core.exceptions import ValidationError


# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# Maximum file size: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB in bytes


def validate_resume_file(file):
    """
    Validate a resume file before upload.
    
    Checks:
    1. File exists
    2. Size <= 10MB
    3. Extension allowed
    4. File signature matches extension (prevents extension spoofing)
    
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
    
    # Validate extension
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Invalid file extension '{ext}'. "
            f"Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}."
        )
    
    # Read file signature to verify actual file type
    # This prevents file extension spoofing (e.g., virus.exe renamed to resume.pdf)
    file.seek(0)
    header = file.read(8)
    file.seek(0)
    
    # PDF signature: %PDF
    if ext == ".pdf":
        if not header.startswith(b"%PDF"):
            raise ValidationError("Invalid PDF file. File signature does not match PDF format.")
    
    # DOCX signature: PK (ZIP archive)
    elif ext == ".docx":
        if not header.startswith(b"PK"):
            raise ValidationError("Invalid DOCX file. File signature does not match DOCX format.")
