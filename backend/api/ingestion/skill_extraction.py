"""Skill extraction from job descriptions."""

import re

# Skills dictionary with canonical names and aliases
# This is a representative subset (~30 skills) for Phase 2A
# In production, this would be expanded to 500+ terms per Decision 3
_SKILLS_DICT: dict[str, list[str]] = {
    # Programming languages
    "Python": ["python", "py"],
    "JavaScript": ["javascript", "js", "ecmascript"],
    "Java": ["java"],
    "C++": ["c++", "cpp"],
    "C": ["c"],
    "C#": ["c#", "csharp"],
    "Go": ["go", "golang"],
    "Rust": ["rust"],
    "Ruby": ["ruby"],
    "PHP": ["php"],
    "TypeScript": ["typescript", "ts"],
    "Swift": ["swift"],
    "Kotlin": ["kotlin"],
    "Scala": ["scala"],
    "R": ["r"],
    "SQL": ["sql"],
    "HTML": ["html"],
    "CSS": ["css"],
    # Frameworks and libraries
    "React": ["react", "reactjs", "react.js"],
    "Angular": ["angular", "angularjs"],
    "Vue": ["vue", "vuejs", "vue.js"],
    "Django": ["django"],
    "Flask": ["flask"],
    "Spring": ["spring", "spring boot"],
    "Node.js": ["node", "nodejs", "node.js"],
    "Express": ["express", "expressjs"],
    # Tools and platforms
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Git": ["git"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure"],
    "GCP": ["gcp", "google cloud platform"],
    "Linux": ["linux"],
}


def extract_skills(description: str) -> list[str]:
    """Extract skills from job description using deterministic matching.

    Uses word boundary matching to avoid false positives (e.g., "python" should not
    match inside "pythonic"). Case-insensitive matching. Returns canonical names.

    Args:
        description: The job description text

    Returns:
        List of canonical skill names found in the description (deduplicated)
    """
    found_skills: set[str] = set()
    description_lower = description.lower()

    for canonical_name, aliases in _SKILLS_DICT.items():
        # Check canonical name and all aliases
        for term in [canonical_name.lower()] + [a.lower() for a in aliases]:
            # Use word boundary matching to avoid substring false positives
            pattern = r"\b" + re.escape(term) + r"\b"
            if re.search(pattern, description_lower):
                found_skills.add(canonical_name)
                break  # Found this skill, don't check other aliases

    return sorted(found_skills)


def get_skills_dict() -> dict[str, list[str]]:
    """Get the skills dictionary.

    Returns:
        Dictionary mapping canonical skill names to aliases
    """
    return _SKILLS_DICT.copy()
