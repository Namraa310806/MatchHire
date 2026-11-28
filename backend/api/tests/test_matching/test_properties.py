"""Property-based correctness tests for the v0 matching engine.

Phase 4 Gate 3. Verifies the eight invariants from
``MatchHire_Prompt_Playbook.md`` ("phase4: add property-based scoring
tests") plus the 10,000-pair randomized sweep, using Hypothesis.

Reproducibility
---------------
Every ``@given`` test uses ``derandomize=True``: Hypothesis runs a
fixed deterministic example sequence (no database, no random seed
dependency), so a failure reproduces identically on every run and on
every machine. When a property fails, Hypothesis prints a
``@reproduce_failure`` decorator blob — paste it above the failing
test to replay the exact generated inputs.

The 10,000-pair sweep is ``test_10000_pairs_invariants_hold`` with
``max_examples=10_000``: each generated example is one candidate/job
pair scored through the real ``api.matching.match()``. Hypothesis does
not guarantee uniqueness — duplicate pairs are permitted and counted;
the effective input space is large enough that exact duplicates are
rare but possible.

Vocabulary used for generation is the REAL fixed vocabulary the
matcher consumes: canonical skills + aliases from
``skills_dictionary.json``, canonical domain keywords + aliases from
``api.extraction.domain_keywords``, plus out-of-vocabulary strings.
"""

import itertools
import json
import math

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from api.extraction.domain_keywords import (
    get_all_domain_keywords,
    get_domain_keyword_aliases,
)
from api.extraction.skill_extractor import DICTIONARY_PATH, get_skills_dictionary
from api.matching import (
    DEFAULT_CONFIG,
    UNIFORM_VECTORIZER,
    CandidateInput,
    JobInput,
    TfidfVectorizer,
    cosine_similarity,
    experience_match,
    keyword_overlap,
    match,
    skill_similarity,
)
from api.matching.keywords import jaccard_similarity, normalize_domain_keywords

# ---------------------------------------------------------------------------
# Vocabulary pools for generation (real matcher inputs)
# ---------------------------------------------------------------------------

_dictionary = get_skills_dictionary()
CANONICAL_SKILLS: list[str] = sorted(_dictionary.get_all_canonical_names())

# canonical -> [canonical, *aliases] raw input forms that all normalize
# to that canonical skill.
_SKILL_FORMS: dict[str, list[str]] = {}
with DICTIONARY_PATH.open(encoding="utf-8") as _fh:
    _raw_dict = json.load(_fh)
for _category, _entries in _raw_dict["skills"].items():
    for _entry in _entries:
        _canonical = _entry["canonical"]
        _SKILL_FORMS[_canonical] = [_canonical, *_entry.get("aliases", [])]


# Case/whitespace mutations of canonical names (normalization edge).
def _mutated_forms(canonical: str) -> list[str]:
    return [f"  {canonical}  ", canonical.upper(), canonical.lower()]


_MUTATED_SKILL_FORMS = [
    form for base in CANONICAL_SKILLS[:80] for form in _mutated_forms(base)
]

_UNKNOWN_TERMS = [
    "NotARealSkill123",
    "Underwater Basket Weaving",
    "Quantum Basket Weaving",
    "",
    "   ",
    "Pythön",
    "!!!",
    "skill",
]

# Every raw term that can appear in a generated skill list. Aliases and
# canonical names resolve into the fixed vocabulary; unknown terms are
# dropped by the matcher (SPEC rule).
SKILL_TERM_POOL: list[str] = sorted(
    {form for forms in _SKILL_FORMS.values() for form in forms}
    | set(_MUTATED_SKILL_FORMS)
    | set(_UNKNOWN_TERMS)
)

CANONICAL_DOMAIN_KEYWORDS: list[str] = sorted(get_all_domain_keywords())
_KEYWORD_FORMS: dict[str, list[str]] = {
    canonical: [canonical, *(get_domain_keyword_aliases(canonical) or [])]
    for canonical in CANONICAL_DOMAIN_KEYWORDS
}
KEYWORD_TERM_POOL: list[str] = sorted(
    {form for forms in _KEYWORD_FORMS.values() for form in forms}
    | {"NotARealKeyword", "", "   ", "!!!"}
)

# Two disjoint halves of the canonical skill vocabulary. Every alias of
# a skill in one half resolves to a canonical in that same half (the
# dictionary loader rejects cross-skill alias collisions), so lists
# drawn from each half's forms normalize to disjoint canonical sets.
_HALF_A_CANONICAL = set(CANONICAL_SKILLS[: len(CANONICAL_SKILLS) // 2])
_HALF_B_CANONICAL = set(CANONICAL_SKILLS[len(CANONICAL_SKILLS) // 2 :])
HALF_A_TERMS = sorted({form for c in _HALF_A_CANONICAL for form in _SKILL_FORMS[c]})
HALF_B_TERMS = sorted({form for c in _HALF_B_CANONICAL for form in _SKILL_FORMS[c]})

# A fixed, deterministic corpus for a corpus-fitted vectorizer. Mixing
# common and rare skills keeps IDF weights non-uniform.
_FITTED_CORPUS = [
    ["Python", "Django"],
    ["Python", "Flask"],
    ["Python", "FastAPI"],
    ["JavaScript", "React"],
    ["JavaScript", "Node.js"],
    ["Java", "Spring Boot"],
    ["Go", "Kubernetes"],
    ["Rust", "Actix"],
    ["C++", "Embedded Systems"],
    ["C", "Embedded Systems"],
    ["Machine Learning", "PyTorch", "Python"],
    ["Data Science", "Python", "SQL"],
    ["DevOps", "AWS", "Docker"],
    ["Python", "Go"],
    ["React", "TypeScript"],
    ["Python"],
    ["Django"],
    ["Kubernetes"],
    ["SQL"],
    ["PyTorch"],
]
FITTED_VECTORIZER = TfidfVectorizer.fit(_FITTED_CORPUS)

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_vec_strategy = st.one_of(st.just(UNIFORM_VECTORIZER), st.just(FITTED_VECTORIZER))

_skill_list = st.lists(st.sampled_from(SKILL_TERM_POOL), max_size=12)

_keyword_list = st.lists(st.sampled_from(KEYWORD_TERM_POOL), max_size=8)

_yoe = st.one_of(
    st.none(),
    st.floats(min_value=0.0, max_value=40.0, allow_nan=False, allow_infinity=False),
)

_req_years = st.one_of(
    st.none(),
    st.floats(min_value=0.0, max_value=20.0, allow_nan=False, allow_infinity=False),
)


candidate_strategy = st.builds(
    CandidateInput.from_iterables,
    skills=_skill_list,
    domain_keywords=_keyword_list,
    total_experience_years=_yoe,
)
job_strategy = st.builds(
    JobInput.from_iterables,
    skills=_skill_list,
    domain_keywords=_keyword_list,
    experience_min_years=_req_years,
    experience_max_years=_req_years,
)

_PROPS = settings(
    max_examples=500,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


def _components(result) -> tuple[float, ...]:
    return (
        result.total_score,
        result.skill_similarity,
        result.experience_match,
        result.keyword_overlap,
    )


def _assert_finite_bounded(result) -> None:
    for value in _components(result):
        assert isinstance(value, float)
        assert math.isfinite(value)
        assert 0.0 <= value <= 1.0


def _permuted_with_duplicates(values: tuple[str, ...]) -> tuple[str, ...]:
    """Reorder a tuple and duplicate every element (order/dup edge)."""
    doubled = tuple(v for item in values for v in (item, item))
    return tuple(reversed(doubled))


# ---------------------------------------------------------------------------
# Invariant 1 — score always in [0, 1]; never NaN/inf (all components)
# ---------------------------------------------------------------------------


@given(candidate=candidate_strategy, job=job_strategy, vectorizer=_vec_strategy)
@_PROPS
def test_inv1_scores_bounded_and_finite(candidate, job, vectorizer):
    """Every component and the total stay finite inside [0, 1]."""
    result = match(candidate, job, config=DEFAULT_CONFIG, vectorizer=vectorizer)
    _assert_finite_bounded(result)


# ---------------------------------------------------------------------------
# Invariant 2 — identical user and job skill sets -> similarity ~ 1
# ---------------------------------------------------------------------------


@_PROPS
@given(
    skills=st.lists(st.sampled_from(CANONICAL_SKILLS), min_size=1, max_size=10),
    vectorizer=_vec_strategy,
)
def test_inv2_identical_skill_sets_similarity_one(skills, vectorizer):
    """Identical non-empty canonical skill sets give cosine ~ 1.0.

    Canonical names are guaranteed to survive normalization, so the
    normalized sets are identical and non-empty.
    """
    sim = skill_similarity(skills, list(skills), vectorizer)
    assert sim == pytest.approx(1.0)


@_PROPS
@given(vectorizer=_vec_strategy)
def test_inv2_identical_inputs_through_match(vectorizer):
    """Same skills/keywords/experience on both sides -> total 1.0."""
    skills = ["Python", "Django"]
    keywords = ["Fintech"]
    candidate = CandidateInput.from_iterables(
        skills=skills,
        domain_keywords=keywords,
        total_experience_years=2.0,
    )
    job = JobInput.from_iterables(
        skills=skills,
        domain_keywords=keywords,
        experience_min_years=2.0,
    )
    result = match(candidate, job, vectorizer=vectorizer)
    assert result.total_score == pytest.approx(1.0)
    assert result.skill_similarity == pytest.approx(1.0)
    assert result.experience_match == pytest.approx(1.0)
    assert result.keyword_overlap == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Invariant 3 — disjoint skill sets -> similarity = 0
# ---------------------------------------------------------------------------


@_PROPS
@given(
    a=st.lists(st.sampled_from(HALF_A_TERMS), max_size=10),
    b=st.lists(st.sampled_from(HALF_B_TERMS), max_size=10),
    vectorizer=_vec_strategy,
)
def test_inv3_disjoint_skill_sets_similarity_zero(a, b, vectorizer):
    """Skill lists drawn from disjoint vocabulary halves score 0.0.

    Half-A and half-B terms normalize to disjoint canonical sets, so
    the cosine similarity has an empty intersection.
    """
    assert skill_similarity(a, b, vectorizer) == 0.0


# ---------------------------------------------------------------------------
# Invariant 4 — adding a job-required skill never decreases total score
# ---------------------------------------------------------------------------


def _required_skill_strategy():
    """A canonical skill plus a raw form (canonical or alias) of it."""
    return st.sampled_from(CANONICAL_SKILLS).flatmap(
        lambda canonical: st.sampled_from(_SKILL_FORMS[canonical]).map(
            lambda form: (canonical, form)
        )
    )


@_PROPS
@given(
    candidate_skills=_skill_list,
    job_base_skills=_skill_list,
    required=_required_skill_strategy(),
    domain_keywords=_keyword_list,
    total_experience_years=_yoe,
    vectorizer=_vec_strategy,
)
def test_inv4_adding_required_skill_never_decreases_total(
    candidate_skills,
    job_base_skills,
    required,
    domain_keywords,
    total_experience_years,
    vectorizer,
):
    """Appending a skill the job requires cannot lower match().total.

    The addition target is the user's profile only; the JobInput is
    identical in both match() calls (it always contains the added
    skill, so the skill is genuinely job-required after normalization).
    Only the skill signal can change; experience and keyword components
    are identical, and cosine similarity over non-negative weights is
    monotone when the added term is already present on the job side
    (the added term contributes to the dot product without decreasing
    cosine — see docs/CORRECTNESS.md).
    """
    _, added_form = required
    job_skills = list(job_base_skills) + [added_form]

    candidate = CandidateInput.from_iterables(
        skills=candidate_skills,
        domain_keywords=domain_keywords,
        total_experience_years=total_experience_years,
    )
    augmented = CandidateInput.from_iterables(
        skills=list(candidate_skills) + [added_form],
        domain_keywords=domain_keywords,
        total_experience_years=total_experience_years,
    )
    job = JobInput.from_iterables(skills=job_skills)

    base = match(candidate, job, vectorizer=vectorizer)
    new = match(augmented, job, vectorizer=vectorizer)

    assert new.experience_match == base.experience_match
    assert new.keyword_overlap == base.keyword_overlap
    assert new.skill_similarity >= base.skill_similarity - 1e-12
    assert new.total_score >= base.total_score - 1e-12


# ---------------------------------------------------------------------------
# Invariant 5 — experience match monotonic non-decreasing in user_yoe,
# capped at 1
# ---------------------------------------------------------------------------


@_PROPS
@given(
    user_yoe=_yoe,
    extra_years=st.floats(
        min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False
    ),
    req_min=_req_years,
    req_max=_req_years,
)
def test_inv5_experience_monotonic_and_capped(user_yoe, extra_years, req_min, req_max):
    """experience_match(u2) >= experience_match(u1) for u2 >= u1, in [0,1].

    ``None`` (unknown) is not ordered against numbers and is excluded
    here; it is covered by the boundary regression tests.
    """
    if user_yoe is None:
        return
    lower = experience_match(user_yoe, req_min, req_max)
    upper = experience_match(user_yoe + extra_years, req_min, req_max)
    for value in (lower, upper):
        assert math.isfinite(value)
        assert 0.0 <= value <= 1.0
    assert upper >= lower - 1e-12


@_PROPS
@given(
    req_min=st.floats(
        min_value=0.01, max_value=20.0, allow_nan=False, allow_infinity=False
    ),
    user_yoe=st.floats(
        min_value=0.0, max_value=60.0, allow_nan=False, allow_infinity=False
    ),
)
def test_inv5_experience_capped_at_one(req_min, user_yoe):
    """user_yoe >= required minimum -> experience_match == 1.0 exactly."""
    if user_yoe >= req_min:
        assert experience_match(user_yoe, req_min, None) == 1.0


# ---------------------------------------------------------------------------
# Invariant 6 — Jaccard similarity is symmetric
# ---------------------------------------------------------------------------


@_PROPS
@given(a=_keyword_list, b=_keyword_list)
def test_inv6_jaccard_symmetric(a, b):
    """Jaccard overlap is identical with arguments swapped."""
    assert keyword_overlap(a, b) == keyword_overlap(b, a)
    set_a = normalize_domain_keywords(a)
    set_b = normalize_domain_keywords(b)
    assert jaccard_similarity(set_a, set_b) == jaccard_similarity(set_b, set_a)


# ---------------------------------------------------------------------------
# Invariant 7 — skill order and duplicate entries never change the score
# ---------------------------------------------------------------------------


@_PROPS
@given(candidate=candidate_strategy, job=job_strategy, vectorizer=_vec_strategy)
def test_inv7_order_and_duplicates_never_change_score(candidate, job, vectorizer):
    """Permuting and duplicating every skill/keyword leaves MatchResult equal."""
    permuted_candidate = CandidateInput.from_iterables(
        skills=_permuted_with_duplicates(candidate.skills),
        domain_keywords=_permuted_with_duplicates(candidate.domain_keywords),
        total_experience_years=candidate.total_experience_years,
    )
    permuted_job = JobInput.from_iterables(
        skills=_permuted_with_duplicates(job.skills),
        domain_keywords=_permuted_with_duplicates(job.domain_keywords),
        experience_min_years=job.experience_min_years,
        experience_max_years=job.experience_max_years,
    )
    assert match(candidate, job, vectorizer=vectorizer) == match(
        permuted_candidate, permuted_job, vectorizer=vectorizer
    )


# ---------------------------------------------------------------------------
# Invariant 8 — score is deterministic across repeated runs
# ---------------------------------------------------------------------------


@_PROPS
@given(candidate=candidate_strategy, job=job_strategy, vectorizer=_vec_strategy)
def test_inv8_deterministic_repeated_runs(candidate, job, vectorizer):
    """Two consecutive match() calls return identical results."""
    first = match(candidate, job, vectorizer=vectorizer)
    second = match(candidate, job, vectorizer=vectorizer)
    assert first == second


@_PROPS
@given(corpus=st.lists(_skill_list, min_size=1, max_size=6))
def test_inv8_vectorizer_fit_deterministic(corpus):
    """Fitting the same corpus twice yields identical similarity scores."""
    v1 = TfidfVectorizer.fit(corpus)
    v2 = TfidfVectorizer.fit(corpus)
    skills = CANONICAL_SKILLS[:5]
    assert skill_similarity(skills, skills, v1) == skill_similarity(skills, skills, v2)


# ---------------------------------------------------------------------------
# 10,000-pair sweep — every universally checkable invariant on real
# match() calls over randomized candidate/job inputs.
# ---------------------------------------------------------------------------


@settings(
    max_examples=10_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(candidate=candidate_strategy, job=job_strategy, vectorizer=_vec_strategy)
def test_10000_pairs_invariants_hold(candidate, job, vectorizer):
    """10,000 generated candidate/job pairs through match().

    Asserts per pair: all scores finite in [0,1] (inv 1); total equals
    the SPEC weighted sum; determinism across repeat calls (inv 8);
    insensitivity to order/duplicates (inv 7); symmetry of the skill
    and keyword signals (invariants 3/6 families); and that match()
    does not mutate its inputs.
    """
    # Snapshot inputs to prove no mutation.
    cand_snapshot = (candidate.skills, candidate.domain_keywords)
    job_snapshot = (job.skills, job.domain_keywords)

    result = match(candidate, job, config=DEFAULT_CONFIG, vectorizer=vectorizer)
    _assert_finite_bounded(result)

    # Total equals the documented weighted formula.
    expected_total = (
        DEFAULT_CONFIG.skill_weight * result.skill_similarity
        + DEFAULT_CONFIG.experience_weight * result.experience_match
        + DEFAULT_CONFIG.keyword_weight * result.keyword_overlap
    )
    assert result.total_score == pytest.approx(expected_total, abs=1e-12)

    # Determinism (inv 8).
    assert result == match(candidate, job, vectorizer=vectorizer)

    # Order/duplicates (inv 7) — permute both sides independently.
    perm_cand = CandidateInput.from_iterables(
        skills=_permuted_with_duplicates(candidate.skills),
        domain_keywords=_permuted_with_duplicates(candidate.domain_keywords),
        total_experience_years=candidate.total_experience_years,
    )
    perm_job = JobInput.from_iterables(
        skills=_permuted_with_duplicates(job.skills),
        domain_keywords=_permuted_with_duplicates(job.domain_keywords),
        experience_min_years=job.experience_min_years,
        experience_max_years=job.experience_max_years,
    )
    assert result == match(perm_cand, perm_job, vectorizer=vectorizer)

    # Signal symmetry (cosine is symmetric; Jaccard is symmetric — inv 6).
    assert result.skill_similarity == pytest.approx(
        skill_similarity(job.skills, candidate.skills, vectorizer), abs=1e-12
    )
    assert result.keyword_overlap == keyword_overlap(
        job.domain_keywords, candidate.domain_keywords
    )

    # Inputs untouched.
    assert (candidate.skills, candidate.domain_keywords) == cand_snapshot
    assert (job.skills, job.domain_keywords) == job_snapshot


# ---------------------------------------------------------------------------
# Additional valid properties (SPEC/DECISIONS-consistent)
# ---------------------------------------------------------------------------


@_PROPS
@given(candidate=candidate_strategy, job=job_strategy, vectorizer=_vec_strategy)
def test_extra_irrelevant_fields_do_not_change_components(candidate, job, vectorizer):
    """Changing one signal's inputs leaves the other components fixed."""
    other_keywords = list(KEYWORD_TERM_POOL[:3])
    other_yoe = 7.5
    other_min = 3.0

    base = match(candidate, job, vectorizer=vectorizer)

    # New domain keywords change only the keyword component.
    kw_changed = match(
        CandidateInput.from_iterables(
            skills=candidate.skills,
            domain_keywords=other_keywords,
            total_experience_years=candidate.total_experience_years,
        ),
        job,
        vectorizer=vectorizer,
    )
    assert kw_changed.skill_similarity == base.skill_similarity
    assert kw_changed.experience_match == base.experience_match

    # New experience changes only the experience component.
    exp_changed = match(
        CandidateInput.from_iterables(
            skills=candidate.skills,
            domain_keywords=candidate.domain_keywords,
            total_experience_years=other_yoe,
        ),
        job,
        vectorizer=vectorizer,
    )
    assert exp_changed.skill_similarity == base.skill_similarity
    assert exp_changed.keyword_overlap == base.keyword_overlap

    # New required experience changes only the experience component.
    job_exp_changed = match(
        candidate,
        JobInput.from_iterables(
            skills=job.skills,
            domain_keywords=job.domain_keywords,
            experience_min_years=other_min,
        ),
        vectorizer=vectorizer,
    )
    assert job_exp_changed.skill_similarity == base.skill_similarity
    assert job_exp_changed.keyword_overlap == base.keyword_overlap


@_PROPS
@given(candidate_skills=_skill_list, job_skills=_skill_list, vectorizer=_vec_strategy)
def test_extra_skill_similarity_symmetric(candidate_skills, job_skills, vectorizer):
    """Cosine similarity is symmetric (up to float rounding)."""
    ab = skill_similarity(candidate_skills, job_skills, vectorizer)
    ba = skill_similarity(job_skills, candidate_skills, vectorizer)
    assert ab == pytest.approx(ba, abs=1e-12)
    assert 0.0 <= ab <= 1.0


@_PROPS
@given(term=st.sampled_from(SKILL_TERM_POOL))
def test_extra_uniform_vectorizer_weights_are_one(term):
    """UNIFORM_VECTORIZER assigns weight 1.0 to every term."""
    assert UNIFORM_VECTORIZER.term_weight(term) == 1.0
    assert not UNIFORM_VECTORIZER.is_corpus_fitted


@_PROPS
@given(corpus=st.lists(_skill_list, min_size=1, max_size=8))
def test_extra_fitted_vectorizer_distinguishable(corpus):
    """A corpus-fitted vectorizer reports is_corpus_fitted and N>0."""
    fitted = TfidfVectorizer.fit(corpus)
    assert fitted.is_corpus_fitted
    assert fitted.document_count == len(corpus)


# ---------------------------------------------------------------------------
# Regression examples for documented boundary cases
# ---------------------------------------------------------------------------


class TestBoundaryRegressionExamples:
    """Fixed examples pinning edge behavior the properties cannot express.

    These document — they do not change — Gate 1 semantics.
    """

    def test_identical_all_unknown_skill_sets_score_zero(self):
        # Both sides normalize to the empty set -> cosine({}, {}) = 0.0.
        # Invariant 2 applies to identical *meaningful* skill sets; the
        # both-empty rule (0.0) is the documented SPEC/Gate-1 behavior.
        assert skill_similarity(["UnknownSkillA"], ["UnknownSkillB"]) == 0.0

    def test_alias_forms_of_same_skill_score_one(self):
        # "js" and "JavaScript" normalize identically -> similarity 1.0.
        assert skill_similarity(["js"], ["JavaScript"]) == pytest.approx(1.0)
        assert skill_similarity(["k8s"], ["Kubernetes"]) == pytest.approx(1.0)

    def test_disjoint_canonical_halves_score_zero(self):
        a = [CANONICAL_SKILLS[0], CANONICAL_SKILLS[1]]
        b = [CANONICAL_SKILLS[-1], CANONICAL_SKILLS[-2]]
        assert skill_similarity(a, b) == 0.0

    def test_experience_boundary_cases(self):
        # required = 0 -> 1.0 for any candidate, including unknown
        assert experience_match(None, 0.0) == 1.0
        assert experience_match(0.0, 0.0, 2.0) == 1.0
        # required > 0, unknown candidate -> 0.0
        assert experience_match(None, 2.0) == 0.0
        assert experience_match(None, 2.0, 5.0) == 0.0
        # max-only range includes 0 -> 1.0 for all
        assert experience_match(None, None, 3.0) == 1.0
        # above range never penalized
        assert experience_match(10.0, 2.0, 5.0) == 1.0

    def test_jaccard_both_empty_is_zero(self):
        assert keyword_overlap([], []) == 0.0
        assert keyword_overlap(["UnknownKw"], ["OtherUnknown"]) == 0.0

    def test_match_does_not_mutate_tuple_inputs(self):
        candidate = CandidateInput(
            skills=("Python", "Django"),
            domain_keywords=("Fintech",),
            total_experience_years=1.0,
        )
        job = JobInput(
            skills=("Python",),
            experience_min_years=1.0,
        )
        before = (candidate.skills, candidate.domain_keywords, job.skills)
        match(candidate, job, vectorizer=UNIFORM_VECTORIZER)
        assert (candidate.skills, candidate.domain_keywords, job.skills) == before


class TestDefect1CosineClampRegression:
    """Regression tests for DEFECT-1 (approved fix, Gate 3 follow-up).

    ``cosine_similarity`` could return ``1.0000000000000002`` for
    identical vectors due to IEEE-754 rounding of
    ``dot / (norm1 * norm2)``, which made ``match()`` raise
    ``ValueError`` in ``MatchResult.__post_init__``. The fix clamps the
    cosine result to its mathematical range [0, 1]. These tests pin the
    reported reproduction and the boundary behavior; mathematically
    equivalent results use ``pytest.approx`` rather than exact equality.
    """

    REPORTED_SKILLS = ["Python", "Django", "React"]

    def test_reported_reproduction_similarity(self):
        # Exact DEFECT-1 report: identical 3-skill set, uniform weights.
        sim = skill_similarity(
            self.REPORTED_SKILLS, self.REPORTED_SKILLS, UNIFORM_VECTORIZER
        )
        assert 0.0 <= sim <= 1.0
        assert sim == pytest.approx(1.0)

    def test_reported_reproduction_match_returns(self):
        # match() must return a result, not raise ValueError.
        candidate = CandidateInput.from_iterables(skills=self.REPORTED_SKILLS)
        job = JobInput.from_iterables(skills=self.REPORTED_SKILLS)
        result = match(candidate, job, vectorizer=UNIFORM_VECTORIZER)
        assert result.skill_similarity == pytest.approx(1.0)
        assert 0.0 <= result.total_score <= 1.0

    def test_identical_skill_sets_across_sizes_and_combos(self):
        # Every identical canonical combination of sizes 1-5 must score
        # ~1.0 and never leave [0, 1], under both vectorizer states.
        sample = CANONICAL_SKILLS[:10]
        for size in range(1, 6):
            for combo in itertools.combinations(sample, size):
                skills = list(combo)
                for vectorizer in (UNIFORM_VECTORIZER, FITTED_VECTORIZER):
                    sim = skill_similarity(skills, skills, vectorizer)
                    assert 0.0 <= sim <= 1.0
                    assert sim == pytest.approx(1.0)

    def test_identical_skill_sets_match_bounded(self):
        # Identical skill sets through match(): all components finite,
        # bounded, and skill signal ~1.0 for every sampled combo.
        sample = CANONICAL_SKILLS[:8]
        for size in range(1, 5):
            for combo in itertools.combinations(sample, size):
                skills = list(combo)
                result = match(
                    CandidateInput.from_iterables(skills=skills),
                    JobInput.from_iterables(skills=skills),
                    vectorizer=UNIFORM_VECTORIZER,
                )
                for value in (
                    result.total_score,
                    result.skill_similarity,
                    result.experience_match,
                    result.keyword_overlap,
                ):
                    assert math.isfinite(value)
                    assert 0.0 <= value <= 1.0
                assert result.skill_similarity == pytest.approx(1.0)

    def test_disjoint_skill_sets_still_zero(self):
        a = ["Python", "Django", "React"]
        b = ["Kubernetes", "Terraform", "AWS"]
        for vectorizer in (UNIFORM_VECTORIZER, FITTED_VECTORIZER):
            assert skill_similarity(a, b, vectorizer) == 0.0
            assert skill_similarity(b, a, vectorizer) == 0.0

    def test_cosine_similarity_within_bounds_for_reported_vectors(self):
        # Direct cosine_similarity on the vectors behind the repro:
        # three unit-weight terms on each side.
        vec = {"Python": 1.0, "Django": 1.0, "React": 1.0}
        for v1, v2 in ((vec, vec), (vec, {"Go": 1.0}), ({}, vec)):
            sim = cosine_similarity(v1, v2)
            assert 0.0 <= sim <= 1.0


class TestInvariant4Directionality:
    """Pin the exact scope of invariant 4 (Gate 3 audit).

    Playbook wording: "Adding a skill the job requires to the user's
    profile never decreases the total score." The addition target is
    the *user's profile*; the job is held fixed. These tests document
    both directions of cosine behavior so the invariant's boundary is
    explicit:

    - Profile-side addition of a job-required skill: total does NOT
      decrease (the invariant — verified exhaustively by
      ``test_inv4_adding_required_skill_never_decreases_total``).
    - Job-side growth of required skills: similarity CAN decrease
      (cosine normalization dilutes the candidate vector). This is NOT
      a violation — the playbook does not claim monotonicity for
      job-side changes — but it is pinned here so the boundary is
      regression-tested rather than assumed.
    """

    def test_profile_side_addition_of_required_skill_never_decreases(self):
        # Literal invariant-4 scenario, concrete numbers:
        # candidate {Python}, job {Python, React}.
        job = JobInput.from_iterables(skills=["Python", "React"])
        before = match(
            CandidateInput.from_iterables(skills=["Python"]),
            job,
            vectorizer=UNIFORM_VECTORIZER,
        )
        # Add "React" — a skill the job requires — to the profile.
        after = match(
            CandidateInput.from_iterables(skills=["Python", "React"]),
            job,
            vectorizer=UNIFORM_VECTORIZER,
        )
        assert after.skill_similarity == pytest.approx(1.0)
        assert after.total_score >= before.total_score
        # Measured: 0.7071 -> 1.0 skill sim; total 0.6536 -> 0.80.
        assert before.skill_similarity == pytest.approx(1 / math.sqrt(2))

    def test_job_side_skill_growth_can_decrease_similarity(self):
        # Counterexample audit: growing the JOB's skill set reduces the
        # candidate's similarity — cosine normalization, not a bug.
        candidate = ["Python"]
        sim_small_job = skill_similarity(candidate, ["Python"], UNIFORM_VECTORIZER)
        sim_large_job = skill_similarity(
            candidate, ["Python", "React"], UNIFORM_VECTORIZER
        )
        assert sim_small_job == pytest.approx(1.0)
        assert sim_large_job == pytest.approx(1 / math.sqrt(2))
        assert sim_large_job < sim_small_job
        # Pinned through match() as well: total drops with the job's
        # extra unrelated requirement (experience/keywords unchanged).
        cand = CandidateInput.from_iterables(skills=candidate)
        total_a = match(
            cand,
            JobInput.from_iterables(skills=["Python"]),
            vectorizer=UNIFORM_VECTORIZER,
        ).total_score
        total_b = match(
            cand,
            JobInput.from_iterables(skills=["Python", "React"]),
            vectorizer=UNIFORM_VECTORIZER,
        ).total_score
        assert total_b < total_a
