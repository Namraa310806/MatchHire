Project: MatchHire — a job aggregation + matching platform for India's Tier-2/3 freshers.

Core invariant (never violate): NO human, user, or admin can create a job. Jobs enter the system ONLY through automated fetchers from official company sources. There must be no API endpoint, serializer, admin form, or management shortcut that creates jobs outside the ingestion pipeline.

Stack: Django + DRF, PostgreSQL 15, Redis 7, Celery + Beat, React (React Query), Docker Compose, Playwright/requests for scraping, scikit-learn (TF-IDF), later sentence-transformers, Razorpay, Sentry, Flower.

Working rules:
1. Do only what the current prompt asks. Do not start the next phase.
2. Never fabricate numbers. Only report measurements actually taken on this machine.
3. Every phase ends with: tests run, results pasted, exact commands used.
4. Record non-obvious decisions in docs/DECISIONS.md (decision, alternatives, why).
5. Keep v0 implementations as reference when building v1 (matching, caching).
6. No secrets in the repo. Config via environment variables; provide .env.example.
7. Prefer boring, readable code. Type hints everywhere. Tests alongside code.
8. If a requirement conflicts with another or is ambiguous, stop and ask instead of guessing.
