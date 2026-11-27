"""Tests pinning the documented aggregation semantics:
macro-averaging, grade>=1 relevance, nDCG graded gains,
zero-relevant-candidate handling, needs-review exclusion."""

from pathlib import Path

import pytest

from eval import metrics
from eval.dataset import EvalCandidate, EvalDataset, EvalJob, EvalLabel
from eval.runner import evaluate_candidate, fit_job_corpus_vectorizer

DATASET_DIR = Path(__file__).resolve().parents[3] / "eval"


def _mini_dataset() -> EvalDataset:
    """2 candidates x 4 jobs with hand-set labels.

    c_good: labels [2,1,0,0] -> relevant jobs exist
    c_none: labels [0,0,0,0] -> zero relevant jobs
    """
    candidates = (
        EvalCandidate("c_good", ("Python",), (), 0.0),
        EvalCandidate("c_none", ("Verilog",), (), 0.0),
    )
    jobs = tuple(
        EvalJob(f"j{i}", f"Job{i}", "Co", ("Python",), (), None, None)
        for i in range(4)
    )
    labels = (
        EvalLabel("c_good", "j0", 2),
        EvalLabel("c_good", "j1", 1),
        EvalLabel("c_good", "j2", 0),
        EvalLabel("c_good", "j3", 0),
        EvalLabel("c_none", "j0", 0),
        EvalLabel("c_none", "j1", 0),
        EvalLabel("c_none", "j2", 0),
        EvalLabel("c_none", "j3", 0),
    )
    return EvalDataset(candidates, jobs, labels)


class TestAggregationSemantics:
    def test_aggregate_is_macro_average(self):
        # Two candidates with different P@5 -> mean, not pooled count
        rows = [
            {"precision@5": 1.0, "precision@10": 1.0, "ndcg@10": 1.0,
             "reciprocal_rank": 1.0, "needs_review_excluded": 0},
            {"precision@5": 0.0, "precision@10": 0.0, "ndcg@10": 0.0,
             "reciprocal_rank": 0.0, "needs_review_excluded": 0},
        ]
        agg = metrics.aggregate(rows)
        assert agg["precision@5"] == pytest.approx(0.5)  # mean of [1.0, 0.0]
        assert agg["mrr"] == pytest.approx(0.5)

    def test_grade_one_and_two_both_relevant_for_p_and_mrr(self):
        # P@k counts label>=1; a rank-1 label-1 job gives RR=1.0
        assert metrics.precision_at_k([1, 0, 0], 3) == pytest.approx(1 / 3)
        assert metrics.reciprocal_rank([1, 2, 0]) == 1.0
        # P@k cannot distinguish grade 1 from grade 2 (both relevant)...
        assert metrics.precision_at_k([1, 0], 1) == metrics.precision_at_k([2, 0], 1)
        # ...but nDCG does: [2,1] perfectly ordered beats [1,2]
        assert metrics.ndcg_at_k([2, 1], 2) > metrics.ndcg_at_k([1, 2], 2)

    def test_ndcg_uses_graded_gains(self):
        # [0,2] vs [2,0]: same multiset of gains, different order
        # -> different DCG, proving gain=label value ordering matters
        assert metrics.ndcg_at_k([2, 0], 2) > metrics.ndcg_at_k([0, 2], 2)


class TestZeroRelevantCandidate:
    def test_zero_relevant_candidate_metrics(self):
        ds = _mini_dataset()
        vec = fit_job_corpus_vectorizer(ds.jobs)
        cand_none = ds.candidates[1]
        result = evaluate_candidate(ds, cand_none, vec)
        # All labels 0 -> P@k = 0, RR = 0, nDCG undefined (None)
        assert result.precision_at_5 == 0.0
        assert result.precision_at_10 == 0.0
        assert result.reciprocal_rank == 0.0
        assert result.ndcg_at_10 is None

    def test_zero_relevant_excluded_from_ndcg_mean_only(self):
        ds = _mini_dataset()
        vec = fit_job_corpus_vectorizer(ds.jobs)
        rows = []
        for cand in ds.candidates:
            r = evaluate_candidate(ds, cand, vec)
            rows.append(
                {
                    "precision@5": r.precision_at_5,
                    "precision@10": r.precision_at_10,
                    "ndcg@10": r.ndcg_at_10,
                    "reciprocal_rank": r.reciprocal_rank,
                    "needs_review_excluded": r.needs_review_excluded,
                }
            )
        agg = metrics.aggregate(rows)
        assert agg["ndcg_excluded_count"] == 1  # c_none only
        assert agg["mrr"] == pytest.approx(0.5)  # c_none contributes 0 to mean
        # P@5 mean includes the zero candidate (macro over ALL candidates)
        p5s = [row["precision@5"] for row in rows]
        assert agg["precision@5"] == pytest.approx(sum(p5s) / 2)


class TestNeedsReviewExclusionEndToEnd:
    def test_needs_review_pair_never_ranked(self):
        candidates = (EvalCandidate("c1", ("Python",), (), 0.0),)
        jobs = tuple(
            EvalJob(f"j{i}", f"Job{i}", "Co", ("Python",), (), None, None)
            for i in range(3)
        )
        labels = (
            EvalLabel("c1", "j0", None),  # needs-review
            EvalLabel("c1", "j1", 0),
            EvalLabel("c1", "j2", 2),
        )
        ds = EvalDataset(candidates, jobs, labels)
        vec = fit_job_corpus_vectorizer(ds.jobs)
        result = evaluate_candidate(ds, ds.candidates[0], vec)
        assert result.needs_review_excluded == 1
        ranked_ids = {r.job_id for r in result.ranked}
        assert "j0" not in ranked_ids
        assert len(result.ranked) == 2
        # metrics computed only over the 2 eligible jobs
        assert all(isinstance(r, int) for r in result.relevances)
