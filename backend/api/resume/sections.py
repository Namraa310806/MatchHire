"""Conservative resume section segmentation.

Resumes do not share a standard format, so segmentation is deliberately
conservative: only well-known section headings are recognized, unmatched
text is preserved under ``_preamble``/``_body``, and segmentation never
blocks extraction from the full text.
"""

import re
from dataclasses import dataclass, field

SECTION_HEADINGS: dict[str, tuple[str, ...]] = {
    "summary": ("summary", "profile", "objective", "about me", "about"),
    "skills": (
        "skills",
        "technical skills",
        "skill set",
        "core competencies",
        "competencies",
        "technologies",
    ),
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "employment history",
        "work history",
    ),
    "education": (
        "education",
        "academic background",
        "academic qualifications",
        "qualifications",
    ),
    "projects": ("projects", "project experience", "key projects"),
    "certifications": (
        "certifications",
        "certificates",
        "licenses",
        "achievements",
        "awards",
    ),
}

# A heading line is short, may carry markdown/bold markers or a trailing
# colon, and must match a known heading exactly after normalization.
_HEADING_RE = re.compile(r"^\s*[#*_\-•\s]*([A-Za-z][A-Za-z /&+\-]{1,40}?)\s*[:\-–—]?\s*[#*_]*\s*$")


@dataclass
class ResumeSections:
    """Detected resume sections mapped to their text content."""

    sections: dict[str, str] = field(default_factory=dict)

    @property
    def found(self) -> list[str]:
        """Canonical section names that were detected, sorted."""
        return sorted(k for k in self.sections if not k.startswith("_"))

    def get(self, name: str) -> str:
        """Return section text or empty string."""
        return self.sections.get(name, "")


def _normalize_heading(line: str) -> str | None:
    """Return the canonical section name for a heading line, or None."""
    match = _HEADING_RE.match(line.strip())
    if not match:
        return None
    candidate = match.group(1).strip().lower().rstrip(":")
    for canonical, aliases in SECTION_HEADINGS.items():
        if candidate in aliases or candidate == canonical:
            return canonical
    return None


def segment_resume(text: str) -> ResumeSections:
    """Segment resume text into canonical sections.

    Lines before the first recognized heading are kept under ``_preamble``;
    content after the last recognized heading boundary that matches no
    further heading remains inside the current section. Text belonging to
    no heading is never discarded.
    """
    result = ResumeSections()
    current: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        content = "\n".join(buffer).strip()
        if content:
            target = current if current is not None else "_preamble"
            existing = result.sections.get(target, "")
            result.sections[target] = (
                f"{existing}\n{content}".strip() if existing else content
            )
        buffer = []

    for raw_line in text.splitlines():
        heading = _normalize_heading(raw_line)
        if heading is not None:
            flush()
            current = heading
        else:
            buffer.append(raw_line)

    flush()

    return result
