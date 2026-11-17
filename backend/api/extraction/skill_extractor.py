"""Skill extraction engine with versioned dictionary support.

This module provides deterministic skill extraction from text using a
versioned skills dictionary with alias resolution and word-boundary-aware
matching to avoid false positives.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DICTIONARY_PATH = Path(__file__).parent / "skills_dictionary.json"


@dataclass
class SkillMatch:
    """Represents a skill extracted from text."""

    canonical_name: str
    category: str
    matched_alias: str | None = None


class SkillsDictionary:
    """Versioned skills dictionary with validation and alias resolution."""

    def __init__(self, dictionary_path: Path = DICTIONARY_PATH):
        """Load and validate the skills dictionary.

        Args:
            dictionary_path: Path to the skills dictionary JSON file

        Raises:
            ValueError: If dictionary is invalid or fails validation
            FileNotFoundError: If dictionary file does not exist
        """
        self.dictionary_path = dictionary_path
        self._data: dict[str, Any] = {}
        self._alias_to_canonical: dict[str, tuple[str, str]] = {}
        self._canonical_to_category: dict[str, str] = {}
        self._load_and_validate()

    def _load_and_validate(self) -> None:
        """Load dictionary from JSON and perform validation.

        Raises:
            ValueError: If dictionary structure is invalid
            FileNotFoundError: If dictionary file does not exist
        """
        if not self.dictionary_path.exists():
            raise FileNotFoundError(f"Skills dictionary not found: {self.dictionary_path}")

        with open(self.dictionary_path, encoding="utf-8") as f:
            self._data = json.load(f)

        # Validate top-level structure
        if "version" not in self._data:
            raise ValueError("Dictionary missing 'version' field")
        if "skills" not in self._data:
            raise ValueError("Dictionary missing 'skills' field")
        if not isinstance(self._data["skills"], dict):
            raise ValueError("'skills' field must be a dictionary")

        # Build alias resolution maps and validate
        all_canonical_names: set[str] = set()
        all_aliases: set[str] = set()

        for category, skills in self._data["skills"].items():
            if not isinstance(skills, list):
                raise ValueError(f"Category '{category}' must contain a list")

            for skill_entry in skills:
                if not isinstance(skill_entry, dict):
                    raise ValueError(f"Skill entry in '{category}' must be a dictionary")

                canonical = skill_entry.get("canonical")
                aliases = skill_entry.get("aliases", [])

                if not canonical or not isinstance(canonical, str):
                    raise ValueError("Skill entry missing valid 'canonical' field")

                if not isinstance(aliases, list):
                    raise ValueError(f"'aliases' for '{canonical}' must be a list")

                # Check for duplicate canonical names
                if canonical in all_canonical_names:
                    raise ValueError(f"Duplicate canonical name: '{canonical}'")
                all_canonical_names.add(canonical)

                # Register canonical name with category
                self._canonical_to_category[canonical] = category

                # Register canonical name as its own alias (case-insensitive)
                canonical_lower = canonical.lower()
                if canonical_lower in all_aliases:
                    raise ValueError(f"Ambiguous alias: '{canonical_lower}' maps to multiple skills")
                self._alias_to_canonical[canonical_lower] = (canonical, category)
                all_aliases.add(canonical_lower)

                # Register all aliases
                for alias in aliases:
                    if not isinstance(alias, str):
                        raise ValueError(f"Alias for '{canonical}' must be a string")

                    alias_lower = alias.lower()
                    if alias_lower in all_aliases:
                        # Check if it's the same canonical name (self-alias is OK)
                        existing_canonical, _ = self._alias_to_canonical[alias_lower]
                        if existing_canonical != canonical:
                            raise ValueError(
                                f"Ambiguous alias: '{alias_lower}' maps to both "
                                f"'{existing_canonical}' and '{canonical}'"
                            )
                    self._alias_to_canonical[alias_lower] = (canonical, category)
                    all_aliases.add(alias_lower)

    @property
    def version(self) -> str:
        """Get the dictionary version."""
        return str(self._data.get("version", "unknown"))

    @property
    def last_updated(self) -> str:
        """Get the last updated date."""
        return str(self._data.get("last_updated", "unknown"))

    @property
    def total_skills(self) -> int:
        """Get total number of canonical skills."""
        return len(self._canonical_to_category)

    @property
    def total_aliases(self) -> int:
        """Get total number of aliases (including canonical names)."""
        return len(self._alias_to_canonical)

    def get_category(self, canonical_name: str) -> str | None:
        """Get the category for a canonical skill name.

        Args:
            canonical_name: The canonical skill name

        Returns:
            Category name or None if not found
        """
        return self._canonical_to_category.get(canonical_name)

    def resolve_alias(self, alias: str) -> tuple[str, str] | None:
        """Resolve an alias to its canonical name and category.

        Args:
            alias: The alias to resolve (case-insensitive)

        Returns:
            Tuple of (canonical_name, category) or None if not found
        """
        return self._alias_to_canonical.get(alias.lower())

    def get_all_canonical_names(self) -> list[str]:
        """Get all canonical skill names.

        Returns:
            List of canonical skill names
        """
        return list(self._canonical_to_category.keys())

    def get_skills_by_category(self, category: str) -> list[str]:
        """Get all canonical skill names in a category.

        Args:
            category: The category name

        Returns:
            List of canonical skill names in the category
        """
        return [name for name, cat in self._canonical_to_category.items() if cat == category]


# Global instance (singleton pattern for performance)
_global_dictionary: SkillsDictionary | None = None


def get_skills_dictionary() -> SkillsDictionary:
    """Get the global skills dictionary instance.

    This loads the dictionary once and reuses it for subsequent calls
    to avoid repeated file I/O and validation overhead.

    Returns:
        The global SkillsDictionary instance

    Raises:
        ValueError: If dictionary is invalid
        FileNotFoundError: If dictionary file does not exist
    """
    global _global_dictionary
    if _global_dictionary is None:
        _global_dictionary = SkillsDictionary()
    return _global_dictionary


def extract_skills(text: str) -> list[SkillMatch]:
    """Extract skills from text using word-boundary-aware matching.

    This function performs case-insensitive, word-boundary-aware matching
    to avoid false positives (e.g., "Go" should not match in "going").
    Aliases are resolved to canonical names. Results are deduplicated and
    sorted deterministically.

    Special handling for ambiguous patterns:
    - "Go" vs "going": requires word boundary
    - "R" vs ordinary text: requires word boundary
    - "C" vs unrelated words: requires word boundary
    - "C++", "C#", ".NET": exact matches required
    - "Node.js", "React.js": dot is part of the skill name
    - "CI/CD": slash is part of the skill name
    - "REST API": space is part of the skill name

    Args:
        text: The text to extract skills from

    Returns:
        List of SkillMatch objects with canonical names and categories,
        sorted by canonical name for determinism
    """
    if not text:
        return []

    dictionary = get_skills_dictionary()
    text_lower = text.lower()

    found_skills: dict[str, SkillMatch] = {}

    # Iterate through canonical names
    for canonical, category in dictionary._canonical_to_category.items():
        # Check canonical name
        canonical_lower = canonical.lower()
        if _match_skill(text_lower, canonical_lower):
            found_skills[canonical] = SkillMatch(
                canonical_name=canonical, category=category, matched_alias=canonical
            )
            continue  # Already found canonical, no need to check aliases

        # Check aliases
        for alias, (alias_canonical, _alias_category) in dictionary._alias_to_canonical.items():
            if alias_canonical == canonical and alias != canonical_lower:
                if _match_skill(text_lower, alias):
                    found_skills[canonical] = SkillMatch(
                        canonical_name=canonical,
                        category=category,
                        matched_alias=alias,
                    )
                    break  # Found this skill via alias, stop checking other aliases

    # Return sorted list for determinism
    return sorted(found_skills.values(), key=lambda x: x.canonical_name)


def _match_skill(text: str, skill_term: str) -> bool:
    """Check if a skill term matches in text with word-boundary awareness.

    This handles special cases:
    - Skills with dots (Node.js, React.js): dots are treated as part of the word
    - Skills with slashes (CI/CD): slashes are treated as part of the word
    - Skills with spaces (REST API): spaces require word boundaries around phrase
    - Skills with special chars (C++, C#, .NET): special chars are literal
    - Single-letter skills (C, R, Go): require strict word boundaries

    Args:
        text: The lowercase text to search in
        skill_term: The lowercase skill term to match

    Returns:
        True if the skill term is found with proper boundaries
    """
    # For C#, we need special handling since # is a word boundary in regex
    if skill_term == "c#":
        # Match C# as a whole word: "c#" or "C#"
        return bool(re.search(r"\bc#(?=\W|$)", text))

    # Escape special regex characters except spaces, dots, slashes, plus, hash
    # These are treated as literal parts of skill names
    escaped = re.escape(skill_term)

    # Restore escaped characters that should be literal in skill names
    escaped = escaped.replace(r"\.", ".")  # Dots in Node.js, React.js
    escaped = escaped.replace(r"/", "/")  # Slashes in CI/CD
    escaped = escaped.replace(r"\+", "+")  # Plus in C++
    escaped = escaped.replace(r"\ ", " ")  # Spaces in phrases

    # For multi-word terms (with spaces), match as phrase with word boundaries
    if " " in skill_term:
        pattern = r"\b" + escaped + r"\b"
    else:
        # For single-word terms, use word boundary
        pattern = r"\b" + escaped + r"\b"

    return bool(re.search(pattern, text))
