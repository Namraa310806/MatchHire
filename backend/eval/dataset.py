"""Evaluation dataset loading and validation.

Dataset layout (CSV, human-editable — see eval/README.md):

- ``candidates.csv``: candidate_id, skills, domain_keywords,
  total_experience_years, note
- ``jobs.csv``: job_id, title, company, skills, domain_keywords,
  experience_min_years, experience_max_years, location, role_type
- ``labels.csv``: candidate_id, job_id, relevance
  (relevance in {0, 1, 2} or ``needs-review``)

List fields are ``;``-separated. Empty experience fields mean NULL
(unknown / no requirement), matching the matcher input contract.
"""

import csv
from dataclasses import dataclass
from pathlib import Path

RELEVANCE_LEVELS = (0, 1, 2)
NEEDS_REVIEW = "needs-review"


@dataclass(frozen=True)
class EvalCandidate:
    candidate_id: str
    skills: tuple[str, ...]
    domain_keywords: tuple[str, ...]
    total_experience_years: float | None
    note: str = ""


@dataclass(frozen=True)
class EvalJob:
    job_id: str
    title: str
    company: str
    skills: tuple[str, ...]
    domain_keywords: tuple[str, ...]
    experience_min_years: float | None
    experience_max_years: float | None
    location: str = ""
    role_type: str = ""


@dataclass(frozen=True)
class EvalLabel:
    candidate_id: str
    job_id: str
    relevance: int | None  # None means "needs-review"


@dataclass(frozen=True)
class EvalDataset:
    candidates: tuple[EvalCandidate, ...]
    jobs: tuple[EvalJob, ...]
    labels: tuple[EvalLabel, ...]


def _split_list(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(";") if part.strip())


def _parse_float(value: str, field: str) -> float | None:
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid float in {field}: {value!r}") from exc


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_candidates(path: Path) -> tuple[EvalCandidate, ...]:
    rows = _read_csv(path)
    candidates = []
    seen: set[str] = set()
    for row in rows:
        cid = row["candidate_id"].strip()
        if not cid:
            raise ValueError("candidate_id must not be empty")
        if cid in seen:
            raise ValueError(f"Duplicate candidate_id: {cid}")
        seen.add(cid)
        candidates.append(
            EvalCandidate(
                candidate_id=cid,
                skills=_split_list(row.get("skills", "")),
                domain_keywords=_split_list(row.get("domain_keywords", "")),
                total_experience_years=_parse_float(
                    row.get("total_experience_years", ""), "total_experience_years"
                ),
                note=row.get("note", "").strip(),
            )
        )
    if not candidates:
        raise ValueError("Dataset has no candidates")
    return tuple(candidates)


def load_jobs(path: Path) -> tuple[EvalJob, ...]:
    rows = _read_csv(path)
    jobs = []
    seen: set[str] = set()
    for row in rows:
        jid = row["job_id"].strip()
        if not jid:
            raise ValueError("job_id must not be empty")
        if jid in seen:
            raise ValueError(f"Duplicate job_id: {jid}")
        seen.add(jid)
        jobs.append(
            EvalJob(
                job_id=jid,
                title=row.get("title", "").strip(),
                company=row.get("company", "").strip(),
                skills=_split_list(row.get("skills", "")),
                domain_keywords=_split_list(row.get("domain_keywords", "")),
                experience_min_years=_parse_float(
                    row.get("experience_min_years", ""), "experience_min_years"
                ),
                experience_max_years=_parse_float(
                    row.get("experience_max_years", ""), "experience_max_years"
                ),
                location=row.get("location", "").strip(),
                role_type=row.get("role_type", "").strip(),
            )
        )
    if not jobs:
        raise ValueError("Dataset has no jobs")
    return tuple(jobs)


def load_labels(path: Path) -> tuple[EvalLabel, ...]:
    rows = _read_csv(path)
    labels = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        cid = row["candidate_id"].strip()
        jid = row["job_id"].strip()
        raw = row["relevance"].strip()
        if (cid, jid) in seen:
            raise ValueError(f"Duplicate label for ({cid}, {jid})")
        seen.add((cid, jid))
        if raw == NEEDS_REVIEW:
            relevance = None
        else:
            try:
                relevance = int(raw)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid relevance {raw!r} for ({cid}, {jid}); "
                    f"expected 0, 1, 2, or {NEEDS_REVIEW!r}"
                ) from exc
            if relevance not in RELEVANCE_LEVELS:
                raise ValueError(
                    f"Relevance {relevance} out of range for ({cid}, {jid}); "
                    f"expected one of {RELEVANCE_LEVELS} or {NEEDS_REVIEW!r}"
                )
        labels.append(EvalLabel(candidate_id=cid, job_id=jid, relevance=relevance))
    if not labels:
        raise ValueError("Dataset has no labels")
    return tuple(labels)


def load_dataset(directory: Path | str) -> EvalDataset:
    """Load and validate a complete evaluation dataset.

    Validation guarantees:
    - unique candidate/job IDs
    - every label references an existing candidate and job
    - every (candidate, job) pair has exactly one label
    """
    directory = Path(directory)
    candidates = load_candidates(directory / "candidates.csv")
    jobs = load_jobs(directory / "jobs.csv")
    labels = load_labels(directory / "labels.csv")

    candidate_ids = {c.candidate_id for c in candidates}
    job_ids = {j.job_id for j in jobs}

    for label in labels:
        if label.candidate_id not in candidate_ids:
            raise ValueError(
                f"Label references unknown candidate {label.candidate_id!r}"
            )
        if label.job_id not in job_ids:
            raise ValueError(f"Label references unknown job {label.job_id!r}")

    expected = {(c.candidate_id, j.job_id) for c in candidates for j in jobs}
    actual = {(label.candidate_id, label.job_id) for label in labels}
    missing = expected - actual
    extra = actual - expected
    if missing:
        sample = sorted(missing)[:5]
        raise ValueError(
            f"{len(missing)} candidate/job pairs missing labels, e.g. {sample}"
        )
    if extra:
        raise ValueError(f"Labels for non-existent pairs: {sorted(extra)[:5]}")

    return EvalDataset(candidates=candidates, jobs=jobs, labels=labels)


def label_map(dataset: EvalDataset) -> dict[tuple[str, str], EvalLabel]:
    """(candidate_id, job_id) -> EvalLabel lookup."""
    return {(label.candidate_id, label.job_id): label for label in dataset.labels}


def relevance_for(
    dataset: EvalDataset, candidate_id: str, job_id: str
) -> int | None:
    """Graded relevance (0/1/2) or None for needs-review."""
    return label_map(dataset)[(candidate_id, job_id)].relevance
