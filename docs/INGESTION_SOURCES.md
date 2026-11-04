# MatchHire Ingestion Sources Research

This document records research into publicly accessible job sources for Phase 2B implementation.

## General Principles

- Sources must be publicly accessible without authentication
- Must respect robots.txt and rate limits
- Must not require CAPTCHA solving or bypassing anti-bot protections
- Must not violate terms of service
- Legal review required for gray-area sources
- Prioritize stable, well-documented ATS ecosystems

## Candidate Sources

### 1. Greenhouse ATS

**Company Example:** Stripe

**Career Page URL:** https://boards.greenhouse.io/stripe

**Official Job Endpoint:** `GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true`

**ATS/Platform:** Greenhouse

**Endpoint Response Format:** JSON
```json
{
  "jobs": [
    {
      "id": 8172510,
      "title": "Abuse Investigator",
      "location": {"name": "Seattle, San Francisco, New York City"},
      "absolute_url": "https://stripe.com/jobs/search?gh_jid=8172510",
      "updated_at": "2026-10-29T10:42:09-04:00",
      "first_published": "2026-09-09T10:50:29-04:00",
      "content": "<h2>...</h2>",  // HTML-escaped description
      "departments": [...],
      "offices": [...]
    }
  ],
  "meta": {"total": 702}
}
```

**Required Request Headers:** None (User-Agent recommended)

**Pagination Behavior:** None - all jobs returned in single response

**Rate Limits:** Not documented in public API documentation; no explicit rate limit observed during testing

**Terms and Robots Policy:**
- robots.txt URL: https://boards-api.greenhouse.io/robots.txt
- robots.txt observed: `Disallow: /embed/` (job board API path is allowed)
- Greenhouse official API documentation: https://developers.greenhouse.io/harvest.html
- Authentication not required for public GET endpoints
- Data is publicly available for career page integration
- robots.txt permission does not automatically establish legal permission for all uses

**Application URL:** Available in `absolute_url` field

**Date Checked:** 2026-11-03

**Selected for Implementation:** Yes - Stripe

**Rationale:**
- Well-documented public API
- No authentication required
- Stable response structure
- Direct application URLs
- All jobs in one response (no pagination complexity)
- robots.txt allows access

---

### 2. Lever ATS

**Company Example:** Spotify

**Career Page URL:** https://jobs.lever.co/spotify

**Official Job Endpoint:** `GET https://api.lever.co/v0/postings/{slug}?mode=json`

**ATS/Platform:** Lever

**Endpoint Response Format:** JSON (bare array, not object wrapper)
```json
[
  {
    "id": "2a55d6c9-c564-443a-be3e-a3851db5a93b",
    "text": "Account Executive - Commercial",
    "categories": {
      "location": "New York, NY",
      "commitment": "Permanent",
      "department": "Operations and Business Support",
      "team": "Platform",
      "allLocations": ["New York, NY"]
    },
    "workplaceType": "onsite",
    "createdAt": 1792767640768,  // Unix timestamp in milliseconds
    "hostedUrl": "https://jobs.lever.co/spotify/2a55d6c9...",
    "applyUrl": "https://jobs.lever.co/spotify/2a55d6c9.../apply",
    "descriptionPlain": "...",
    "description": "<div>...</div>",
    "lists": [...]
  }
]
```

**Required Request Headers:** None (User-Agent recommended)

**Pagination Behavior:** Optional - `skip` and `limit` query parameters available
- Implementation: Not used in Phase 2B (all jobs fetched in single response)

**Rate Limits:**
- robots.txt specifies `Crawl-delay: 1` (recommend 1 second between requests)
- No explicit API rate limit documented
- Current implementation: Single HTTP request per invocation (no pagination = no additional requests)
- Enforcement: Not enforced in code (only documented)
- Future scheduling: When repeated ingestion is introduced, must respect 1-second crawl-delay between invocations

**Terms and Robots Policy:**
- robots.txt URL: https://api.lever.co/robots.txt
- robots.txt observed: `Allow: /` with `Crawl-delay: 1`
- Lever official API documentation: https://www.lever.co/developer/documentation
- EU companies use `api.eu.lever.co` instead of `api.lever.co`
- No authentication required for public endpoints
- Content signals allow search indexing
- AI training crawlers explicitly disallowed
- robots.txt permission does not automatically establish legal permission for all uses

**Application URL:** Available in `applyUrl` field

**Date Checked:** 2026-11-03

**Selected for Implementation:** Yes - Spotify

**Rationale:**
- Public API with no authentication
- Plain-text description available (`descriptionPlain`)
- Structured categories for location, commitment, team
- Application URL directly available
- robots.txt allows with crawl-delay
- EU endpoint availability for European companies

**Notes:**
- Response is bare JSON array, not object with `jobs` key
- `createdAt` is Unix timestamp in milliseconds, not ISO string
- Salary data in `salaryRange` field when companies publish it (optional)

---

### 3. Ashby ATS

**Company Example:** Notion

**Career Page URL:** https://jobs.ashbyhq.com/notion

**Official Job Endpoint:** `GET https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true`

**ATS/Platform:** Ashby

**Endpoint Response Format:** JSON
```json
{
  "jobPostings": [
    {
      "title": "Software Engineer",
      "locationId": "remote",
      "employmentType": "FULL_TIME",
      "description": "...",
      "publishedDate": "2024-01-01T00:00:00Z",
      "compensation": {
        "amount": {...}
      }
    }
  ]
}
```

**Required Request Headers:** None

**Pagination Behavior:** Not documented in public samples

**Rate Limits:** Not documented

**Terms and Robots Policy:**
- robots.txt URL: https://api.ashbyhq.com/robots.txt
- robots.txt observed: `Disallow: /api/` (API path disallowed)
- Authentication not required for public job board endpoints
- robots.txt disallow prevents implementation

**Application URL:** Available in hosted URL field

**Date Checked:** 2026-11-03

**Selected for Implementation:** No - robots.txt disallows `/api/` path

**Rationale for Rejection:**
- robots.txt explicitly disallows `/api/` path
- Cannot proceed without explicit permission or different endpoint
- Better to use sources with clear robots.txt permission

---

## Implementation Rate-Limit Behavior

### Current Implementation (Phase 2B)

**Stripe (Greenhouse):**
- HTTP requests per invocation: 1 (single fetch, no pagination)
- Pagination requests: 0 (all jobs in single response)
- Rate-limit enforcement: None (no documented rate limit)
- Request frequency control: Manual invocation only (no scheduling in Phase 2B)
- Future consideration: Reasonable polling (daily or hourly) when scheduling is added

**Spotify (Lever):**
- HTTP requests per invocation: 1 (single fetch, no pagination used)
- Pagination requests: 0 (skip/limit available but not used in Phase 2B)
- Rate-limit enforcement: None (crawl-delay is documented but not enforced in code)
- Request frequency control: Manual invocation only (no scheduling in Phase 2B)
- Future requirement: Must respect 1-second crawl-delay when repeated ingestion is introduced

### Rate-Limit Limitations

**Current Limitations:**
- No automatic enforcement of rate limits in code
- No request throttling mechanism
- No backoff strategy for 429 responses
- No metrics for request frequency tracking
- Manual invocation only (no scheduling infrastructure)

**Future Requirements (Out of Scope for Phase 2B):**
- Implement request throttling before adding scheduling
- Add exponential backoff for 429 responses
- Track request frequency per source
- Enforce crawl-delay constraints when repeated ingestion is introduced
- Consider rate-limit-aware scheduling (e.g., spread sources over time window)

---

## Research Date

**Document Last Updated:** 2026-11-03

**Phase:** Phase 2B - First Real Company Scrapers
