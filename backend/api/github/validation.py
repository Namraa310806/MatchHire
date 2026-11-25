"""GitHub username validation and normalization.

GitHub login rules: 1-39 chars, alphanumeric or single hyphens, no leading
or trailing hyphen. Logins are case-insensitive; we normalize to lowercase
for storage and uniqueness.
"""

import re

GITHUB_USERNAME_RE = re.compile(r"^[A-Za-z0-9](?:-?[A-Za-z0-9]){0,38}$")

# Repo full names ("owner/repo") as returned by the GitHub API. Validated
# before being used to build API paths.
GITHUB_REPO_FULL_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def normalize_username(raw: object) -> str | None:
    """Return the lowercase-normalized username, or None if invalid.

    Only bare usernames are accepted; URLs, emails, and other input are
    rejected.
    """
    if not isinstance(raw, str):
        return None
    candidate = raw.strip()
    if not GITHUB_USERNAME_RE.match(candidate):
        return None
    return candidate.lower()


def is_valid_repo_full_name(value: object) -> bool:
    """Check an ``owner/repo`` string before using it in API paths."""
    return isinstance(value, str) and bool(GITHUB_REPO_FULL_NAME_RE.match(value))
