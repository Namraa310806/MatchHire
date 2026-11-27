# Golden Evaluation Dataset

Reproducible evaluation set for the v0 matching engine
(`api.matching`). Used by `eval.runner` and `api/tests/test_eval`.

## Files

- `candidates.csv` — 10 synthetic candidate profiles (archetypes:
  Python+ML fresher, React fresher, DevOps, embedded/VLSI, Java
  backend, data analyst, Android, cybersecurity, QA, full-stack with
  unknown experience). Skills and domain keywords are `;`-separated;
  experience is years or empty (= unknown).
- `jobs.csv` — 60 synthetic job postings across ML/AI, frontend,
  backend, DevOps/cloud, data, VLSI/embedded, cybersecurity, QA and
  mobile. Same field conventions; experience min/max empty = no
  stated bound.
- `labels.csv` — graded relevance for **every** candidate×job pair
  (600 rows). `0` irrelevant, `1` acceptable, `2` strong,
  `needs-review` = borderline, excluded from metrics.
- `build_labels.py` — regenerates `labels.csv` from the documented
  rubric in its docstring. Labels are rubric-assigned human judgment,
  never derived from matcher scores.

## Label methodology

See `build_labels.py` docstring for the exact rubric. In short:
strong (2) requires domain-keyword alignment **and** skill overlap,
or ≥3 shared canonical skills; acceptable (1) for single weak signals
or experience-floor shortfalls; irrelevant (0) otherwise;
`needs-review` when domain-aligned but zero shared skills.

**These labels are synthetic and rubric-assigned — they are NOT
human-verified ground truth.** Review and correct `labels.csv`
directly; the CSV is the source of truth.

## Running

```bash
cd backend
uv run python -m eval.runner            # human-readable summary
uv run python -m eval.runner --json     # full JSON report
uv run python -m eval.build_labels      # regenerate labels.csv
```

The evaluator fits `TfidfVectorizer` on the job skill corpus (never
the uniform vectorizer) and scores every pair with the unmodified
Gate 1 `match()`.
