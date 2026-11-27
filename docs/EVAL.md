# Golden Evaluation — v0 Matching Engine

Evaluation of the pure-Python v0 matcher (`backend/api/matching/`)
against a hand-labeled synthetic dataset. This measures *ranking
quality on synthetic data only* — it is not evidence of real-world
production performance.

- **Date:** 2026-11-26
- **Matcher:** Gate 1 v0 engine, unmodified (formula
  `0.50·skill_similarity + 0.30·experience_match + 0.20·keyword_overlap`,
  SPEC Decision 1/2/3)
- **Vectorizer:** `TfidfVectorizer.fit(job_skill_corpus)` — corpus-fitted
  IDF over the 60 evaluation jobs (`is_corpus_fitted=True`, N=60).
  `UNIFORM_VECTORIZER` is NOT used for the primary evaluation.
- **Reproduce:** `cd backend && uv run python -m eval.runner [--json]`

## Dataset

`backend/eval/` — 10 synthetic candidates × 60 synthetic jobs = 600
labeled pairs. Candidates cover the playbook archetypes (Python+ML
fresher, React fresher, DevOps, embedded/VLSI, plus Java backend, data
analyst, Android, cybersecurity, QA, and a full-stack profile with
unknown experience). Jobs span ML/AI, frontend, backend, DevOps/cloud,
data, VLSI/embedded, security, QA and mobile, with varied skill-set
sizes and experience requirements (including `0`, ranges, and
unstated). No real candidate or company identities are used.

## Relevance labels

Scale: `0` irrelevant, `1` acceptable, `2` strong, `needs-review`
(borderline; excluded from metrics). Labels were assigned by a
documented rubric (`eval/build_labels.py` docstring) — domain-keyword
alignment + skill overlap + experience floor — **not** from matcher
scores. Distribution: 400×0, 155×1, 44×2, 1 needs-review.

**Limitation:** the rubric deliberately uses the same signal families
the matcher consumes (canonical skill overlap, domain keywords), so
labels are correlated with matcher inputs. Metrics are therefore
optimistic relative to truly independent human judgment. The CSV is
intended for human review/correction before being treated as ground
truth.

## Metric definitions and aggregation

All aggregates are **macro-averages**: each candidate contributes one
row of metrics, and the aggregate is the unweighted mean across
candidates (`eval/metrics.py::aggregate` → `_mean`). No job-level or
label-level pooling occurs.

- **Relevance for P@k and MRR:** a job counts as relevant when its
  graded label is **≥ 1** — grades 1 ("acceptable") and 2 ("strong")
  both count. Grade 0 does not.
- **nDCG gain:** equals the graded label value (0, 1, or 2) — graded
  relevance is used directly as gain, not binarized.
- **P@k:** `(# relevant jobs in top-k) / min(k, pool_size)`. With 60
  jobs the denominator is always k.
- **DCG@k / IDCG@k / nDCG@k:** DCG = Σ gainᵢ/log₂(i+1) over rank order;
  IDCG = same over the ideal (gain-sorted) order; nDCG = DCG/IDCG.
- **MRR:** per candidate = 1/rank of the first relevant (label ≥ 1)
  job, 0 if none; aggregate = mean over all candidates (zero-relevant
  candidates contribute 0, they are NOT excluded).
- **Zero-relevant-job candidates:** P@k = 0 and MRR contribution = 0;
  nDCG is **undefined** (IDCG = 0) → the candidate is excluded from the
  nDCG mean and counted in `ndcg_excluded_count`. In this dataset every
  candidate has ≥1 relevant job, so `ndcg_excluded_count = 0`.
- **needs-review pairs:** excluded from that candidate's ranking pool
  *before* scoring/ranking — they never appear in `ranked` and cannot
  affect any metric. `needs_review_excluded` reports how many were
  dropped per candidate (1 total: c10/j27).
- **Why MRR = 1.0:** every candidate has at least one relevant job,
  and the matcher's top-ranked job is relevant (label ≥ 1) for all 10
  candidates — verified in `per_candidate` output and ordering tests.
  MRR=1.0 means "first result was relevant everywhere," not "perfect
  ranking" (P@10=0.86 and nDCG@10=0.95 show lower-ranked noise).
- **Determinism:** ranking sorts by `(-total_score, job_id)`; the same
  dataset + code produces byte-identical reports (verified by running
  the evaluator twice — see reproducibility section).

## Reproducibility

```bash
cd backend
uv run python -m eval.runner --json > /tmp/eval_run1.json
uv run python -m eval.runner --json > /tmp/eval_run2.json
diff /tmp/eval_run1.json /tmp/eval_run2.json   # identical
```

- **Dataset paths:** `backend/eval/candidates.csv`, `jobs.csv`,
  `labels.csv` (loaded by `eval.dataset.load_dataset`).
- **TF-IDF corpus:** the skill sets of all 60 evaluation jobs — one
  document per job (`eval.runner.fit_job_corpus_vectorizer`).
- **Vectorizer:** `TfidfVectorizer.fit(corpus)` → smoothed IDF
  `ln((N+1)/(df+1)) + 1`, N=60, binary TF, fixed ~500-term vocabulary.
  `is_corpus_fitted=True`. `UNIFORM_VECTORIZER` is not used.
- **Matcher:** `api.matching.match()` with `DEFAULT_CONFIG`
  (0.50/0.30/0.20) — unmodified Gate 1 engine.
- **Tie-breaking:** `total_score` descending, then `job_id`
  ascending — fully deterministic.
- **Expected aggregate (this dataset, this code):**
  `precision@5=0.92, precision@10=0.86, ndcg@10≈0.9498, mrr=1.0,
  ndcg_excluded_count=0, needs_review_excluded=1`.

## Results (v0, corpus-fitted TF-IDF)

| Metric | Aggregate |
|---|---|
| Precision@5 | 0.9200 |
| Precision@10 | 0.8600 |
| nDCG@10 | 0.9498 |
| MRR | 1.0000 |

Per-candidate:

| Candidate | P@5 | P@10 | nDCG@10 | MRR |
|---|---|---|---|---|
| c01_ml_fresher | 1.00 | 1.00 | 0.995 | 1.00 |
| c02_frontend_react_fresher | 1.00 | 0.90 | 0.963 | 1.00 |
| c03_devops_engineer | 1.00 | 1.00 | 0.996 | 1.00 |
| c04_vlsi_embedded | 1.00 | 0.60 | 1.000 | 1.00 |
| c05_java_backend_dev | 1.00 | 1.00 | 1.000 | 1.00 |
| c06_data_analyst | 1.00 | 1.00 | 1.000 | 1.00 |
| c07_android_dev | 0.20 | 0.10 | 0.639 | 1.00 |
| c08_security_analyst | 1.00 | 1.00 | 1.000 | 1.00 |
| c09_qa_engineer | 1.00 | 1.00 | 1.000 | 1.00 |
| c10_fullstack_unknown | 1.00 | 1.00 | 0.905 | 1.00 |

## Where v0 fails (do not fix yet — Gate 3+ scope)

- **c07_android_dev (P@5=0.20):** only j59 (Android Developer) is
  relevant. Every other job scores exactly 0.30 — zero skill overlap,
  zero keyword overlap, and `experience_match=1.0` for all
  no-requirement/fresher jobs. The weighted formula gives a flat
  0.30 tail with no discrimination among irrelevant jobs; ties break
  by job_id, so irrelevant jobs fill the top-10. Root cause: the
  experience signal (30% weight) rewards "no requirement" jobs even
  when skills are disjoint — a known formula property, not a bug.
- **Experience-floor blindness is asymmetric:** c04_vlsi_embedded
  scores j45 (VLSI Design, 1–3y required) below fresher-friendly jobs
  because `experience_match` penalizes the 0-yoe candidate — yet the
  label is still 1 (partially relevant). Ranking reflects the SPEC
  formula faithfully; whether that ordering is *desirable* is a
  product question for later gates.
- **Synonym/near-skill gaps:** e.g. c10_fullstack_unknown ranks
  j19/j20 (Django) top — correct — but jobs requiring only adjacent
  skills (j23 Node.js, j60 React Native) score mid-pack; TF-IDF over
  canonical names cannot credit "React experience ≈ frontend fit"
  beyond exact vocabulary overlap. This is the expected v0→v1
  (embeddings) motivation.
- **needs-review:** 1 pair (c10/j27) excluded — Microservices domain
  match with zero shared canonical skills.

## The 81% worked-example discrepancy

`MatchHire_Documentation_FINAL.pdf`'s "Concrete Worked Example" claims
component scores 0.78 / 1.00 / 0.60 → 81%. Those numbers came from
sklearn TF-IDF over **raw text** and raw keyword terms — a different
input representation than this engine's canonical skill sets and fixed
domain-keyword vocabulary. Under the v0 contract the same logical
inputs produce 0.5 / 1.0 / 0.0 → **0.55** (see `docs/DECISIONS.md`,
Gate 1 section). The document's numbers are not reproduced and are not
asserted; corpus-fitted IDF narrows but does not close the gap because
the inputs themselves differ (raw text vs canonical sets, and several
of the doc's "keywords" are not in the domain vocabulary).

## Limitations

1. Synthetic candidates/jobs — no production data.
2. Rubric labels correlate with matcher signal families (see above).
3. `needs-review` handling (pool exclusion) is one reasonable
   convention; alternatives exist.
4. P@k/MRR treat label 1 ("acceptable") as relevant — a stricter
   label-2-only variant would report lower numbers.
5. Flat-tail behavior (c07) shows the formula's weakness on
   zero-overlap pairs; nDCG@10 is robust to it only because relevant
   jobs still rank first.
