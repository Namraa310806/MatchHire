"""Profile persistence and cache invalidation for resume parsing results.

Persists only fields supported by the current data model:
- Canonical skills -> ``Skill`` / ``CandidateSkill`` rows (fixed vocabulary;
  unknown terms are never persisted).
- Domain keywords -> ``CandidateProfile.extracted_domain_keywords`` (JSON).
- Experience estimate -> ``CandidateProfile.total_experience_years`` only when
  currently unset, so an estimate never overwrites an explicit user value.

Deletion semantics (Decision 9): deleting the resume file never deletes
extracted profile data.
"""

import logging
from decimal import Decimal
from typing import Any

from django.core.cache import cache
from django.db import transaction

from api.evidence import SOURCE_RESUME, link_skill
from api.extraction import (
    DomainKeywordMatch,
    ExperienceEstimate,
    SkillMatch,
    get_skills_dictionary,
)
from api.models import CandidateProfile, Skill

logger = logging.getLogger(__name__)

# Cache key conventions for matching. The matching engine is not yet
# implemented; these keys document the invalidation interface it must use.
MATCH_SCORES_CACHE_KEY = "match:scores:candidate:{candidate_id}"


def invalidate_matching_caches(candidate_id: int) -> None:
    """Invalidate cached match data derived from a candidate profile.

    Minimal documented interface until the matching engine lands: removes
    the candidate's cached match-score set. Safe to call when no cache
    entries exist.
    """
    cache.delete(MATCH_SCORES_CACHE_KEY.format(candidate_id=candidate_id))


@transaction.atomic
def persist_resume_extraction(
    profile: CandidateProfile,
    skills: list[SkillMatch],
    domain_keywords: list[DomainKeywordMatch],
    experience: ExperienceEstimate,
) -> dict[str, Any]:
    """Persist extracted resume data onto the candidate profile.

    Args:
        profile: The candidate profile to update (locked by caller).
        skills: Canonical skill matches from the shared extractor.
        domain_keywords: Domain keyword matches from the shared extractor.
        experience: Experience estimate from the shared estimator.

    Returns:
        Summary dict of what was persisted (counts only, no PII).
    """
    dictionary = get_skills_dictionary()
    skills_linked = 0

    for match in skills:
        category = dictionary.get_category(match.canonical_name) or match.category
        skill, _created = Skill.objects.get_or_create(
            name=match.canonical_name,
            defaults={"category": category},
        )
        detail = {"matched_alias": match.matched_alias} if match.matched_alias else {}
        _cs, created, _ev, _ev_created = link_skill(
            profile, skill, source=SOURCE_RESUME, detail=detail, proficiency=""
        )
        if created:
            skills_linked += 1

    keywords = sorted({kw.keyword for kw in domain_keywords})
    profile.extracted_domain_keywords = keywords

    experience_years = None
    if experience.total_years is not None and profile.total_experience_years is None:
        # Only fill an unset value: never overwrite an explicit user entry
        # with an estimate.
        profile.total_experience_years = Decimal(str(experience.total_years))
        experience_years = float(experience.total_years)

    profile.save(
        update_fields=[
            "extracted_domain_keywords",
            "total_experience_years",
            "updated_at",
        ]
    )

    return {
        "skills_found": len(skills),
        "skills_linked": skills_linked,
        "domain_keywords": len(keywords),
        "experience_years": experience_years,
        "experience_confidence": experience.confidence,
    }


def delete_resume_file(profile: CandidateProfile) -> None:
    """Delete the stored resume file and clear upload metadata.

    Per Decision 9, extracted profile data (skills, domain keywords,
    experience) is retained; only the file and its upload metadata are
    removed. Consent is revoked because the candidate can no longer
    permit processing of a file that no longer exists.
    """
    if profile.resume_file:
        profile.resume_file.delete(save=False)
    profile.resume_file = ""
    profile.resume_uploaded_at = None
    profile.resume_consent_given = False
    profile.save(
        update_fields=[
            "resume_file",
            "resume_uploaded_at",
            "resume_consent_given",
            "updated_at",
        ]
    )
