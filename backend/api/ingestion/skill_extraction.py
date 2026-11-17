"""Skill extraction from job descriptions using shared versioned dictionary.

This module now uses the shared extraction utilities from api.extraction
to maintain consistency between job ingestion and resume parsing.
The original ~30-term dictionary has been replaced with the versioned
500+ term dictionary per Phase 3A requirements.
"""

from api.extraction import SkillMatch
from api.extraction import extract_skills as shared_extract_skills


def extract_skills(description: str) -> list[str]:
    """Extract skills from job description using the shared versioned dictionary.

    This function is a thin wrapper around the shared extraction engine
    to maintain backward compatibility with the existing ingestion pipeline.
    It returns only canonical skill names (not full SkillMatch objects)
    to match the original interface.

    The shared extractor provides:
    - Case-insensitive matching
    - Word-boundary-aware matching to avoid false positives
    - Alias resolution to canonical names
    - Deterministic output (sorted)
    - Duplicate removal
    - 500+ canonical skills with categories

    Args:
        description: The job description text

    Returns:
        List of canonical skill names found in the description (deduplicated, sorted)
    """
    skill_matches: list[SkillMatch] = shared_extract_skills(description)
    return [match.canonical_name for match in skill_matches]


def get_skills_dict() -> dict[str, list[str]]:
    """Get the skills dictionary for backward compatibility.

    This function provides a dictionary representation of the skills
    vocabulary for compatibility with existing tests and code that expect
    the old dictionary format. This is deprecated; new code should use
    the SkillsDictionary class from api.extraction instead.

    Returns:
        Dictionary mapping canonical skill names to aliases (simplified representation)
    """
    from api.extraction import get_skills_dictionary

    dictionary = get_skills_dictionary()
    result: dict[str, list[str]] = {}

    # Build a simplified dict representation
    for canonical in dictionary.get_all_canonical_names():
        # In the new structure, we don't have a direct alias list per canonical
        # For backward compatibility, we return the canonical name as its own alias
        result[canonical] = [canonical]

    return result
