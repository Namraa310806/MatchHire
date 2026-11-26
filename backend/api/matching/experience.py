"""Experience-match signal (SPEC weight 0.30).

Implements the exact rules from docs/SPEC.md "Experience Matching
(Decision 1)". No additional bonuses or penalties are applied.

Rules implemented (SPEC references):

- Job requires zero years / no requirement (``required_yoe = 0`` or
  both job fields ``None``): score = 1.0 for ANY candidate experience,
  including unknown (``user_yoe = null`` -> 1.0). [SPEC: "Job Specifies
  Zero Years", "Experience Missing or Unknown from Job"]
- Job requires positive minimum (``required_yoe > 0``):
  ``min(user_yoe / required_yoe, 1.0)`` when ``user_yoe`` is known;
  candidate >= minimum -> 1.0 (capped); candidate < minimum -> partial
  credit; ``user_yoe = null`` -> 0.0. [SPEC: "Job Requires Positive
  Minimum"]
- Job specifies a range: if the range includes 0 (minimum is 0 or
  absent-with-maximum), treat as ``required_yoe = 0`` -> 1.0 for all;
  otherwise use the minimum value in the formula; candidate above the
  range -> 1.0 (overqualification never penalized); ``user_yoe = null``
  -> 0.0 unless the range includes 0. [SPEC: "Job Specifies Range"]
- Division-by-zero protection: when ``required_yoe = 0`` the formula
  is never evaluated; score is 1.0. [SPEC: "Division by Zero
  Protection"]

``experience_max_years`` is part of the input contract but does not
enter the formula: SPEC caps the score at 1.0 and never penalizes
candidates above the range, so the upper bound cannot change the
result. It is retained so the integration gate can pass job rows
through unchanged.
"""

import math


def _validate_years(value: float | None, name: str) -> None:
    if value is None:
        return
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be a real number or None")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value}")
    if value < 0.0:
        raise ValueError(f"{name} must be non-negative, got {value}")


def experience_match(
    user_yoe: float | None,
    required_min_years: float | None,
    required_max_years: float | None = None,
) -> float:
    """Compute the experience-match component in [0, 1].

    Args:
        user_yoe: Candidate's total years of experience; ``None`` means
            unknown (distinct from explicit 0.0).
        required_min_years: Job's minimum required years; ``None`` means
            no lower bound stated.
        required_max_years: Job's maximum stated years (upper bound of a
            range). Accepted for contract completeness; does not affect
            the score per SPEC (overqualification is not penalized).

    Returns:
        Experience match score in [0.0, 1.0].
    """
    _validate_years(user_yoe, "user_yoe")
    _validate_years(required_min_years, "required_min_years")
    _validate_years(required_max_years, "required_max_years")

    # No requirement stated -> required_yoe = 0 -> score 1.0 for all,
    # including unknown candidate experience.
    if required_min_years is None and required_max_years is None:
        return 1.0

    # Effective minimum: an absent minimum with a stated maximum is a
    # range starting at 0 ("up to X years"), which includes 0.
    required = required_min_years if required_min_years is not None else 0.0

    # required_yoe = 0 (explicit zero, or a range including 0): full
    # match for any candidate experience, including unknown. No
    # division is performed (division-by-zero protection).
    if required <= 0.0:
        return 1.0

    # required_yoe > 0 with unknown candidate experience -> 0.0
    # (assume not qualified, per SPEC).
    if user_yoe is None:
        return 0.0

    # min(user_yoe / required_yoe, 1.0): partial credit below the
    # minimum, capped at 1.0 at or above it (overqualification free).
    return min(user_yoe / required, 1.0)
