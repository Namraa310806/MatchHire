"""Minimal GitHub REST API client for profile ingestion.

Uses ``requests.Session`` per project convention. Successful GET responses
are cached in the Django cache (Redis in deployment) to avoid re-fetching.
Only public, unauthenticated-scope data is requested; a shared server-side
``GITHUB_TOKEN`` env var is used for rate limits when configured. Tokens
are never logged or exposed.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Any, cast

import requests
from django.conf import settings
from django.core.cache import cache

from api.github.validation import is_valid_repo_full_name

logger = logging.getLogger(__name__)

API_VERSION_HEADER = "2022-11-28"
USER_AGENT = "MatchHire-GitHub/1.0 (+https://github.com/Namraa310806/MatchHire)"
README_MAX_CHARS = 100_000
CACHE_PREFIX = "github:api:"


class GitHubAPIError(Exception):
    """Base class for GitHub API failures."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        retry_after: int | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class GitHubUserNotFoundError(GitHubAPIError):
    """GitHub returned 404 (user or resource does not exist)."""


class GitHubAuthError(GitHubAPIError):
    """401, or 403 not attributable to rate limiting (bad/forbidden token)."""


class GitHubRateLimitError(GitHubAPIError):
    """429, or 403 with exhausted rate limit (transient; retry later)."""


class GitHubServerError(GitHubAPIError):
    """5xx responses (transient)."""


class GitHubInvalidResponseError(GitHubAPIError):
    """2xx response with an unexpected payload shape."""


@dataclass
class GitHubUser:
    """Validated subset of ``GET /users/{username}``."""

    id: int
    login: str
    name: str = ""
    bio: str = ""
    public_repos: int = 0


@dataclass
class GitHubRepo:
    """Validated subset of a repository listing entry."""

    full_name: str
    name: str
    description: str = ""
    topics: list[str] = field(default_factory=list)
    size_kb: int = 0
    fork: bool = False
    archived: bool = False
    pushed_at: str = ""


class GitHubClient:
    """Thin wrapper around the GitHub REST API."""

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float | None = None,
    ):
        self.base_url = (base_url or settings.GITHUB_API_BASE_URL).rstrip("/")
        self.token = token if token is not None else settings.GITHUB_TOKEN
        self.timeout = (
            timeout if timeout is not None else settings.GITHUB_API_TIMEOUT_SECONDS
        )
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": API_VERSION_HEADER,
            }
        )
        if self.token:
            self._session.headers["Authorization"] = f"Bearer {self.token}"

    # -- public API -----------------------------------------------------

    def get_user(self, username: str) -> GitHubUser:
        """Fetch and validate ``GET /users/{username}``."""
        payload = self._get_json(f"/users/{username}")
        if not isinstance(payload, dict):
            raise GitHubInvalidResponseError("User payload is not an object")
        user_id = payload.get("id")
        login = payload.get("login")
        if not isinstance(user_id, int) or isinstance(user_id, bool):
            raise GitHubInvalidResponseError("User payload missing numeric id")
        if not isinstance(login, str) or not login:
            raise GitHubInvalidResponseError("User payload missing login")
        name = payload.get("name")
        bio = payload.get("bio")
        public_repos = payload.get("public_repos")
        return GitHubUser(
            id=user_id,
            login=login,
            name=name if isinstance(name, str) else "",
            bio=bio if isinstance(bio, str) else "",
            public_repos=public_repos if isinstance(public_repos, int) else 0,
        )

    def list_user_repos(self, username: str, max_repos: int) -> list[GitHubRepo]:
        """Fetch up to ``max_repos`` public repos, most recently pushed first."""
        repos: list[GitHubRepo] = []
        page = 1
        per_page = 100
        while len(repos) < max_repos:
            payload = self._get_json(
                f"/users/{username}/repos",
                params={"per_page": per_page, "page": page, "sort": "pushed"},
            )
            if not isinstance(payload, list):
                raise GitHubInvalidResponseError("Repos payload is not a list")
            if not payload:
                break
            for item in payload:
                repo = _parse_repo(item)
                if repo is not None:
                    repos.append(repo)
                if len(repos) >= max_repos:
                    break
            if len(payload) < per_page:
                break
            page += 1
        return repos

    def get_repo_languages(self, repo_full_name: str) -> dict[str, int]:
        """Fetch ``GET /repos/{owner}/{repo}/languages`` (bytes per language)."""
        if not is_valid_repo_full_name(repo_full_name):
            raise GitHubInvalidResponseError(
                f"Invalid repo full name: {repo_full_name!r}"
            )
        payload = self._get_json(f"/repos/{repo_full_name}/languages")
        if not isinstance(payload, dict):
            raise GitHubInvalidResponseError("Languages payload is not an object")
        result: dict[str, int] = {}
        for lang, byte_count in payload.items():
            if isinstance(lang, str) and isinstance(byte_count, (int, float)):
                result[lang] = int(byte_count)
        return result

    def get_readme(self, repo_full_name: str) -> str:
        """Fetch raw README text (``Accept: raw``), capped at README_MAX_CHARS."""
        if not is_valid_repo_full_name(repo_full_name):
            raise GitHubInvalidResponseError(
                f"Invalid repo full name: {repo_full_name!r}"
            )
        text = self._get_text(
            f"/repos/{repo_full_name}/readme",
            headers={"Accept": "application/vnd.github.raw"},
        )
        return text[:README_MAX_CHARS]

    # -- internals --------------------------------------------------------

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        resp = self._request("GET", path, params=params)
        try:
            return resp.json()
        except ValueError as exc:
            raise GitHubInvalidResponseError("Response is not valid JSON") from exc

    def _get_text(self, path: str, headers: dict[str, str] | None = None) -> str:
        resp = self._request("GET", path, headers=headers)
        return resp.text

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        url = f"{self.base_url}{path}"
        cache_key = self._cache_key(method, url, params)

        cached = cache.get(cache_key)
        if cached is not None:
            return cast(requests.Response, _CachedResponse(cached))

        try:
            resp = self._session.request(
                method, url, params=params, headers=headers, timeout=self.timeout
            )
        except (requests.Timeout, requests.ConnectionError):
            raise  # transient; caller/task handles retry

        self._raise_for_status(resp)

        # Cache successful GET responses only.
        try:
            body: Any
            if "json" in resp.headers.get("Content-Type", ""):
                body = resp.json()
            else:
                body = resp.text
            cache.set(
                cache_key,
                {"status_code": resp.status_code, "body": body},
                timeout=settings.GITHUB_API_CACHE_TTL_SECONDS,
            )
        except (ValueError, TypeError):
            pass  # caching is best-effort; never fail the request for it

        return resp

    @staticmethod
    def _cache_key(method: str, url: str, params: dict[str, Any] | None) -> str:
        raw = json.dumps(
            {"method": method, "url": url, "params": params or {}},
            sort_keys=True,
        )
        return CACHE_PREFIX + hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _raise_for_status(resp: requests.Response) -> None:
        status = resp.status_code
        if status < 400:
            return

        retry_after = _parse_retry_after(resp)
        message = f"GitHub API returned HTTP {status} for {resp.url}"

        if status == 404:
            raise GitHubUserNotFoundError(message, status_code=status)
        if status == 401:
            raise GitHubAuthError(message, status_code=status)
        if status == 429 or (status == 403 and _is_rate_limited(resp)):
            raise GitHubRateLimitError(
                message, status_code=status, retry_after=retry_after
            )
        if status == 403:
            raise GitHubAuthError(message, status_code=status)
        if status >= 500:
            raise GitHubServerError(message, status_code=status)
        raise GitHubAPIError(message, status_code=status)


class _CachedResponse:
    """Minimal requests.Response stand-in for cache hits."""

    def __init__(self, payload: dict[str, Any]):
        self.status_code = payload["status_code"]
        self._body = payload["body"]
        self.headers = {"Content-Type": "application/json"}
        self.url = ""

    def json(self) -> Any:
        return self._body

    @property
    def text(self) -> str:
        return self._body if isinstance(self._body, str) else json.dumps(self._body)


def _parse_repo(item: Any) -> GitHubRepo | None:
    """Extract validated fields from a repo listing entry; None if unusable."""
    if not isinstance(item, dict):
        return None
    full_name = item.get("full_name")
    name = item.get("name")
    if not is_valid_repo_full_name(full_name) or not isinstance(name, str):
        return None
    topics = item.get("topics")
    size = item.get("size")
    description = item.get("description")
    pushed_at = item.get("pushed_at")
    return GitHubRepo(
        full_name=cast(str, full_name),
        name=name,
        description=description if isinstance(description, str) else "",
        topics=[t for t in topics if isinstance(t, str)]
        if isinstance(topics, list)
        else [],
        size_kb=size if isinstance(size, int) else 0,
        fork=bool(item.get("fork")),
        archived=bool(item.get("archived")),
        pushed_at=pushed_at if isinstance(pushed_at, str) else "",
    )


def _is_rate_limited(resp: requests.Response) -> bool:
    remaining = resp.headers.get("X-RateLimit-Remaining")
    if remaining == "0":
        return True
    retry_after = resp.headers.get("Retry-After")
    if retry_after:
        return True
    return False


def _parse_retry_after(resp: requests.Response) -> int | None:
    retry_after = resp.headers.get("Retry-After")
    if retry_after:
        try:
            return int(retry_after)
        except ValueError:
            pass
    reset = resp.headers.get("X-RateLimit-Reset")
    if reset:
        try:
            import time

            delta = int(reset) - int(time.time())
            return max(delta, 0)
        except ValueError:
            pass
    return None


# Module-level convenience used by views/tasks; tests monkeypatch these names.
def get_user(username: str) -> GitHubUser:
    return GitHubClient().get_user(username)


def list_user_repos(username: str, max_repos: int) -> list[GitHubRepo]:
    return GitHubClient().list_user_repos(username, max_repos)


def get_repo_languages(repo_full_name: str) -> dict[str, int]:
    return GitHubClient().get_repo_languages(repo_full_name)


def get_readme(repo_full_name: str) -> str:
    return GitHubClient().get_readme(repo_full_name)
