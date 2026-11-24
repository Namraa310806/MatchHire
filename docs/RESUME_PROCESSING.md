# Resume Processing Pipeline (Phase 3B)

This document describes the asynchronous resume upload and parsing pipeline,
its API contract, storage configuration, failure handling, and deletion
semantics. It implements Decision 9 (consent/retention/deletion) and reuses
the Phase 3A shared extraction engine (`api/extraction/`).

## API Contract

All endpoints require authentication (JWT via httpOnly cookie for browsers,
`Authorization: Bearer` for non-browser clients).

### `POST /api/resumes/`

Multipart upload. Fields:

- `file` — the resume PDF (required)
- `consent` — must be a truthy value (`true`, `1`, `on`, `yes`); explicit
  consent is mandatory per Decision 9

Responses:

- `202 Accepted`
  ```json
  {
    "task_id": "<uuid>",
    "status": "queued",
    "status_url": "/api/resumes/status/<uuid>/"
  }
  ```
  `status` reflects the record after dispatch; under synchronous/eager
  execution it may already be `completed`, `partial`, or `failed`.
- `400 Bad Request` — missing consent, missing file, invalid/corrupt/
  encrypted/oversized PDF. Body includes `error_category`.
- `401/403` — unauthenticated.
- `429` — upload rate limit exceeded.
- `503` — storage or task-dispatch failure (state is rolled back; no
  orphaned files).

### `GET /api/resumes/status/<task_id>/`

Returns the caller's own task status. Other candidates' tasks and
missing/expired records both return `404` (existence is not leaked).

```json
{
  "task_id": "<uuid>",
  "status": "queued|processing|completed|partial|failed",
  "error_category": null,
  "error_message": null,
  "result": {
    "skills_found": 6,
    "skills_linked": 6,
    "domain_keywords": 2,
    "experience_years": 2.0,
    "experience_confidence": "high",
    "pages": 1,
    "sections_found": ["education", "experience", "skills", "summary"],
    "stage_errors": []
  },
  "created_at": "...",
  "updated_at": "..."
}
```

`result` never contains resume text, PII, filesystem paths, or internal
exception details.

### `DELETE /api/resumes/`

Deletes the stored resume file and clears `resume_file`,
`resume_uploaded_at`, and `resume_consent_given`. Per Decision 9, extracted
profile data (skills, domain keywords, experience estimate) is **retained**.
Idempotent: `204` even when no resume exists. Any in-flight parse task for
the deleted file fails with `resume_deleted`/`resume_replaced`.

## Pipeline

```
Upload -> validate bytes (magic, PyMuPDF open, encryption, size)
       -> store at resumes/<profile_id>/<uuid>.pdf
       -> queue parse_resume_task on parse_queue
       -> extract text (PyMuPDF, no OCR)
       -> segment sections (conservative heading detection)
       -> extract_skills / extract_domain_keywords / estimate_experience_years
       -> persist profile data in one transaction
       -> invalidate matching caches
       -> publish status
```

Scanned PDFs (no usable text layer) fail with `no_text_layer`; nothing is
fabricated. Stage-level extraction failures degrade to `partial` when at
least one stage produced data, `failed` otherwise.

## Task lifecycle and reliability

- Status records live in the Django cache (Redis in deployment) under
  `resume:task:<task_id>` with TTL `RESUME_TASK_STATUS_TTL_SECONDS`
  (default 24h — **proposed, pending approval**; matches the Celery result
  expiry convention).
- Celery task ID equals the status task ID (`apply_async(task_id=...)`).
- Terminal statuses are never reprocessed; a per-task cache lock prevents
  concurrent duplicate execution.
- `expected_resume_name` staleness check (before storage read and again
  inside the persistence transaction) ensures an old task cannot overwrite
  results from a newer upload.
- Transient errors (storage `OSError`, DB `OperationalError`, Redis) retry
  with backoff, max 3 retries. Permanent validation errors never retry.
- Skill/domain/experience extraction never overwrites an explicitly set
  `total_experience_years`; the estimate only fills an unset value.

## Storage

`CandidateProfile.resume_file` uses Django's default storage:

- **Local (default):** `FileSystemStorage` rooted at `MEDIA_ROOT`
  (default `<backend>/media`).
- **S3/R2:** set `AWS_STORAGE_BUCKET_NAME` (plus optional
  `AWS_S3_REGION_NAME`, `AWS_S3_ENDPOINT_URL` for R2, `AWS_ACCESS_KEY_ID`,
  `AWS_SECRET_ACCESS_KEY`). `django-storages` `S3Boto3Storage` is selected
  automatically; `AWS_S3_FILE_OVERWRITE=False` prevents clobbering.

Filenames are server-generated (`resumes/<id>/<uuid>.pdf`); user input
never reaches storage paths.

## Validation rules

- Size limit: `RESUME_MAX_UPLOAD_BYTES` (default 10 MiB — **proposed**).
- Magic bytes `%PDF-` required; extension/MIME/Content-Type are ignored.
- Document must open in PyMuPDF, have >=1 page, and be unencrypted.
- No page-count limit is enforced (none is specified in SPEC).
- Minimum extracted text: `RESUME_MIN_TEXT_LENGTH` (default 20 chars).

## Rate limiting

`POST /api/resumes/` uses DRF `ScopedRateThrottle`, scope `resume_upload`,
rate `RESUME_UPLOAD_THROTTLE_RATE` (default `10/hour` — **proposed**).
Auth endpoints use scope `auth_token` (`AUTH_THROTTLE_RATE`, default
`20/minute` — **proposed**).

## Environment variables

See `.env.example`. New variables: `MEDIA_ROOT`, `AWS_STORAGE_BUCKET_NAME`,
`AWS_S3_REGION_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, `REDIS_CACHE_URL`, `RESUME_MAX_UPLOAD_BYTES`,
`RESUME_TASK_STATUS_TTL_SECONDS`, `RESUME_MIN_TEXT_LENGTH`,
`RESUME_UPLOAD_THROTTLE_RATE`, `AUTH_THROTTLE_RATE`, `JWT_COOKIE_SECURE`,
`JWT_COOKIE_SAMESITE`, `JWT_COOKIE_DOMAIN`.

## Known limitations

- No OCR: scanned/image-only PDFs are rejected with `no_text_layer`.
- Section segmentation is conservative; unrecognized layouts still yield
  full-text extraction.
- Experience estimate is stored only when `total_experience_years` is unset
  and carries no explicit-vs-estimated flag (schema limitation).
- Domain keywords are persisted on the profile as a JSON list; there is no
  dedicated relational table yet.
- Retention periods for resume files and derived data remain unresolved
  (Decision 9); no automatic deletion is implemented.
