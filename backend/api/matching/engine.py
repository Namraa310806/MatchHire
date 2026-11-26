"""v0 matching engine — pure Python, no Django imports.

Public interface::

    match(candidate, job, config=DEFAULT_CONFIG, vectorizer=...) -> MatchResult

Formula (docs/SPEC.md, Match-Score Semantics)::

    match_score = 0.50 * skill_similarity
                + 0.30 * experience_match
                + 0.20 * keyword_overlap

This module is the permanent reference matcher. It performs no I/O:
no database, no Redis, no network, no Django. All inputs are plain
data objects from ``api.matching.inputs``.
"""

import math
from dataclasses import dataclass

from api.matching.config import DEFAULT_CONFIG, MatchConfig
from api.matching.experience import experience_match
from api.matching.inputs import CandidateInput, JobInput
from api.matching.keywords import keyword_overlap
from api.matching.tfidf import TfidfVectorizer, skill_similarity


@dataclass(frozen=True)
class MatchResult:
    """Component breakdown and weighted total for one candidate/job pair.

    All scores are floats in [0.0, 1.0]. ``total_score`` is the
    weighted sum of the three components; the components are exposed
    separately because they are persisted for the score breakdown
    (``MatchScore.skill_similarity`` etc.).
    """

    total_score: float
    skill_similarity: float
    experience_match: float
    keyword_overlap: float

    def __post_init__(self) -> None:
        for name in (
            "total_score",
            "skill_similarity",
            "experience_match",
            "keyword_overlap",
        ):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"{name} must be a real number")
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite, got {value}")
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0.0, 1.0], got {value}")


def match(
    candidate: CandidateInput,
    job: JobInput,
    config: MatchConfig = DEFAULT_CONFIG,
    *,
    vectorizer: TfidfVectorizer,
) -> MatchResult:
    """Score one candidate/job pair with the v0 formula.

    Args:
        candidate: Candidate skills, experience, domain keywords.
        job: Job skills, experience requirement, domain keywords.
        config: Scoring weights (defaults to the SPEC 50/30/20 split).
        vectorizer: REQUIRED. The TF-IDF vectorizer for the skill
            signal. There is deliberately no default: callers must pass
            ``UNIFORM_VECTORIZER`` (uniform weights — binary cosine,
            NOT corpus-fitted TF-IDF) or a ``TfidfVectorizer.fit(...)``
            instance fitted on the job corpus, so uniform behavior can
            never be used silently in a production scoring path.

    Returns:
        MatchResult with the total and all three component scores.
    """
    sim = skill_similarity(candidate.skills, job.skills, vectorizer)
    exp = experience_match(
        candidate.total_experience_years,
        job.experience_min_years,
        job.experience_max_years,
    )
    kw = keyword_overlap(candidate.domain_keywords, job.domain_keywords)

    total = (
        config.skill_weight * sim
        + config.experience_weight * exp
        + config.keyword_weight * kw
    )
    # Defensive clamp: components are each in [0,1] and weights sum to
    # 1.0, so this only guards against float rounding at the boundary.
    total = min(max(total, 0.0), 1.0)

    return MatchResult(
        total_score=total,
        skill_similarity=sim,
        experience_match=exp,
        keyword_overlap=kw,
    )
