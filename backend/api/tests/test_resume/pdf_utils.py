"""Helpers for building synthetic PDF bytes in tests."""

from typing import cast

import pymupdf


def make_pdf(text: str = "", pages: int = 1, per_page: str | None = None) -> bytes:
    """Create a simple single/multi-page text PDF.

    Args:
        text: Text to place on every page (ignored if per_page given).
        pages: Number of pages.
        per_page: Optional list of per-page texts (overrides text/pages count
            is derived from its length when provided).
    """
    doc = pymupdf.open()
    contents = per_page if per_page is not None else [text] * pages
    for content in contents:
        page = doc.new_page()
        if content.strip():
            page.insert_textbox(
                pymupdf.Rect(50, 50, 550, 800), content, fontsize=10
            )
    data = cast(bytes, doc.tobytes())
    doc.close()
    return data


def make_encrypted_pdf(text: str = "Secret resume") -> bytes:
    """Create a password-protected PDF."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=12)
    data = cast(
        bytes,
        doc.tobytes(
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            owner_pw="ownerpass",
            user_pw="userpass",
        ),
    )
    doc.close()
    return data


SAMPLE_RESUME = """John Doe
Software Engineer

SUMMARY
Fresher software engineer with 2 years of experience in Python and Django,
with interests in fintech and machine learning applications.

SKILLS
Python, Django, JavaScript, SQL, Git, REST API

EXPERIENCE
Software Developer Intern at TechCorp
Jan 2023 - Dec 2023
Built REST APIs with Django and PostgreSQL.

EDUCATION
B.Tech Computer Science, State University, 2022
"""
