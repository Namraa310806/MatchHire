"""Generate labels.csv from a documented, hand-authored relevance rubric.

IMPORTANT: labels are assigned by the rubric below — human judgment
encoded as rules — NEVER from matcher scores. Running this script only
reproduces the committed labels.csv; edit the rubric or the CSV
directly to change labels (the CSV is the source of truth for review).

Relevance scale:
- 2 = strong: job is a genuinely good fit for the candidate archetype
- 1 = acceptable: partially relevant (adjacent domain, thin skill fit,
  or otherwise plausible but not a strong match)
- 0 = irrelevant: unrelated domain and skills
- needs-review = borderline case flagged for human review; excluded
  from metric computation

Rubric (per candidate, TARGET_DOMAINS and CORE_SKILLS are defined in
CANDIDATE_RULES below):

Let sig = |canonical(job.skills) ∩ canonical(candidate.skills)|
Let dom = canonical(job.domain_keywords) ∩ TARGET_DOMAINS(candidate) != ∅
Let under = candidate.total_experience_years is not None AND
           job.experience_min_years is not None AND
           job.experience_min_years > 0 AND
           candidate.total_experience_years < job.experience_min_years

would_be_strong = (dom AND sig >= 1) OR sig >= 3

- if would_be_strong AND under -> 1   (qualified domain/skills but
  below the stated experience floor: partially relevant)
- elif would_be_strong -> 2
- elif dom OR sig >= 1 -> 1
- else -> 0

needs-review override: dom AND sig == 0 -> needs-review
(domain-aligned but zero shared skills: genuinely ambiguous whether
the candidate's skills transfer).

Unknown candidate experience (None) never triggers `under` — matching
the SPEC convention that unknown experience is not disqualifying.
"""

import csv
from pathlib import Path
from typing import Any

from api.extraction.domain_keywords import (
    get_all_domain_keywords,
    get_domain_keyword_aliases,
)
from api.extraction.skill_extractor import get_skills_dictionary

DATASET_DIR = Path(__file__).parent

# Per-candidate rubric parameters. target_domains uses canonical domain
# keyword names; core_skills is informational (documents the archetype's
# defining skills — the rubric itself uses the full candidate skill set).
CANDIDATE_RULES: dict[str, dict] = {
    "c01_ml_fresher": {
        "target_domains": {"Machine Learning", "Data Science"},
        "core_skills": {"Python", "scikit-learn", "TensorFlow", "Pandas"},
    },
    "c02_frontend_react_fresher": {
        "target_domains": {"SaaS", "User Experience"},
        "core_skills": {"JavaScript", "TypeScript", "React", "HTML", "CSS"},
    },
    "c03_devops_engineer": {
        "target_domains": {"DevOps", "Cloud Computing"},
        "core_skills": {"Docker", "Kubernetes", "AWS", "Terraform", "Linux"},
    },
    "c04_vlsi_embedded": {
        "target_domains": {"VLSI", "Embedded Systems", "IoT"},
        "core_skills": {"Verilog", "FPGA", "VHDL", "Embedded C", "STM32"},
    },
    "c05_java_backend_dev": {
        "target_domains": {"Microservices", "Distributed Systems"},
        "core_skills": {"Java", "Spring", "PostgreSQL", "Redis"},
    },
    "c06_data_analyst": {
        "target_domains": {"Data Analytics", "Data Science"},
        "core_skills": {"SQL", "Python", "Pandas"},
    },
    "c07_android_dev": {
        "target_domains": set(),  # no domain keywords -> skill-overlap only
        "core_skills": {"Kotlin", "Android", "Jetpack Compose"},
    },
    "c08_security_analyst": {
        "target_domains": {"Cybersecurity", "InfoSec"},
        "core_skills": {"SIEM", "Nmap", "Wireshark", "Burp Suite"},
    },
    "c09_qa_engineer": {
        "target_domains": {"Quality Assurance", "Test Automation"},
        "core_skills": {"Pytest", "Selenium", "Postman"},
    },
    "c10_fullstack_unknown": {
        "target_domains": {"SaaS", "Agile", "Microservices"},
        "core_skills": {"Python", "JavaScript", "React", "Django"},
    },
}


def _split(value: str) -> list[str]:
    return [p.strip() for p in value.split(";") if p.strip()]


def _canonical_skills(names: list[str]) -> set[str]:
    dictionary = get_skills_dictionary()
    out = set()
    for name in names:
        resolved = dictionary.resolve_alias(name)
        if resolved is not None:
            out.add(resolved[0])
    return out


def _canonical_keywords(names: list[str]) -> set[str]:
    resolver: dict[str, str] = {}
    for canonical in get_all_domain_keywords():
        resolver[canonical.casefold()] = canonical
    for canonical in get_all_domain_keywords():
        for alias in get_domain_keyword_aliases(canonical) or []:
            resolver.setdefault(alias.casefold(), canonical)
    out = set()
    for name in names:
        resolved = resolver.get(name.strip().casefold())
        if resolved is not None:
            out.add(resolved)
    return out


def _parse_float(value: str) -> float | None:
    value = value.strip()
    return float(value) if value else None


def label_pair(
    cand_skills: set[str],
    cand_keywords: set[str],
    cand_yoe: float | None,
    job_skills: set[str],
    job_keywords: set[str],
    job_exp_min: float | None,
    target_domains: set[str],
) -> str:
    sig = len(cand_skills & job_skills)
    dom = bool(job_keywords & target_domains)
    under = (
        cand_yoe is not None
        and job_exp_min is not None
        and job_exp_min > 0
        and cand_yoe < job_exp_min
    )
    would_be_strong = (dom and sig >= 1) or sig >= 3

    if dom and sig == 0:
        return "needs-review"
    if would_be_strong and under:
        return "1"
    if would_be_strong:
        return "2"
    if dom or sig >= 1:
        return "1"
    return "0"


def build() -> list[tuple[str, str, str]]:
    candidates: dict[str, dict[str, Any]] = {}
    with (DATASET_DIR / "candidates.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            cid = row["candidate_id"].strip()
            candidates[cid] = {
                "skills": _canonical_skills(_split(row["skills"])),
                "keywords": _canonical_keywords(_split(row["domain_keywords"])),
                "yoe": _parse_float(row.get("total_experience_years", "")),
            }

    jobs: dict[str, dict[str, Any]] = {}
    with (DATASET_DIR / "jobs.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            jid = row["job_id"].strip()
            jobs[jid] = {
                "skills": _canonical_skills(_split(row["skills"])),
                "keywords": _canonical_keywords(_split(row["domain_keywords"])),
                "exp_min": _parse_float(row.get("experience_min_years", "")),
            }

    rows = []
    for cid, cand in candidates.items():
        rules = CANDIDATE_RULES[cid]
        for jid, job in jobs.items():
            rel = label_pair(
                cand["skills"],
                cand["keywords"],
                cand["yoe"],
                job["skills"],
                job["keywords"],
                job["exp_min"],
                rules["target_domains"],
            )
            rows.append((cid, jid, rel))
    return rows


def main() -> None:
    rows = build()
    out = DATASET_DIR / "labels.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["candidate_id", "job_id", "relevance"])
        writer.writerows(rows)
    counts: dict[str, int] = {}
    for _, _, rel in rows:
        counts[rel] = counts.get(rel, 0) + 1
    print(f"Wrote {len(rows)} labels to {out}: {counts}")


if __name__ == "__main__":
    main()
