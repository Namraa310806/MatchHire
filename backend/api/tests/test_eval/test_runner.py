"""Tests for the evaluation runner: ranking, ordering assertions,
determinism, fitted-vectorizer use, and metric sanity."""

from pathlib import Path

import pytest

from api.matching import UNIFORM_VECTORIZER
from eval.dataset import load_dataset, relevance_for
from eval.runner import (
    evaluate,
    evaluate_candidate,
    fit_job_corpus_vectorizer,
    rank_jobs_for_candidate,
    to_candidate_input,
    to_job_input,
)

DATASET_DIR = Path(__file__).resolve().parents[3] / "eval"


@pytest.fixture(scope="module")
def dataset():
    return load_dataset(DATASET_DIR)


@pytest.fixture(scope="module")
def vectorizer(dataset):
    return fit_job_corpus_vectorizer(dataset.jobs)


@pytest.fixture(scope="module")
def report(dataset, vectorizer):
    return evaluate(dataset, vectorizer=vectorizer)


def _rank_map(result) -> dict[str, int]:
    return {r.job_id: i for i, r in enumerate(result.ranked)}


class TestFittedVectorizer:
    def test_corpus_fitted_not_uniform(self, vectorizer):
        assert vectorizer.is_corpus_fitted
        assert vectorizer is not UNIFORM_VECTORIZER
        assert vectorizer.document_count == 60

    def test_report_records_vectorizer(self, report):
        assert report["vectorizer"]["type"] == "corpus-fitted"
        assert report["vectorizer"]["is_corpus_fitted"] is True

    def test_fitted_differs_from_uniform_on_dataset(self, dataset):
        # Corpus-fitted IDF must actually change at least one score vs
        # uniform weights somewhere in the dataset.
        cand = next(c for c in dataset.candidates if c.candidate_id == "c01_ml_fresher")
        vec = fit_job_corpus_vectorizer(dataset.jobs)
        fitted = rank_jobs_for_candidate(cand, dataset.jobs, vec)
        uniform = rank_jobs_for_candidate(cand, dataset.jobs, UNIFORM_VECTORIZER)
        fitted_scores = {r.job_id: r.skill_similarity for r in fitted}
        uniform_scores = {r.job_id: r.skill_similarity for r in uniform}
        assert fitted_scores != uniform_scores


class TestOrderingAssertions:
    """Playbook sanity suite: domain-appropriate jobs must outrank
    clearly off-domain jobs for archetype candidates."""

    def test_ml_fresher_ml_intern_above_devops(self, dataset, vectorizer):
        cand = next(c for c in dataset.candidates if c.candidate_id == "c01_ml_fresher")
        ranks = _rank_map(evaluate_candidate(dataset, cand, vectorizer))
        # j01 = ML Engineering Intern (label 2), j29 = DevOps Engineer (label 0)
        assert relevance_for(dataset, "c01_ml_fresher", "j01") == 2
        assert relevance_for(dataset, "c01_ml_fresher", "j29") == 0
        assert ranks["j01"] < ranks["j29"]

    def test_ml_fresher_data_scientist_above_vlsi(self, dataset, vectorizer):
        cand = next(c for c in dataset.candidates if c.candidate_id == "c01_ml_fresher")
        ranks = _rank_map(evaluate_candidate(dataset, cand, vectorizer))
        # j02 = Data Scientist (label 2), j45 = VLSI Design Engineer (label 0)
        assert relevance_for(dataset, "c01_ml_fresher", "j02") == 2
        assert relevance_for(dataset, "c01_ml_fresher", "j45") == 0
        assert ranks["j02"] < ranks["j45"]

    def test_vlsi_profile_semiconductor_above_web(self, dataset, vectorizer):
        cand = next(c for c in dataset.candidates if c.candidate_id == "c04_vlsi_embedded")
        ranks = _rank_map(evaluate_candidate(dataset, cand, vectorizer))
        # j46 = Embedded Software Engineer vs j11 = React Developer
        assert relevance_for(dataset, "c04_vlsi_embedded", "j46") == 2
        assert relevance_for(dataset, "c04_vlsi_embedded", "j11") == 0
        assert ranks["j46"] < ranks["j11"]

    def test_devops_profile_devops_above_ml(self, dataset, vectorizer):
        cand = next(c for c in dataset.candidates if c.candidate_id == "c03_devops_engineer")
        ranks = _rank_map(evaluate_candidate(dataset, cand, vectorizer))
        # j29 = DevOps Engineer (label 2) vs j01 = ML Intern (label 0/1)
        assert relevance_for(dataset, "c03_devops_engineer", "j29") == 2
        assert ranks["j29"] < ranks["j01"]

    def test_frontend_fresher_react_above_embedded(self, dataset, vectorizer):
        cand = next(
            c for c in dataset.candidates if c.candidate_id == "c02_frontend_react_fresher"
        )
        ranks = _rank_map(evaluate_candidate(dataset, cand, vectorizer))
        assert relevance_for(dataset, "c02_frontend_react_fresher", "j11") == 2
        assert relevance_for(dataset, "c02_frontend_react_fresher", "j45") == 0
        assert ranks["j11"] < ranks["j45"]


class TestDeterminismAndContract:
    def test_evaluate_is_deterministic(self, dataset, vectorizer):
        r1 = evaluate(dataset, vectorizer=vectorizer)
        r2 = evaluate(dataset, vectorizer=vectorizer)
        assert r1 == r2

    def test_ranking_tie_break_is_stable(self, dataset, vectorizer):
        # Re-rank twice; identical job_ids in identical order
        cand = dataset.candidates[0]
        r1 = rank_jobs_for_candidate(cand, dataset.jobs, vectorizer)
        r2 = rank_jobs_for_candidate(cand, dataset.jobs, vectorizer)
        assert [r.job_id for r in r1] == [r.job_id for r in r2]
        # tie-break: equal scores must be ordered by job_id ascending
        scores = [(r.total_score, r.job_id) for r in r1]
        for i in range(len(scores) - 1):
            s1, j1 = scores[i]
            s2, j2 = scores[i + 1]
            assert s1 > s2 or (s1 == s2 and j1 < j2)

    def test_needs_review_pairs_excluded(self, dataset, vectorizer):
        cand = next(c for c in dataset.candidates if c.candidate_id == "c10_fullstack_unknown")
        result = evaluate_candidate(dataset, cand, vectorizer)
        assert result.needs_review_excluded >= 1  # c10/j27 is needs-review
        excluded_ids = {"j27"}
        ranked_ids = {r.job_id for r in result.ranked}
        assert not (ranked_ids & excluded_ids)
        # all relevances are ints (no None)
        assert all(isinstance(r, int) for r in result.relevances)

    def test_scores_in_bounds(self, dataset, vectorizer):
        for cand in dataset.candidates:
            result = evaluate_candidate(dataset, cand, vectorizer)
            for r in result.ranked:
                assert 0.0 <= r.total_score <= 1.0
                assert 0.0 <= r.skill_similarity <= 1.0
                assert 0.0 <= r.experience_match <= 1.0
                assert 0.0 <= r.keyword_overlap <= 1.0

    def test_input_adapters_match_contract(self, dataset):
        cand = dataset.candidates[0]
        job = dataset.jobs[0]
        ci = to_candidate_input(cand)
        ji = to_job_input(job)
        assert ci.skills == cand.skills
        assert ji.skills == job.skills
        assert ji.experience_min_years == job.experience_min_years

    def test_candidate_with_no_relevant_jobs(self, dataset, vectorizer):
        # c04_vlsi_embedded vs web/frontend jobs are all label 0 —
        # verify metrics still produce sane values for that candidate
        cand = next(c for c in dataset.candidates if c.candidate_id == "c04_vlsi_embedded")
        result = evaluate_candidate(dataset, cand, vectorizer)
        # There ARE relevant jobs (embedded/vlsi) so ndcg is not None
        assert result.ndcg_at_10 is not None
        # But precision at bottom of ranking must be low
        tail = result.relevances[-5:]
        assert sum(1 for r in tail if r >= 1) <= 2

    def test_report_structure(self, report):
        assert report["dataset"]["candidates"] == 10
        assert report["dataset"]["jobs"] == 60
        agg = report["aggregate"]
        for key in ("precision@5", "precision@10", "ndcg@10", "mrr", "candidates"):
            assert key in agg
        assert len(report["per_candidate"]) == 10
        for row in report["per_candidate"]:
            assert set(row) >= {
                "candidate_id",
                "precision@5",
                "precision@10",
                "ndcg@10",
                "reciprocal_rank",
                "needs_review_excluded",
            }
