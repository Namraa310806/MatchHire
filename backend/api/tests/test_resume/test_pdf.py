"""Unit tests for PDF validation, text extraction, and section segmentation."""

import pytest
from django.test import override_settings

from api.resume.pdf import (
    ResumeValidationError,
    extract_text,
    validate_pdf_bytes,
)
from api.resume.sections import segment_resume
from api.tests.test_resume.pdf_utils import (
    SAMPLE_RESUME,
    make_encrypted_pdf,
    make_pdf,
)


class TestValidatePdfBytes:
    def test_valid_pdf(self):
        validate_pdf_bytes(make_pdf(SAMPLE_RESUME))

    def test_empty_file(self):
        with pytest.raises(ResumeValidationError) as exc:
            validate_pdf_bytes(b"")
        assert exc.value.code == "empty_file"

    def test_oversized_file(self):
        with override_settings(RESUME_MAX_UPLOAD_BYTES=100):
            with pytest.raises(ResumeValidationError) as exc:
                validate_pdf_bytes(make_pdf(SAMPLE_RESUME))
            assert exc.value.code == "file_too_large"

    def test_wrong_magic_bytes(self):
        # Valid-looking content but not a PDF
        with pytest.raises(ResumeValidationError) as exc:
            validate_pdf_bytes(b"NOTAPDF" + b"\x00" * 100)
        assert exc.value.code == "invalid_pdf"

    def test_pdf_extension_lie(self):
        # Content-Type/extension are irrelevant: bytes decide
        with pytest.raises(ResumeValidationError):
            validate_pdf_bytes(b"%PDF-1.7 fake content not really a pdf")

    def test_corrupt_pdf(self):
        with pytest.raises(ResumeValidationError) as exc:
            validate_pdf_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n%%EOF\n")
        assert exc.value.code in {"corrupt_pdf", "empty_pdf"}

    def test_encrypted_pdf(self):
        with pytest.raises(ResumeValidationError) as exc:
            validate_pdf_bytes(make_encrypted_pdf())
        assert exc.value.code == "encrypted_pdf"


class TestExtractText:
    def test_text_extraction(self):
        doc = extract_text(make_pdf(SAMPLE_RESUME))
        assert doc.page_count == 1
        assert doc.has_text_layer is True
        assert "Python" in doc.text

    def test_multipage(self):
        doc = extract_text(make_pdf(per_page=["Page one text here", "Page two text here"]))
        assert doc.page_count == 2
        assert "Page one" in doc.text
        assert "Page two" in doc.text

    def test_scanned_no_text_layer(self):
        doc = extract_text(make_pdf(""))
        assert doc.has_text_layer is False

    def test_near_empty_document(self):
        with override_settings(RESUME_MIN_TEXT_LENGTH=50):
            doc = extract_text(make_pdf("Hi"))
            assert doc.has_text_layer is False


class TestSegmentResume:
    def test_standard_sections(self):
        sections = segment_resume(SAMPLE_RESUME)
        assert "summary" in sections.found
        assert "skills" in sections.found
        assert "experience" in sections.found
        assert "education" in sections.found
        assert "Python" in sections.get("skills")

    def test_missing_sections(self):
        text = "John Doe\nJust a name and nothing else really."
        sections = segment_resume(text)
        assert sections.found == []
        # Nothing is lost
        assert "John Doe" in sections.get("_preamble") or "John Doe" in sections.sections.get(
            "_body", ""
        )

    def test_unusual_headings_fall_back(self):
        text = "NAME: John\nWHAT I DID: things\nTOOLS: Python"
        sections = segment_resume(text)
        # Unknown headings are not force-mapped; text is preserved
        assert sections.found == []
        total = "\n".join(sections.sections.values())
        assert "WHAT I DID" in total

    def test_repeated_section_merges(self):
        text = "EXPERIENCE\nJob A 2020-2021\nEXPERIENCE\nJob B 2022-2023"
        sections = segment_resume(text)
        assert "Job A" in sections.get("experience")
        assert "Job B" in sections.get("experience")
