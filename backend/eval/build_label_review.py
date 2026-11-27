"""Generate label_review.csv — a human-reviewable audit of every
candidate/job relevance label.

One row per pair with the assigned grade and a rubric_reason string
that explains exactly which rubric branch produced the grade. The
reasons are recomputed with the SAME logic as build_labels.py
(imported helpers + CANDIDATE_RULES), so every grade is traceable.

human_review_grade and reviewer_notes start blank — this file does
NOT modify labels.csv and contains no invented review results.
Reviewers fill human_review_grade (0/1/2/agree/disagree) and notes,
then labels.csv can be corrected separately.
"""

import csv
from typing import Any

from .build_labels import (
    CANDIDATE_RULES,
    DATASET_DIR,
    _canonical_keywords,
    _canonical_skills,
    _parse_float,
    _split,
)

OUT_PATH = DATASET_DIR / "label_review.csv"
FIELDNAMES = [
    "candidate_id",
    "candidate_summary",
    "job_id",
    "job_title",
    "job_domain",
    "assigned_grade",
    "rubric_reason",
    "human_review_grade",
    "reviewer_notes",
]


def _load_candidates() -> dict[str, dict[str, Any]]:
    out = {}
    with (DATASET_DIR / "candidates.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            cid = row["candidate_id"].strip()
            out[cid] = {
                "summary": row.get("note", "").strip() or cid,
                "skills": _canonical_skills(_split(row["skills"])),
                "keywords": _canonical_keywords(_split(row["domain_keywords"])),
                "yoe": _parse_float(row.get("total_experience_years", "")),
            }
    return out


def _load_jobs() -> dict[str, dict[str, Any]]:
    out = {}
    with (DATASET_DIR / "jobs.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            jid = row["job_id"].strip()
            out[jid] = {
                "title": row.get("title", "").strip(),
                "domain": row.get("domain_keywords", "").strip(),
                "skills": _canonical_skills(_split(row["skills"])),
                "keywords": _canonical_keywords(_split(row["domain_keywords"])),
                "exp_min": _parse_float(row.get("experience_min_years", "")),
            }
    return out


def _grade_and_reason(
    cand: dict[str, Any],
    job: dict[str, Any],
    target_domains: set[str],
) -> tuple[str, str]:
    """Mirror of build_labels.label_pair, returning (grade, reason)."""
    shared = cand["skills"] & job["skills"]
    sig = len(shared)
    matched_domains = sorted(job["keywords"] & target_domains)
    dom = bool(matched_domains)
    under = (
        cand["yoe"] is not None
        and job["exp_min"] is not None
        and job["exp_min"] > 0
        and cand["yoe"] < job["exp_min"]
    )
    would_be_strong = (dom and sig >= 1) or sig >= 3

    dom_txt = ",".join(matched_domains) if matched_domains else "none"
    shared_txt = ",".join(sorted(shared)[:5]) + ("..." if sig > 5 else "")

    if dom and sig == 0:
        return (
            "needs-review",
            f"domain-aligned ({dom_txt}) but 0 shared canonical skills",
        )
    if would_be_strong and under:
        return (
            "1",
            f"would be strong (dom={dom_txt}, shared={sig}: {shared_txt or 'none'}) "
            f"but underqualified: yoe={cand['yoe']} < required_min={job['exp_min']}",
        )
    if would_be_strong:
        if dom and sig >= 1:
            why = f"domain match ({dom_txt}) + {sig} shared skills ({shared_txt})"
        else:
            why = f"{sig} shared canonical skills >= 3 ({shared_txt})"
        return ("2", f"strong: {why}")
    if dom or sig >= 1:
        parts = []
        if dom:
            parts.append(f"domain match ({dom_txt})")
        if sig >= 1:
            parts.append(f"{sig} shared skill(s) ({shared_txt})")
        return ("1", "acceptable: " + " + ".join(parts))
    return ("0", "irrelevant: no domain alignment and 0 shared skills")


def main() -> None:
    candidates = _load_candidates()
    jobs = _load_jobs()

    rows = []
    for cid, cand in candidates.items():
        target_domains = CANDIDATE_RULES[cid]["target_domains"]
        for jid, job in jobs.items():
            grade, reason = _grade_and_reason(cand, job, target_domains)
            rows.append(
                {
                    "candidate_id": cid,
                    "candidate_summary": cand["summary"],
                    "job_id": jid,
                    "job_title": job["title"],
                    "job_domain": job["domain"] or "(none)",
                    "assigned_grade": grade,
                    "rubric_reason": reason,
                    "human_review_grade": "",
                    "reviewer_notes": "",
                }
            )

    with OUT_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["assigned_grade"]] = counts.get(r["assigned_grade"], 0) + 1
    print(f"Wrote {len(rows)} rows to {OUT_PATH}: {counts}")


if __name__ == "__main__":
    main()
