"""Input contract for the v0 matching engine.

The matcher consumes plain data objects — never Django models — so the
core stays importable and testable without Django initialization.

Field semantics mirror the persisted models they will be adapted from
at the integration gate:

- ``CandidateInput.skills`` / ``JobInput.skills``: skill names as
  canonical names or aliases from the fixed skills dictionary
  (``api.extraction``). Aliases are resolved to canonical names;
  terms outside the vocabulary are ignored, matching the SPEC rule
  that unknown skills are excluded from matching.
- ``CandidateInput.total_experience_years``: the candidate's total
  years of experience. ``None`` means *unknown* — distinct from an
  explicit ``0.0`` (fresher). The matcher does NOT aggregate
  ``WorkExperience`` rows; that decision belongs to the integration
  gate.
- ``JobInput.experience_min_years`` / ``experience_max_years``: the
  job's experience requirement. Both ``None`` means no requirement.
  ``experience_max_years`` is accepted for contract completeness;
  per SPEC, overqualification is never penalized, so the upper bound
  does not reduce the score.
- ``domain_keywords``: canonical domain keywords as produced by
  ``api.extraction.domain_keywords`` (or stored in
  ``CandidateProfile.extracted_domain_keywords``). Aliases are
  resolved; terms outside the fixed vocabulary are ignored.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field


def _freeze_strings(values: Iterable[str]) -> tuple[str, ...]:
    """Coerce an iterable of strings into a tuple, preserving order."""
    return tuple(values)


@dataclass(frozen=True)
class CandidateInput:
    """Everything the matcher needs to know about a candidate."""

    skills: tuple[str, ...] = field(default_factory=tuple)
    total_experience_years: float | None = None
    domain_keywords: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_iterables(
        cls,
        skills: Iterable[str] = (),
        domain_keywords: Iterable[str] = (),
        total_experience_years: float | None = None,
    ) -> "CandidateInput":
        """Build a CandidateInput from arbitrary iterables (e.g. lists)."""
        return cls(
            skills=_freeze_strings(skills),
            total_experience_years=total_experience_years,
            domain_keywords=_freeze_strings(domain_keywords),
        )


@dataclass(frozen=True)
class JobInput:
    """Everything the matcher needs to know about a job."""

    skills: tuple[str, ...] = field(default_factory=tuple)
    experience_min_years: float | None = None
    experience_max_years: float | None = None
    domain_keywords: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_iterables(
        cls,
        skills: Iterable[str] = (),
        domain_keywords: Iterable[str] = (),
        experience_min_years: float | None = None,
        experience_max_years: float | None = None,
    ) -> "JobInput":
        """Build a JobInput from arbitrary iterables (e.g. lists)."""
        return cls(
            skills=_freeze_strings(skills),
            experience_min_years=experience_min_years,
            experience_max_years=experience_max_years,
            domain_keywords=_freeze_strings(domain_keywords),
        )
