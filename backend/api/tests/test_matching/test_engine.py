"""Tests for the match() engine: weighted total, bounds, determinism."""

import math
from dataclasses import FrozenInstanceError

import pytest

from api.matching import (
    DEFAULT_CONFIG,
    UNIFORM_VECTORIZER,
    CandidateInput,
    JobInput,
    MatchConfig,
    TfidfVectorizer,
    match,
)
from api.matching.engine import MatchResult


def _candidate(**kwargs) -> CandidateInput:
    return CandidateInput.from_iterables(**kwargs)


def _job(**kwargs) -> JobInput:
    return JobInput.from_iterables(**kwargs)


def score(candidate, job, config=DEFAULT_CONFIG, vectorizer=UNIFORM_VECTORIZER):
    """match() with the explicit uniform vectorizer (test convenience)."""
    return match(candidate, job, config=config, vectorizer=vectorizer)


class TestVectorizerContract:
    def test_vectorizer_is_required(self):
        # match() must not silently default to uniform weights
        with pytest.raises(TypeError):
            match(_candidate(), _job())  # type: ignore[call-arg]

    def test_uniform_vectorizer_is_explicitly_unfitted(self):
        assert not UNIFORM_VECTORIZER.is_corpus_fitted
        assert UNIFORM_VECTORIZER.document_count == 0
        assert UNIFORM_VECTORIZER.term_weight("Python") == 1.0

    def test_fitted_vectorizer_changes_engine_score(self):
        # Python common, Go rare in the corpus -> matching Go weighs more
        fitted = TfidfVectorizer.fit([["Python"]] * 9 + [["Go"]])
        cand = _candidate(skills=["Python", "Go"])
        job = _job(skills=["Go"])
        uniform_result = score(cand, job)
        fitted_result = score(cand, job, vectorizer=fitted)
        assert fitted_result.skill_similarity > uniform_result.skill_similarity
        # Other components unchanged
        assert fitted_result.experience_match == uniform_result.experience_match
        assert fitted_result.keyword_overlap == uniform_result.keyword_overlap

    def test_fitted_vectorizer_deterministic_in_engine(self):
        fitted = TfidfVectorizer.fit([["Python", "Go"], ["Python"], ["Django"]])
        cand = _candidate(skills=["Python", "Go"], total_experience_years=1.0)
        job = _job(skills=["Python", "Django"], experience_min_years=1.0)
        assert score(cand, job, vectorizer=fitted) == score(
            cand, job, vectorizer=fitted
        )


class TestWeightedTotal:
    def test_spec_formula(self):
        # Identical everything -> all components 1.0 -> total 1.0
        cand = _candidate(
            skills=["Python", "Django"],
            domain_keywords=["Fintech"],
            total_experience_years=2.0,
        )
        job = _job(
            skills=["Python", "Django"],
            domain_keywords=["Fintech"],
            experience_min_years=2.0,
        )
        result = score(cand, job)
        assert result.total_score == pytest.approx(1.0)
        assert result.skill_similarity == pytest.approx(1.0)
        assert result.experience_match == pytest.approx(1.0)
        assert result.keyword_overlap == pytest.approx(1.0)

    def test_weighted_sum(self):
        cand = _candidate(
            skills=["Python", "Django"],
            domain_keywords=["Fintech"],
            total_experience_years=1.0,
        )
        job = _job(
            skills=["Python", "React"],
            domain_keywords=["Fintech", "SaaS"],
            experience_min_years=2.0,
        )
        result = score(cand, job)
        expected = (
            0.50 * result.skill_similarity
            + 0.30 * result.experience_match
            + 0.20 * result.keyword_overlap
        )
        assert result.total_score == pytest.approx(expected)

    def test_zero_everything(self):
        result = score(_candidate(), _job())
        # skills 0, experience 1.0 (no requirement), keywords 0
        assert result.skill_similarity == 0.0
        assert result.experience_match == 1.0
        assert result.keyword_overlap == 0.0
        assert result.total_score == pytest.approx(0.30)

    def test_custom_config_changes_total(self):
        cand = _candidate(skills=["Python"], domain_keywords=["Fintech"])
        job = _job(skills=["Kubernetes"], domain_keywords=["Fintech"])
        default = score(cand, job)
        skill_only = MatchConfig(
            skill_weight=0.0, experience_weight=0.0, keyword_weight=1.0
        )
        result = score(cand, job, config=skill_only)
        # skill signal disjoint -> 0; keyword identical -> 1.0
        assert result.skill_similarity == 0.0
        assert result.keyword_overlap == 1.0
        assert result.total_score == pytest.approx(1.0)
        assert default.total_score != result.total_score


class TestResultContract:
    def test_result_fields(self):
        result = score(_candidate(skills=["Python"]), _job(skills=["Python"]))
        assert isinstance(result, MatchResult)
        assert result.total_score == pytest.approx(0.5 + 0.3)
        assert result.skill_similarity == pytest.approx(1.0)
        assert result.experience_match == pytest.approx(1.0)
        assert result.keyword_overlap == 0.0

    def test_result_is_frozen(self):
        result = score(_candidate(), _job())
        with pytest.raises(FrozenInstanceError):
            result.total_score = 0.5  # type: ignore[misc]

    def test_result_rejects_out_of_range(self):
        with pytest.raises(ValueError, match=r"\[0\.0, 1\.0\]"):
            MatchResult(
                total_score=1.5,
                skill_similarity=0.5,
                experience_match=0.5,
                keyword_overlap=0.5,
            )

    def test_result_rejects_nan(self):
        with pytest.raises(ValueError, match="finite"):
            MatchResult(
                total_score=math.nan,
                skill_similarity=0.5,
                experience_match=0.5,
                keyword_overlap=0.5,
            )


class TestEdgeCases:
    def test_empty_inputs_no_nan(self):
        result = score(CandidateInput(), JobInput())
        assert math.isfinite(result.total_score)
        assert 0.0 <= result.total_score <= 1.0

    def test_long_inputs(self):
        cand = _candidate(skills=[f"zzz_not_a_skill_{i}" for i in range(500)] + ["Python"])
        job = _job(skills=["Python"])
        result = score(cand, job)
        assert result.skill_similarity == pytest.approx(1.0)

    def test_unicode_inputs(self):
        result = score(
            _candidate(skills=["Python", ""], domain_keywords=["Fintech"]),
            _job(skills=["Python"], domain_keywords=["Fintech"]),
        )
        assert math.isfinite(result.total_score)

    def test_duplicate_inputs(self):
        once = score(
            _candidate(skills=["Python", "Django"], domain_keywords=["Fintech"]),
            _job(skills=["Python"], domain_keywords=["Fintech"]),
        )
        dup = score(
            _candidate(
                skills=["Python", "python", "py", "Django"],
                domain_keywords=["Fintech", "fintech"],
            ),
            _job(skills=["Python", "Python"], domain_keywords=["Fintech"]),
        )
        assert once == dup

    def test_deterministic_repeated_runs(self):
        cand = _candidate(
            skills=["Python", "Django", "React"],
            domain_keywords=["Fintech", "DevOps"],
            total_experience_years=1.5,
        )
        job = _job(
            skills=["Python", "Django"],
            domain_keywords=["Fintech"],
            experience_min_years=2.0,
            experience_max_years=5.0,
        )
        assert score(cand, job) == score(cand, job) == score(cand, job)

    def test_scores_always_in_bounds(self):
        cases = [
            (_candidate(), _job()),
            (
                _candidate(skills=["Python"], total_experience_years=None),
                _job(skills=["Python"], experience_min_years=5.0),
            ),
            (
                _candidate(
                    skills=["Python", "Go", "Rust"],
                    domain_keywords=["Fintech", "DevOps", "SaaS"],
                    total_experience_years=0.0,
                ),
                _job(
                    skills=["Python", "Kubernetes"],
                    domain_keywords=["Fintech"],
                    experience_min_years=0.0,
                    experience_max_years=2.0,
                ),
            ),
        ]
        for cand, job in cases:
            result = score(cand, job)
            for s in (
                result.total_score,
                result.skill_similarity,
                result.experience_match,
                result.keyword_overlap,
            ):
                assert math.isfinite(s)
                assert 0.0 <= s <= 1.0

    def test_experience_null_vs_zero_distinction(self):
        job = _job(experience_min_years=2.0)
        unknown = score(_candidate(total_experience_years=None), job)
        explicit_zero = score(_candidate(total_experience_years=0.0), job)
        # Both are 0.0 component-wise here, but the inputs are distinct
        assert unknown.experience_match == explicit_zero.experience_match == 0.0

        fresher_job = _job(experience_min_years=0.0)
        # With required=0, null and 0 both score 1.0 per SPEC
        assert score(_candidate(total_experience_years=None), fresher_job).experience_match == 1.0
        assert score(_candidate(total_experience_years=0.0), fresher_job).experience_match == 1.0

    def test_tuple_inputs_accepted_directly(self):
        result = score(
            CandidateInput(skills=("Python",), total_experience_years=1.0),
            JobInput(skills=("Python",), experience_min_years=1.0),
        )
        # skills 1.0 * 0.5 + experience 1.0 * 0.3 + keywords 0.0 * 0.2 = 0.8
        assert result.total_score == pytest.approx(0.8)

    def test_default_config_is_spec_weights(self):
        assert DEFAULT_CONFIG.skill_weight == 0.5
        assert DEFAULT_CONFIG.experience_weight == 0.3
        assert DEFAULT_CONFIG.keyword_weight == 0.2


class TestDocumentationWorkedExample:
    """The 'Concrete Worked Example' in MatchHire_Documentation_FINAL.pdf.

    The document reports raw component scores 0.78 / 1.00 / 0.60 for a
    total of 81%. Those numbers were produced by sklearn's
    TfidfVectorizer over raw text and raw keyword terms — a different
    input representation than this engine's canonical skill/keyword
    sets. They do NOT reproduce here and are not asserted. This test
    pins the actual contract-consistent outputs for the same logical
    inputs instead.
    """

    def test_worked_example_inputs(self):
        cand = _candidate(
            skills=["Python", "Django", "SQL", "Redis"],
            domain_keywords=["backend", "REST", "Django"],
            total_experience_years=0.8,
        )
        job = _job(
            skills=["Python", "FastAPI", "PostgreSQL", "Redis"],
            domain_keywords=["backend", "microservices", "REST"],
            experience_min_years=0.0,
            experience_max_years=1.0,
        )
        result = score(cand, job)
        # Binary cosine over {Python,Django,SQL,Redis} vs
        # {Python,FastAPI,PostgreSQL,Redis}: |∩|=2, sqrt(4*4) -> 0.5
        assert result.skill_similarity == pytest.approx(0.5)
        # "0-1 year" range includes 0 -> 1.0 for any candidate
        assert result.experience_match == pytest.approx(1.0)
        # Only "Microservices" is a domain keyword; "backend", "REST",
        # "Django" are not in the fixed vocabulary -> one-sided -> 0.0
        assert result.keyword_overlap == 0.0
        # 0.5*0.5 + 1.0*0.3 + 0.0*0.2 = 0.55 (doc claims 0.81 via sklearn)
        assert result.total_score == pytest.approx(0.55)
