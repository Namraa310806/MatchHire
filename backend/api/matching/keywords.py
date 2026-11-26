"""Domain-keyword overlap signal (SPEC weight 0.20).

Jaccard similarity over explicitly supplied candidate and job domain
keyword sets::

    |A ∩ B| / |A ∪ B|

Normalization follows the shared domain-keyword conventions
(``api.extraction.domain_keywords``): inputs may be canonical keyword
names or aliases; aliases resolve to canonical names case-insensitively;
terms outside the fixed vocabulary are ignored; duplicates and order
do not matter.

Empty-set behavior (defined explicitly — SPEC is silent):

- Both sets empty -> 0.0. Two candidates/jobs with no domain-keyword
  data get no credit for the signal, consistent with the
  skill-similarity both-empty rule (0.0). Recorded as a proposed
  decision in docs/DECISIONS.md.
- Exactly one set empty -> 0.0 (empty intersection over non-empty
  union would be 0 anyway; stated for clarity).
"""

from collections.abc import Iterable

from api.extraction.domain_keywords import (
    get_all_domain_keywords,
    get_domain_keyword_aliases,
)

# alias/canonical (casefolded) -> canonical keyword name.
# Canonical names are registered first so they take precedence over
# aliases of other keywords; alias collisions resolve first-wins in
# vocabulary order (deterministic).
_KEYWORD_RESOLVER: dict[str, str] | None = None


def _build_resolver() -> dict[str, str]:
    resolver: dict[str, str] = {}
    canonicals = get_all_domain_keywords()
    for canonical in canonicals:
        resolver[canonical.casefold()] = canonical
    for canonical in canonicals:
        for alias in get_domain_keyword_aliases(canonical) or []:
            resolver.setdefault(alias.casefold(), canonical)
    return resolver


def _resolver() -> dict[str, str]:
    global _KEYWORD_RESOLVER
    if _KEYWORD_RESOLVER is None:
        _KEYWORD_RESOLVER = _build_resolver()
    return _KEYWORD_RESOLVER


def normalize_domain_keywords(keywords: Iterable[str]) -> frozenset[str]:
    """Normalize domain keywords to canonical vocabulary terms.

    Case-insensitive; aliases resolve to canonical names; unknown terms
    are dropped; duplicates collapse. Order does not matter.

    Raises:
        TypeError: if a non-string term is supplied.
    """
    resolver = _resolver()
    canonical: set[str] = set()
    for keyword in keywords:
        if not isinstance(keyword, str):
            raise TypeError(
                f"domain keywords must be strings, got {type(keyword).__name__}"
            )
        resolved = resolver.get(keyword.strip().casefold())
        if resolved is not None:
            canonical.add(resolved)
    return frozenset(canonical)


def jaccard_similarity(set_a: frozenset[str], set_b: frozenset[str]) -> float:
    """Jaccard similarity |A ∩ B| / |A ∪ B| with explicit empty rules.

    Both empty -> 0.0; exactly one empty -> 0.0; otherwise the standard
    ratio in [0.0, 1.0].
    """
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union


def keyword_overlap(
    candidate_keywords: Iterable[str],
    job_keywords: Iterable[str],
) -> float:
    """Jaccard similarity between normalized domain-keyword sets."""
    return jaccard_similarity(
        normalize_domain_keywords(candidate_keywords),
        normalize_domain_keywords(job_keywords),
    )
