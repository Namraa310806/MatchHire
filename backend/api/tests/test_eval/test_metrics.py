"""Hand-calculated metric tests."""

import math

import pytest

from eval.metrics import (
    aggregate,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    reciprocal_rank,
)


class TestPrecisionAtK:
    def test_perfect_ranking(self):
        # 5 relevant jobs at top -> P@5 = 1.0
        assert precision_at_k([2, 2, 1, 1, 2, 0, 0], 5) == 1.0

    def test_partial(self):
        # top-5: 2,0,1,0,2 -> 3 relevant of 5
        assert precision_at_k([2, 0, 1, 0, 2, 0], 5) == pytest.approx(0.6)

    def test_label_zero_not_relevant(self):
        assert precision_at_k([0, 0, 0], 3) == 0.0

    def test_label_one_counts_as_relevant(self):
        assert precision_at_k([1, 0, 0], 3) == pytest.approx(1 / 3)

    def test_pool_smaller_than_k(self):
        # 2 results, k=5 -> denominator is pool size 2
        assert precision_at_k([2, 0], 5) == 0.5

    def test_empty_pool(self):
        assert precision_at_k([], 5) == 0.0

    def test_k_must_be_positive(self):
        with pytest.raises(ValueError):
            precision_at_k([1], 0)


class TestNdcg:
    def test_perfect_ranking(self):
        # ideal order already -> nDCG = 1.0
        assert ndcg_at_k([2, 2, 1, 0], 3) == pytest.approx(1.0)

    def test_worst_ordering_lower_than_best(self):
        best = ndcg_at_k([2, 2, 1, 0], 3)
        worst = ndcg_at_k([0, 0, 0, 2, 2, 1], 3)
        assert worst is not None and best is not None
        assert worst < best

    def test_hand_calculated(self):
        # gains [1,0,0,...]: DCG = 1/log2(2) = 1; IDCG same -> 1.0
        assert ndcg_at_k([1, 0, 0], 3) == pytest.approx(1.0)
        # gains [0,2]: DCG = 2/log2(3) ≈ 1.2619; IDCG = 2/log2(2)+0 = 2
        # nDCG = 1.2619/2 ≈ 0.6309
        expected = (2 / math.log2(3)) / 2
        assert ndcg_at_k([0, 2], 2) == pytest.approx(expected)

    def test_no_relevant_returns_none(self):
        assert ndcg_at_k([0, 0, 0], 3) is None

    def test_empty_returns_none(self):
        assert ndcg_at_k([], 3) is None


class TestMRR:
    def test_first_position(self):
        assert reciprocal_rank([2, 1, 0]) == 1.0

    def test_second_position(self):
        assert reciprocal_rank([0, 2, 1]) == 0.5

    def test_third_position(self):
        assert reciprocal_rank([0, 0, 1]) == pytest.approx(1 / 3)

    def test_no_relevant(self):
        assert reciprocal_rank([0, 0, 0]) == 0.0

    def test_empty(self):
        assert reciprocal_rank([]) == 0.0

    def test_mean(self):
        assert mean_reciprocal_rank([1.0, 0.5, 0.0]) == pytest.approx(0.5)
        assert mean_reciprocal_rank([]) == 0.0


class TestAggregate:
    def test_means_and_exclusions(self):
        rows = [
            {"precision@5": 0.4, "precision@10": 0.3, "ndcg@10": 0.5,
             "reciprocal_rank": 0.5, "needs_review_excluded": 2},
            {"precision@5": 0.2, "precision@10": 0.2, "ndcg@10": None,
             "reciprocal_rank": 0.0, "needs_review_excluded": 1},
        ]
        agg = aggregate(rows)
        assert agg["candidates"] == 2
        assert agg["precision@5"] == pytest.approx(0.3)
        assert agg["ndcg@10"] == pytest.approx(0.5)  # None excluded from mean
        assert agg["ndcg_excluded_count"] == 1
        assert agg["mrr"] == pytest.approx(0.25)
        assert agg["needs_review_excluded"] == 3

    def test_empty(self):
        agg = aggregate([])
        assert agg["candidates"] == 0
        assert agg["mrr"] is None
