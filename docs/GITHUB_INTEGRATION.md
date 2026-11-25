# GitHub Profile Integration (Phase 3C)

GitHub is a second candidate-evidence source alongside resume parsing.
Candidates connect a **public** GitHub account by username; the system
fetches public profile/repo metadata via the GitHub REST API and stores
extracted skills as `source="github"` evidence — never overwriting
resume/manual evidence.

## API Contract

All endpoints require authentication (JWT cookie for browsers,
`Authorization: Bearer` for non-browser clients) and operate only on the
caller's own connection.

### `POST /api/profile/github/`

Body: `{"github_username": "<login>"}` — bare username only (no URLs).
GitHub login rules enforced; stored lowercase-normalized.

- `202 Accepted` → `{"task_id", "status", "status_url"}` — connect or
  re-sync. A fresh `sync_token` is generated per request, invalidating
  all previously dispatched sync tasks.
- `400` — missing/invalid username (`error_category: invalid_username`).
- `404` — no GitHub user with that name (`user_not_found`).
- `409` — account already connected to another candidate
  (`account_conflict`), or username resolves to a different GitHub account
  than the connected identity (`identity_mismatch`; disconnect first).
- `429` — throttle (`github_sync` scope, `GITHUB_SYNC_THROTTLE_RATE`).
- `503` — GitHub unreachable/auth failure/dispatch failure; existing
  connection and evidence are left untouched.

Identity is resolved via `GET /users/{login}` **before** any DB write;
`github_user_id` (immutable numeric id) is the authoritative identity.
A username rename with the same id is followed; a different id is a
conflict, never a silent transfer.

### `GET /api/profile/github/`

Own connection state: `connected`, `github_username`, `github_login`,
`github_name`, `github_bio`, `public_repo_count`, `language_bytes`,
`connected_at`, `last_synced_at`, `pending_sync` (task_id/status/url).
`404` when not connected. Never exposes tokens or `sync_token`.

### `DELETE /api/profile/github/`

Disconnect: transactionally removes all `source="github"` skill evidence,
reconciles merged `CandidateSkill` membership, fails any pending sync
status (`disconnected`), and deletes the connection. Resume/manual
evidence and all Phase 3B extracted data are preserved. Idempotent `204`.

### `GET /api/profile/github/status/<task_id>/`

Own sync task status (`queued|processing|completed|partial|failed` +
safe `error_category`/`error_message`/`result` counts). `404` for other
candidates' tasks and expired records (existence not leaked).

## Sync Pipeline

```
POST -> validate username -> GET /users/{login} (cached)
     -> upsert connection + sync_token + active_sync_task_id
     -> queue sync_github_profile_task on parse_queue
     -> GET /users/{login} repos (paginated, cap GITHUB_MAX_REPOS)
     -> per eligible repo: GET languages + bounded README
        (skip forks, archived, empty repos; cap GITHUB_MAX_README_REPOS)
     -> extract_skills over name/description/topics/languages/README
     -> persist_github_sync: row lock + verify sync_token + github_user_id
        + replace github evidence + snapshot fields, one transaction
     -> invalidate matching caches -> publish status
```

- Language weighting: **bytes-by-language** aggregated across eligible
  repos (repo-size-by-language per playbook), stored in `language_bytes`.
- Skill evidence `detail`: `{"matched_alias", "origins": ["repo:owner/name", ...]}`
  (origins capped at 20). No proficiency, experience, or repo-count→skill
  inference.
- Repo metadata and README text are untrusted input: data-only into the
  shared extractor; API paths built only from validated `owner/repo` names.

## Reliability

- Per-task cache lock + terminal-status short-circuit (duplicate delivery).
- `sync_token` verified before fetch and again under `select_for_update`
  at persist: stale tasks fail `superseded`; a task can never recreate a
  deleted connection or restore removed evidence.
- **Ownership contract:** the DB fencing token (`exec_fencing`, incremented
  under the row lock per execution via `claim_execution_fencing`) — not
  Redis lock acquisition — formally transfers execution ownership. The
  Redis lock (atomic SET NX + Lua compare-and-renew/delete, renewed every
  300s) is a duplicate-delivery/efficiency guard; `owns()` is only an
  early-out. A successor's Redis acquire alone does not fence out the
  current owner — only its fencing claim does, verified inside the persist
  transaction.
- Identity re-verified at persist (`identity_mismatch` on change).
- Disconnect serializes with persist via the connection row lock.
- Transient errors (timeout, connection error, 429, 5xx, Redis) retry
  ≤3 with backoff honoring `Retry-After`; permanent errors fail with safe
  categories. Failed syncs preserve the last successful snapshot and
  evidence.
- Non-benign stage failures (unexpected per-repo API errors, extraction
  failure) degrade to `partial` and **persist nothing**: the last complete
  successful snapshot and github evidence are preserved. Benign 404s
  (repo/README deleted since listing) do not count as stage errors.
- Transient per-repo errors (429/5xx/timeout) abort the whole sync for
  task-level retry rather than producing a partial write.

## Token handling

`GITHUB_TOKEN` env var is an optional shared server-side token for rate
limits (60→5000 req/hr). No per-user GitHub credentials exist or are
stored. The token is never logged, serialized, or returned by any endpoint.

## Environment variables

See `.env.example`: `GITHUB_TOKEN`, `GITHUB_API_BASE_URL`,
`GITHUB_API_TIMEOUT_SECONDS`, `GITHUB_API_CACHE_TTL_SECONDS`,
`GITHUB_TASK_STATUS_TTL_SECONDS`, `GITHUB_MAX_REPOS`,
`GITHUB_MAX_README_REPOS`, `GITHUB_SYNC_THROTTLE_RATE`.

## Known limitations

- Public data only; no private repos, code crawling, commit analysis, or
  contribution scoring.
- Without `GITHUB_TOKEN`, syncs of large accounts may hit the 60 req/hr
  unauthenticated limit (retries apply; set the token for production).
- Successful GitHub GETs are cached (`GITHUB_API_CACHE_TTL_SECONDS`,
  default 1h), so re-syncs may serve slightly stale public data.
- `public_repo_count` reflects GitHub's count, not the fetched subset.
- Live GitHub behavior verified only via mocks/fixtures; no live-integration
  claims.
