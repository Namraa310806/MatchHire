"""Tests for TF-IDF skill similarity and domain-keyword overlap."""

import math

import pytest

from api.matching.keywords import (
    jaccard_similarity,
    keyword_overlap,
    normalize_domain_keywords,
)
from api.matching.tfidf import (
    UNIFORM_VECTORIZER,
    TfidfVectorizer,
    cosine_similarity,
    normalize_skill_names,
    skill_similarity,
)


class TestSkillNormalization:
    def test_canonical_names_pass_through(self):
        assert normalize_skill_names(["Python", "React"]) == frozenset(
            {"Python", "React"}
        )

    def test_aliases_resolve_to_canonical(self):
        assert normalize_skill_names(["js", "k8s", "py"]) == frozenset(
            {"JavaScript", "Kubernetes", "Python"}
        )

    def test_case_insensitive(self):
        assert normalize_skill_names(["PYTHON", "javascript"]) == frozenset(
            {"Python", "JavaScript"}
        )

    def test_whitespace_trimmed(self):
        assert normalize_skill_names(["  Python  "]) == frozenset({"Python"})

    def test_duplicates_collapse(self):
        assert normalize_skill_names(["Python", "python", "py", "Python"]) == frozenset(
            {"Python"}
        )

    def test_unknown_terms_dropped(self):
        assert normalize_skill_names(["Python", "NotARealSkill123"]) == frozenset(
            {"Python"}
        )

    def test_unicode_terms_ignored_not_errors(self):
        # Non-vocabulary unicode is dropped like any unknown term
        assert normalize_skill_names(["Pythön", "Python"]) == frozenset({"Python"})

    def test_non_string_rejected(self):
        with pytest.raises(TypeError):
            normalize_skill_names(["Python", 42])  # type: ignore[list-item]


class TestCosineSimilarity:
    def test_identical_vectors(self):
        assert cosine_similarity({"a": 1.0}, {"a": 1.0}) == pytest.approx(1.0)

    def test_disjoint_vectors(self):
        assert cosine_similarity({"a": 1.0}, {"b": 1.0}) == 0.0

    def test_empty_vector_returns_zero(self):
        assert cosine_similarity({}, {"a": 1.0}) == 0.0
        assert cosine_similarity({"a": 1.0}, {}) == 0.0
        assert cosine_similarity({}, {}) == 0.0

    def test_partial_overlap(self):
        # {a,b} vs {a,c}: dot=1, norms sqrt(2)*sqrt(2) -> 0.5
        assert cosine_similarity({"a": 1.0, "b": 1.0}, {"a": 1.0, "c": 1.0}) == (
            pytest.approx(0.5)
        )


class TestSkillSimilarity:
    def test_identical_skill_sets(self):
        skills = ["Python", "Django", "PostgreSQL"]
        assert skill_similarity(skills, skills) == pytest.approx(1.0)

    def test_disjoint_skill_sets(self):
        assert skill_similarity(["Python"], ["Kubernetes"]) == 0.0

    def test_empty_candidate_skills(self):
        assert skill_similarity([], ["Python"]) == 0.0

    def test_empty_job_skills(self):
        assert skill_similarity(["Python"], []) == 0.0

    def test_both_empty(self):
        assert skill_similarity([], []) == 0.0

    def test_partial_overlap_binary(self):
        # candidate {Python, Django}, job {Python, React}
        # cosine = 1 / sqrt(2*2) = 0.5 with uniform weights
        assert skill_similarity(
            ["Python", "Django"], ["Python", "React"]
        ) == pytest.approx(0.5)

    def test_duplicates_do_not_change_score(self):
        once = skill_similarity(["Python", "Django"], ["Python", "React"])
        dup = skill_similarity(
            ["Python", "python", "py", "Django", "Django"],
            ["Python", "React", "react"],
        )
        assert once == dup

    def test_order_does_not_change_score(self):
        a = skill_similarity(["Python", "Django", "React"], ["Python", "Go"])
        b = skill_similarity(["React", "Python", "Django"], ["Go", "Python"])
        assert a == b

    def test_aliases_match_canonical(self):
        # "js" on one side, "JavaScript" on the other -> identical sets
        assert skill_similarity(["js"], ["JavaScript"]) == pytest.approx(1.0)

    def test_unicode_input(self):
        # Unicode that is not a vocabulary term is ignored, not an error
        assert skill_similarity(["Python", ""], ["Python"]) == pytest.approx(1.0)

    def test_very_long_skill_lists(self):
        many = [f"Skill{i}" for i in range(2000)] + ["Python"]
        # Unknown terms dropped; only Python counts -> identical to ["Python"]
        assert skill_similarity(many, ["Python"]) == pytest.approx(1.0)

    def test_no_nan_or_inf(self):
        for cand, job in [
            ([], []),
            (["Python"], []),
            ([], ["Python"]),
            (["Python"], ["Kubernetes"]),
        ]:
            score = skill_similarity(cand, job)
            assert math.isfinite(score)
            assert 0.0 <= score <= 1.0

    def test_deterministic(self):
        cand, job = ["Python", "Django"], ["Python", "React", "PostgreSQL"]
        assert skill_similarity(cand, job) == skill_similarity(cand, job)


class TestTfidfVectorizer:
    def test_uniform_vectorizer_weights(self):
        assert not UNIFORM_VECTORIZER.is_corpus_fitted
        vec = {t: UNIFORM_VECTORIZER.term_weight(t) for t in ["Python", "Go"]}
        assert vec == {"Python": 1.0, "Go": 1.0}

    def test_fit_marks_corpus_fitted(self):
        vec = TfidfVectorizer.fit([["Python"], ["Go"]])
        assert vec.is_corpus_fitted
        assert vec.document_count == 2

    def test_empty_corpus_fit_is_uniform_and_unfitted(self):
        vec = TfidfVectorizer.fit([])
        assert vec.document_count == 0
        assert not vec.is_corpus_fitted
        assert vec.term_weight("Anything") == pytest.approx(1.0)

    def test_fit_computes_idf(self):
        # Corpus: Python in all 2 docs, Go in 1 doc
        vec = TfidfVectorizer.fit([["Python", "Go"], ["Python", "Django"]])
        assert vec.document_count == 2
        python_w = vec.term_weight("Python")
        go_w = vec.term_weight("Go")
        unseen_w = vec.term_weight("Rust")
        # Rarer terms get higher weight
        assert go_w > python_w
        assert unseen_w > go_w  # df=0 -> max smooth idf

    def test_fit_normalizes_corpus_aliases(self):
        vec = TfidfVectorizer.fit([["js"], ["JavaScript"]])
        # Both docs contain canonical JavaScript -> df=2
        assert vec.doc_freq.get("JavaScript") == 2

    def test_transform_uses_weights(self):
        vec = TfidfVectorizer.fit([["Python"], ["Python"], ["Go"]])
        v = vec.transform(["Python", "Go"])
        assert v["Python"] < v["Go"]
        assert set(v) == {"Python", "Go"}

    def test_corpus_fitted_idf_changes_similarity(self):
        # Corpus: Python is common (in 9/10 docs), Go is rare (1/10).
        # Candidate {Python, Go} vs job {Go}: the rare Go match should
        # weigh more under fitted IDF than under uniform weights.
        corpus = [["Python"]] * 9 + [["Go"]]
        fitted = TfidfVectorizer.fit(corpus)
        cand, job = ["Python", "Go"], ["Go"]
        fitted_score = skill_similarity(cand, job, fitted)
        uniform_score = skill_similarity(cand, job, UNIFORM_VECTORIZER)
        assert fitted_score > uniform_score
        # Deterministic across runs
        assert skill_similarity(cand, job, fitted) == fitted_score

    def test_fitted_vectorizer_deterministic(self):
        fitted = TfidfVectorizer.fit([["Python", "Go"], ["Python"], ["Django"]])
        cand, job = ["Python", "Go"], ["Python", "Django"]
        assert skill_similarity(cand, job, fitted) == skill_similarity(
            cand, job, fitted
        )


class TestKeywordNormalization:
    def test_canonical_names(self):
        assert normalize_domain_keywords(["Fintech", "DevOps"]) == frozenset(
            {"Fintech", "DevOps"}
        )

    def test_aliases_resolve(self):
        assert normalize_domain_keywords(["ml", "financial technology"]) == frozenset(
            {"Machine Learning", "Fintech"}
        )

    def test_case_insensitive(self):
        assert normalize_domain_keywords(["FINTECH", "devops"]) == frozenset(
            {"Fintech", "DevOps"}
        )

    def test_unknown_terms_dropped(self):
        assert normalize_domain_keywords(["Fintech", "Underwater Basket Weaving"]) == (
            frozenset({"Fintech"})
        )

    def test_duplicates_collapse(self):
        assert normalize_domain_keywords(["Fintech", "fintech", "financial technology"]) == (
            frozenset({"Fintech"})
        )

    def test_non_string_rejected(self):
        with pytest.raises(TypeError):
            normalize_domain_keywords(["Fintech", None])  # type: ignore[list-item]


class TestJaccardSimilarity:
    def test_identical_sets(self):
        assert jaccard_similarity(frozenset({"a"}), frozenset({"a"})) == 1.0

    def test_disjoint_sets(self):
        assert jaccard_similarity(frozenset({"a"}), frozenset({"b"})) == 0.0

    def test_partial_overlap(self):
        assert jaccard_similarity(
            frozenset({"a", "b"}), frozenset({"b", "c"})
        ) == pytest.approx(1 / 3)

    def test_both_empty_is_zero(self):
        # Explicit rule: both empty -> 0.0 (documented decision)
        assert jaccard_similarity(frozenset(), frozenset()) == 0.0

    def test_one_empty_is_zero(self):
        assert jaccard_similarity(frozenset({"a"}), frozenset()) == 0.0
        assert jaccard_similarity(frozenset(), frozenset({"a"})) == 0.0

    def test_symmetric(self):
        a, b = frozenset({"a", "b", "c"}), frozenset({"b", "c", "d"})
        assert jaccard_similarity(a, b) == jaccard_similarity(b, a)


class TestKeywordOverlap:
    def test_overlap(self):
        score = keyword_overlap(["Fintech", "DevOps"], ["Fintech", "SaaS"])
        assert score == pytest.approx(1 / 3)

    def test_both_empty(self):
        assert keyword_overlap([], []) == 0.0

    def test_one_empty(self):
        assert keyword_overlap(["Fintech"], []) == 0.0

    def test_alias_normalization_before_jaccard(self):
        # "ml" resolves to "Machine Learning" -> identical sets -> 1.0
        assert keyword_overlap(["ml"], ["Machine Learning"]) == 1.0

    def test_deterministic(self):
        a = keyword_overlap(["Fintech", "DevOps"], ["Fintech", "SaaS"])
        b = keyword_overlap(["Fintech", "DevOps"], ["Fintech", "SaaS"])
        assert a == b
