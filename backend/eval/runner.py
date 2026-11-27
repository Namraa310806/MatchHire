"""Evaluation runner: score the dataset with the v0 matcher and compute
ranking metrics.

Uses a ``TfidfVectorizer`` fitted on the evaluation job skill corpus —
never ``UNIFORM_VECTORIZER`` for the primary evaluation. Deterministic:
same dataset + same code -> identical report. Ranking ties break by
``job_id`` ascending.
"""

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from api.matching import (
    CandidateInput,
    JobInput,
    TfidfVectorizer,
    match,
)
from api.matching.config import DEFAULT_CONFIG

from . import metrics
from .dataset import EvalCandidate, EvalDataset, EvalJob, load_dataset

DEFAULT_K = 10


@dataclass(frozen=True)
class RankedJob:
    job_id: str
    total_score: float
    skill_similarity: float
    experience_match: float
    keyword_overlap: float


@dataclass(frozen=True)
class CandidateResult:
    candidate_id: str
    ranked: tuple[RankedJob, ...]
    relevances: tuple[int, ...]  # graded labels in rank order (needs-review excluded)
    needs_review_excluded: int
    precision_at_5: float
    precision_at_10: float
    ndcg_at_10: float | None
    reciprocal_rank: float


def to_candidate_input(candidate: EvalCandidate) -> CandidateInput:
    return CandidateInput.from_iterables(
        skills=candidate.skills,
        domain_keywords=candidate.domain_keywords,
        total_experience_years=candidate.total_experience_years,
    )


def to_job_input(job: EvalJob) -> JobInput:
    return JobInput.from_iterables(
        skills=job.skills,
        domain_keywords=job.domain_keywords,
        experience_min_years=job.experience_min_years,
        experience_max_years=job.experience_max_years,
    )


def fit_job_corpus_vectorizer(jobs: Iterable[EvalJob]) -> TfidfVectorizer:
    """Fit TF-IDF IDF over the evaluation job skill corpus.

    Each job contributes one document = its canonical skill set.
    """
    return TfidfVectorizer.fit([job.skills for job in jobs])


def rank_jobs_for_candidate(
    candidate: EvalCandidate,
    jobs: Iterable[EvalJob],
    vectorizer: TfidfVectorizer,
) -> tuple[RankedJob, ...]:
    """Score one candidate against all jobs; deterministic ordering.

    Sort: total_score descending, then job_id ascending (stable
    tie-break independent of dict/set ordering).
    """
    cand_input = to_candidate_input(candidate)
    scored = []
    for job in jobs:
        result = match(
            cand_input,
            to_job_input(job),
            config=DEFAULT_CONFIG,
            vectorizer=vectorizer,
        )
        scored.append(
            RankedJob(
                job_id=job.job_id,
                total_score=result.total_score,
                skill_similarity=result.skill_similarity,
                experience_match=result.experience_match,
                keyword_overlap=result.keyword_overlap,
            )
        )
    scored.sort(key=lambda r: (-r.total_score, r.job_id))
    return tuple(scored)


def evaluate_candidate(
    dataset: EvalDataset,
    candidate: EvalCandidate,
    vectorizer: TfidfVectorizer,
    k: int = DEFAULT_K,
) -> CandidateResult:
    """Rank and score one candidate; needs-review pairs are excluded."""
    labels = {(label.candidate_id, label.job_id): label.relevance for label in dataset.labels}
    excluded = 0
    eligible_jobs = []
    for job in dataset.jobs:
        rel = labels[(candidate.candidate_id, job.job_id)]
        if rel is None:
            excluded += 1
        else:
            eligible_jobs.append(job)

    ranked = rank_jobs_for_candidate(candidate, eligible_jobs, vectorizer)
    relevances = tuple(labels[(candidate.candidate_id, r.job_id)] for r in ranked)
    # relevances are int (needs-review already excluded); assert for type checkers
    relevances_int = tuple(r for r in relevances if r is not None)

    return CandidateResult(
        candidate_id=candidate.candidate_id,
        ranked=ranked,
        relevances=relevances_int,
        needs_review_excluded=excluded,
        precision_at_5=metrics.precision_at_k(relevances_int, 5),
        precision_at_10=metrics.precision_at_k(relevances_int, min(k, 10)),
        ndcg_at_10=metrics.ndcg_at_k(relevances_int, k),
        reciprocal_rank=metrics.reciprocal_rank(relevances_int),
    )


def evaluate(
    dataset: EvalDataset,
    k: int = DEFAULT_K,
    vectorizer: TfidfVectorizer | None = None,
) -> dict:
    """Run the full evaluation and return a JSON-serializable report."""
    vec = vectorizer or fit_job_corpus_vectorizer(dataset.jobs)
    per_candidate = []
    for candidate in dataset.candidates:
        result = evaluate_candidate(dataset, candidate, vec, k=k)
        per_candidate.append(result)

    summary_rows = [
        {
            "candidate_id": r.candidate_id,
            "precision@5": r.precision_at_5,
            "precision@10": r.precision_at_10,
            "ndcg@10": r.ndcg_at_10,
            "reciprocal_rank": r.reciprocal_rank,
            "needs_review_excluded": r.needs_review_excluded,
        }
        for r in per_candidate
    ]
    aggregate = metrics.aggregate(summary_rows)

    top_rows = []
    for r in per_candidate:
        top_rows.append(
            {
                "candidate_id": r.candidate_id,
                "top10": [
                    {
                        "job_id": rk.job_id,
                        "total_score": round(rk.total_score, 6),
                        "relevance": rel,
                    }
                    for rk, rel in zip(r.ranked[:10], r.relevances[:10], strict=True)
                ],
            }
        )

    return {
        "dataset": {
            "candidates": len(dataset.candidates),
            "jobs": len(dataset.jobs),
            "labels": len(dataset.labels),
        },
        "vectorizer": {
            "type": "corpus-fitted",
            "is_corpus_fitted": vec.is_corpus_fitted,
            "document_count": vec.document_count,
        },
        "k": k,
        "aggregate": aggregate,
        "per_candidate": summary_rows,
        "top10": top_rows,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="MatchHire golden evaluation")
    parser.add_argument(
        "--dataset",
        default=str(Path(__file__).parent),
        help="Directory containing candidates/jobs/labels CSVs",
    )
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--json", action="store_true", help="Emit full JSON report")
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    report = evaluate(dataset, k=args.k)
    if args.json:
        print(json.dumps(report, indent=2))
        return

    agg = report["aggregate"]
    print(f"Dataset: {report['dataset']['candidates']} candidates x "
          f"{report['dataset']['jobs']} jobs")
    print(f"Vectorizer: corpus-fitted (N={report['vectorizer']['document_count']})")
    print(f"Aggregate: P@5={agg['precision@5']:.4f} "
          f"P@10={agg['precision@10']:.4f} "
          f"nDCG@10={agg['ndcg@10'] if agg['ndcg@10'] is not None else 'n/a'} "
          f"MRR={agg['mrr']:.4f} "
          f"(nDCG excluded: {agg['ndcg_excluded_count']}, "
          f"needs-review excluded: {agg['needs_review_excluded']})")
    for row in report["per_candidate"]:
        ndcg = row["ndcg@10"]
        print(
            f"  {row['candidate_id']:<24} P@5={row['precision@5']:.2f} "
            f"P@10={row['precision@10']:.2f} "
            f"nDCG@10={ndcg if ndcg is not None else 'n/a'} "
            f"RR={row['reciprocal_rank']:.2f} "
            f"(excluded={row['needs_review_excluded']})"
        )


if __name__ == "__main__":
    main()
