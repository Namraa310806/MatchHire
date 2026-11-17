"""Years of experience estimation from resume text.

This module provides conservative experience estimation from resume text,
following the rules specified in docs/SPEC.md for internship weighting
and overlap handling.
"""

import re
from dataclasses import dataclass
from datetime import date
from typing import Final

# Internship weighting per SPEC.md
# Internships count as 0.5 years (6 months) of experience
INTERNSHIP_WEIGHTING: Final[float] = 0.5

# Minimum threshold for a role to count as experience (in months)
# Roles shorter than this are ignored
MIN_ROLE_DURATION_MONTHS: Final[int] = 1


@dataclass
class ExperienceEstimate:
    """Represents an estimated years of experience with confidence."""

    total_years: float | None
    confidence: str  # "high", "medium", "low", "none"
    methodology: str  # Description of how the estimate was derived


def estimate_experience_years(text: str) -> ExperienceEstimate:
    """Estimate total years of experience from resume text.

    This function follows conservative estimation rules:
    - Recognizes explicit experience durations (e.g., "3 years experience")
    - Recognizes employment periods where reasonably parseable
    - Accounts for internships as fractional experience (0.5 years per internship)
    - Avoids double-counting overlapping employment periods
    - Returns null when experience cannot be reliably determined
    - Does not infer experience from graduation year alone
    - Distinguishes total professional experience from academic/project experience

    Rules from SPEC.md:
    - Internships count as 0.5 years (6 months) of experience
    - Overlapping periods are merged to avoid double-counting
    - Roles shorter than 1 month are ignored
    - Explicit "X years" statements are given highest confidence
    - Date ranges are given medium confidence
    - Ambiguous or missing information returns null with "none" confidence

    Args:
        text: The resume text to analyze

    Returns:
        ExperienceEstimate with total years, confidence level, and methodology
    """
    if not text or not text.strip():
        return ExperienceEstimate(
            total_years=None, confidence="none", methodology="Empty input"
        )

    text_lower = text.lower()

    # Priority 1: Look for explicit total experience statements
    explicit_match = _extract_explicit_total_experience(text_lower)
    if explicit_match is not None:
        return ExperienceEstimate(
            total_years=explicit_match,
            confidence="high",
            methodology="Explicit total experience statement",
        )

    # Priority 2: Extract individual employment periods and sum them
    employment_periods = _extract_employment_periods(text_lower)
    if employment_periods:
        total_experience = _sum_employment_periods(employment_periods)
        if total_experience > 0:
            return ExperienceEstimate(
                total_years=total_experience,
                confidence="medium",
                methodology=f"Summed {len(employment_periods)} employment periods",
            )

    # Priority 3: Count internships (fallback)
    internship_count = _count_internships(text_lower)
    if internship_count > 0:
        total_experience = internship_count * INTERNSHIP_WEIGHTING
        return ExperienceEstimate(
            total_years=total_experience,
            confidence="low",
            methodology=f"Counted {internship_count} internship(s) at {INTERNSHIP_WEIGHTING} years each",
        )

    # No reliable experience information found
    return ExperienceEstimate(
        total_years=None, confidence="none", methodology="No reliable experience information found"
    )


def _extract_explicit_total_experience(text: str) -> float | None:
    """Extract explicit total experience statements (e.g., "5 years experience").

    Args:
        text: Lowercase text to search

    Returns:
        Total years as float, or None if not found
    """
    # Pattern: "X years of experience" or "X years experience"
    match = re.search(r"(\d+(?:\.\d+)?)\s*years?\s*(?:of\s*)?experience", text)
    if match:
        return float(match.group(1))

    # Pattern: "X+ years experience"
    match = re.search(r"(\d+)\+\s*years?\s*(?:of\s*)?experience", text)
    if match:
        return float(match.group(1))

    # Pattern: "over X years" or "more than X years"
    match = re.search(r"(?:over|more than|at least)\s+(\d+(?:\.\d+)?)\s*years?", text)
    if match:
        return float(match.group(1))

    return None


def _extract_employment_periods(text: str) -> list[tuple[date, date, bool]]:
    """Extract employment periods from text, excluding education periods.

    Returns list of (start_date, end_date, is_internship) tuples.
    Dates may be None if not parseable.

    Args:
        text: Lowercase text to search

    Returns:
        List of employment period tuples (excludes education periods)
    """
    periods: list[tuple[date, date, bool]] = []

    # Pattern: Month Year - Month Year (e.g., "Jan 2020 - Dec 2022")
    month_year_pattern = r"(\w+)\s+(\d{4})\s*[-–to]+\s*(\w+)\s+(\d{4})"

    # Pattern: Year - Year (e.g., "2020 - 2022")
    year_pattern = r"(\d{4})\s*[-–to]+\s*(\d{4})"

    # Pattern: Month Year - Present (e.g., "Jan 2020 - Present")
    present_pattern = r"(\w+)\s+(\d{4})\s*[-–to]+\s*(?:present|current|ongoing)"

    # Education keywords to exclude
    education_keywords = [
        "education", "bachelor", "b.tech", "btech", "b.e.", "be",
        "master", "m.tech", "mtech", "m.e.", "me", "m.s.", "ms",
        "phd", "ph.d", "doctorate", "university", "college", "school",
        "degree", "diploma", "graduation", "graduated", "academic",
        "project", "projects", "research", "thesis", "coursework"
    ]

    # Try month-year patterns first
    for match in re.finditer(month_year_pattern, text):
        # Get context around the match to classify
        match_start = match.start()
        match_end = match.end()
        context_window = 100  # characters before and after
        context_start = max(0, match_start - context_window)
        context_end = min(len(text), match_end + context_window)
        context = text[context_start:context_end]

        # Check if this is in an education context
        # More strict: require education keyword to be within 50 chars of the date
        is_education = False
        for keyword in education_keywords:
            if keyword in context:
                # Check if keyword is close to the date range (within 50 chars)
                keyword_pos = context.find(keyword)
                date_pos_in_context = match_start - context_start
                if abs(keyword_pos - date_pos_in_context) < 50:
                    is_education = True
                    break

        if is_education:
            continue  # Skip education periods

        start_month_str = match.group(1)
        start_year = int(match.group(2))
        end_month_str = match.group(3)
        end_year = int(match.group(4))

        start_date = _parse_month_year(start_month_str, start_year)
        end_date = _parse_month_year(end_month_str, end_year)

        if start_date and end_date:
            # Check for internship keyword in context
            is_internship = "intern" in context
            periods.append((start_date, end_date, is_internship))

    # Try year patterns
    for match in re.finditer(year_pattern, text):
        # Get context
        match_start = match.start()
        match_end = match.end()
        context_window = 100
        context_start = max(0, match_start - context_window)
        context_end = min(len(text), match_end + context_window)
        context = text[context_start:context_end]

        # Check if this is in an education context (strict proximity check)
        is_education = False
        for keyword in education_keywords:
            if keyword in context:
                keyword_pos = context.find(keyword)
                date_pos_in_context = match_start - context_start
                if abs(keyword_pos - date_pos_in_context) < 50:
                    is_education = True
                    break

        if is_education:
            continue  # Skip education periods

        start_year = int(match.group(1))
        end_year = int(match.group(2))

        start_date = date(start_year, 1, 1)
        end_date = date(end_year, 12, 31)

        # Check for internship keyword in context
        is_internship = "intern" in context
        periods.append((start_date, end_date, is_internship))

    # Try present patterns
    for match in re.finditer(present_pattern, text):
        # Get context
        match_start = match.start()
        match_end = match.end()
        context_window = 100
        context_start = max(0, match_start - context_window)
        context_end = min(len(text), match_end + context_window)
        context = text[context_start:context_end]

        # Check if this is in an education context (strict proximity check)
        is_education = False
        for keyword in education_keywords:
            if keyword in context:
                keyword_pos = context.find(keyword)
                date_pos_in_context = match_start - context_start
                if abs(keyword_pos - date_pos_in_context) < 50:
                    is_education = True
                    break

        if is_education:
            continue  # Skip education periods

        start_month_str = match.group(1)
        start_year = int(match.group(2))

        start_date = _parse_month_year(start_month_str, start_year)
        end_date = date.today()  # Present means current date

        if start_date:
            # Check for internship keyword in context
            is_internship = "intern" in context
            periods.append((start_date, end_date, is_internship))

    return periods


def _parse_month_year(month_str: str, year: int) -> date | None:
    """Parse month name and year into a date object.

    Args:
        month_str: Month name (e.g., "Jan", "January")
        year: Year as integer

    Returns:
        Date object for first day of the month, or None if invalid
    """
    months = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }

    month_lower = month_str.lower()
    month_num = months.get(month_lower)

    if month_num is None:
        return None

    try:
        return date(year, month_num, 1)
    except ValueError:
        return None


def _sum_employment_periods(
    periods: list[tuple[date, date, bool]]
) -> float:
    """Sum employment periods, handling overlaps and internship weighting.

    Args:
        periods: List of (start_date, end_date, is_internship) tuples

    Returns:
        Total years of experience as float
    """
    if not periods:
        return 0.0

    # Sort periods by start date
    sorted_periods = sorted(periods, key=lambda x: x[0])

    # Merge overlapping periods
    merged: list[tuple[date, date, bool]] = []
    for start, end, is_internship in sorted_periods:
        if not merged:
            merged.append((start, end, is_internship))
        else:
            last_start, last_end, last_is_internship = merged[-1]

            # Check for overlap or adjacency
            if start <= last_end:
                # Merge: extend end date if current period ends later
                new_end = max(last_end, end)
                # If either is internship, mark as internship (conservative)
                new_is_internship = last_is_internship or is_internship
                merged[-1] = (last_start, new_end, new_is_internship)
            else:
                # No overlap, add as new period
                merged.append((start, end, is_internship))

    # Calculate total experience with internship weighting
    total_years = 0.0
    for start, end, is_internship in merged:
        duration_days = (end - start).days
        duration_years = duration_days / 365.25

        # Apply internship weighting
        if is_internship:
            duration_years *= INTERNSHIP_WEIGHTING

        # Only count if duration is at least minimum threshold
        if duration_years >= (MIN_ROLE_DURATION_MONTHS / 12.0):
            total_years += duration_years

    return round(total_years, 2)


def _count_internships(text: str) -> int:
    """Count internships mentioned in text.

    Args:
        text: Lowercase text to search

    Returns:
        Number of internships found
    """
    # More conservative pattern to avoid false positives
    # Look for "intern" as a standalone word or "internship"
    intern_pattern = r"\binternship\b"
    internship_matches = re.findall(intern_pattern, text)

    # Also look for "intern" but be more restrictive
    # Must be followed by role context (at, with, for, as)
    intern_role_pattern = r"\bintern\s+(?:at|with|for|as)\b"
    intern_role_matches = re.findall(intern_role_pattern, text)

    total = len(internship_matches) + len(intern_role_matches)

    # Be conservative: cap at reasonable maximum (e.g., 5)
    # to avoid overcounting from repeated mentions
    return min(total, 5)
