"""Matching configuration for the v0 matching engine.

Weights are explicit configuration, not magic numbers. The defaults are
the SPEC formula::

    match_score = 0.50 * skill_similarity + 0.30 * experience_match
                + 0.20 * keyword_overlap

Validation guarantees every weight is finite, non-negative, and the
weights sum to 1.0 (within floating-point tolerance), so a weighted
total of component scores in [0, 1] can never leave [0, 1].
"""

import math
from dataclasses import dataclass

_WEIGHT_SUM_TOLERANCE = 1e-9


@dataclass(frozen=True)
class MatchConfig:
    """Scoring weights for the matching formula.

    Attributes:
        skill_weight: Weight of the TF-IDF skill similarity signal.
        experience_weight: Weight of the experience-match signal.
        keyword_weight: Weight of the domain-keyword Jaccard signal.
    """

    skill_weight: float = 0.50
    experience_weight: float = 0.30
    keyword_weight: float = 0.20

    def __post_init__(self) -> None:
        weights = (
            self.skill_weight,
            self.experience_weight,
            self.keyword_weight,
        )
        for name, value in zip(
            ("skill_weight", "experience_weight", "keyword_weight"), weights, strict=True
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"{name} must be a real number, got {type(value).__name__}")
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite, got {value}")
            if value < 0.0:
                raise ValueError(f"{name} must be non-negative, got {value}")

        total = sum(weights)
        if abs(total - 1.0) > _WEIGHT_SUM_TOLERANCE:
            raise ValueError(
                "MatchConfig weights must sum to 1.0 "
                f"(got {total!r}: skill={self.skill_weight}, "
                f"experience={self.experience_weight}, keyword={self.keyword_weight})"
            )


DEFAULT_CONFIG = MatchConfig()
