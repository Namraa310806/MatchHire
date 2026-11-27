"""Ranking metrics for the golden evaluation.

Definitions (documented in docs/EVAL.md):

- A job is *relevant* for P@k and MRR when its graded label is >= 1
  ("acceptable" or "strong").
- nDCG gain equals the graded label value (0, 1, 2).
- ``needs-review`` pairs (relevance None) are excluded from a
  candidate's ranking pool before metrics are computed.
- P@k = (# relevant jobs in top-k) / min(k, pool_size).
- DCG@k = sum over rank i (1-based) of gain_i / log2(i + 1).
- IDCG@k = DCG of the ideal ordering (gains sorted descending).
- nDCG@k = DCG/IDCG; undefined (IDCG == 0) -> candidate excluded from
  the nDCG mean and counted separately.
- MRR = mean over candidates of 1/rank of the first relevant job;
  candidates with no relevant job contribute 0.
"""

import math
from collections.abc import Mapping, Sequence
from typing import Any


def _gain(relevance: int) -> float:
    return float(relevance)


def precision_at_k(
    ranked_relevances: Sequence[int], k: int, relevant_threshold: int = 1
) -> float:
    """Fraction of top-k results that are relevant.

    ``ranked_relevances`` are the graded labels in rank order for one
    candidate's evaluated pool. Denominator is min(k, pool size).
    """
    if k <= 0:
        raise ValueError("k must be positive")
    if not ranked_relevances:
        return 0.0
    top = ranked_relevances[:k]
    relevant = sum(1 for rel in top if rel >= relevant_threshold)
    return relevant / min(k, len(ranked_relevances))


def _dcg(gains: Sequence[float], k: int) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains[:k]))


def ndcg_at_k(ranked_relevances: Sequence[int], k: int) -> float | None:
    """Normalized DCG at k. Returns None when IDCG is 0 (no relevant
    jobs in the pool — nDCG is undefined, not zero)."""
    if k <= 0:
        raise ValueError("k must be positive")
    if not ranked_relevances:
        return None
    gains = [_gain(rel) for rel in ranked_relevances]
    idcg = _dcg(sorted(gains, reverse=True), k)
    if idcg == 0.0:
        return None
    return _dcg(gains, k) / idcg


def reciprocal_rank(ranked_relevances: Sequence[int], relevant_threshold: int = 1) -> float:
    """1/rank of the first relevant job, or 0.0 if none."""
    for i, rel in enumerate(ranked_relevances, start=1):
        if rel >= relevant_threshold:
            return 1.0 / i
    return 0.0


def mean_reciprocal_rank(per_candidate_rr: Sequence[float]) -> float:
    if not per_candidate_rr:
        return 0.0
    return sum(per_candidate_rr) / len(per_candidate_rr)


def aggregate(
    per_candidate: Sequence[Mapping[str, Any]],
) -> dict[str, float | int | None]:
    """Aggregate per-candidate metric dicts into means.

    ``per_candidate`` entries look like::

        {"precision@5": 0.4, "precision@10": 0.3, "ndcg@10": 0.55,
         "reciprocal_rank": 0.5, "needs_review_excluded": 3}

    nDCG mean excludes candidates whose nDCG was None (no relevant
    jobs); the count is reported as ``ndcg_excluded_count``.
    """
    if not per_candidate:
        return {
            "candidates": 0,
            "precision@5": None,
            "precision@10": None,
            "ndcg@10": None,
            "ndcg_excluded_count": 0,
            "mrr": None,
        }

    def _mean(key: str, skip_none: bool = False) -> float | None:
        values = [
            float(c[key])
            for c in per_candidate
            if not skip_none or c[key] is not None
        ]
        if not values:
            return None
        return sum(values) / len(values)

    return {
        "candidates": len(per_candidate),
        "precision@5": _mean("precision@5"),
        "precision@10": _mean("precision@10"),
        "ndcg@10": _mean("ndcg@10", skip_none=True),
        "ndcg_excluded_count": sum(
            1 for c in per_candidate if c["ndcg@10"] is None
        ),
        "mrr": _mean("reciprocal_rank"),
        "needs_review_excluded": sum(
            int(c.get("needs_review_excluded") or 0) for c in per_candidate
        ),
    }
