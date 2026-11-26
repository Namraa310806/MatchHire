"""v0 matching engine — pure Python reference matcher.

No Django imports, no database, no Redis, no network. Importable and
testable without Django initialization.
"""

from api.matching.config import DEFAULT_CONFIG, MatchConfig
from api.matching.engine import MatchResult, match
from api.matching.experience import experience_match
from api.matching.inputs import CandidateInput, JobInput
from api.matching.keywords import keyword_overlap
from api.matching.tfidf import (
    UNIFORM_VECTORIZER,
    TfidfVectorizer,
    cosine_similarity,
    normalize_skill_names,
    skill_similarity,
)

__all__ = [
    "DEFAULT_CONFIG",
    "UNIFORM_VECTORIZER",
    "CandidateInput",
    "JobInput",
    "MatchConfig",
    "MatchResult",
    "TfidfVectorizer",
    "cosine_similarity",
    "experience_match",
    "keyword_overlap",
    "match",
    "normalize_skill_names",
    "skill_similarity",
]
