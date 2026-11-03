"""Years of experience extraction from job descriptions."""

import re


def extract_required_yoe(description: str) -> float | None:
    """Extract required years of experience from job description.

    Conservative extraction following Decision 1 semantics:
    - "fresher" or "fresh graduate" → 0.0
    - "0 years" or "0-2 years" (range includes 0) → 0.0
    - "1-3 years" or "at least 1 year" → 1.0 (minimum of range)
    - "3+ years" or "at least 3 years" → 3.0
    - Missing or ambiguous → None

    Rules:
    - Never guess from ambiguous text
    - Distinguish explicit 0 from unknown
    - Use minimum value from ranges
    - Handle punctuation and capitalization variations

    Args:
        description: The job description text

    Returns:
        Required years of experience as float, or None if unknown/ambiguous
    """
    if not description:
        return None

    description_lower = description.lower()

    # Pattern 1: Explicit "fresher" or "fresh graduate" → 0.0
    if re.search(r"\bfresh(er| graduate)?\b", description_lower):
        return 0.0

    # Pattern 2: "0 years" or "0 year" → 0.0
    match = re.search(r"\b0\s*years?\b", description_lower)
    if match:
        return 0.0

    # Pattern 3: Ranges that include 0 (e.g., "0-2 years", "0 to 2 years")
    match = re.search(r"\b0\s*[-–to]+\s*(\d+)\s*years?\b", description_lower)
    if match:
        return 0.0

    # Pattern 4: Ranges that exclude 0 (e.g., "1-3 years", "2-5 years")
    # Extract the minimum value
    match = re.search(r"\b(\d+)\s*[-–to]+\s*\d+\s*years?\b", description_lower)
    if match:
        min_val = float(match.group(1))
        if min_val > 0:
            return min_val

    # Pattern 5: "at least X years" or "minimum X years"
    match = re.search(r"\b(at least|minimum)\s+(\d+)\s*years?\b", description_lower)
    if match:
        min_val = float(match.group(2))
        if min_val > 0:
            return min_val

    # Pattern 6: "X+ years" or "X plus years"
    match = re.search(r"\b(\d+)\s*\+\s*years?\b", description_lower)
    if match:
        min_val = float(match.group(1))
        if min_val > 0:
            return min_val

    # Pattern 7: Single year requirement (e.g., "3 years experience")
    match = re.search(r"\b(\d+)\s*years?\s*(of\s*)?experience\b", description_lower)
    if match:
        val = float(match.group(1))
        if val > 0:
            return val

    # No clear pattern found → return None (unknown)
    return None
