"""Tests for GitHub connection APIs and sync task (Phase 3C, Gates 3-4).

All GitHub HTTP calls are mocked via ``api.github.client`` module functions;
no live network access. Celery dispatch is routed through synchronous
``apply()`` (same convention as resume tests).
"""

from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import pytest
from celery.exceptions import Ignore
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from api import evidence
from api.github import status as github_status
from api.github.client import GitHubRepo, GitHubUser
from api.models import (
    CandidateGitHubProfile,
    CandidateProfile,
    CandidateSkill,
    CandidateSkillEvidence,
    Skill,
)
from api.tasks import sync_github_profile_task

User = get_user_model()


@pytest.fixture(autouse=True)
def _eager_github_dispatch(monkeypatch):
    """Make GitHub sync dispatch synchronous in tests."""

    def _apply_async(args=None, kwargs=None, task_id=None, **_kwargs):
        return sync_github_profile_task.apply(args=args, kwargs=kwargs, task_id=task_id)

    monkeypatch.setattr(
        "api.github.views.sync_github_profile_task.apply_async", _apply_async
    )


@pytest.fixture
def gh(monkeypatch):
    """Mock all GitHub client module functions."""
    mocks = SimpleNamespace(
        get_user=Mock(
            return_value=GitHubUser(
                id=12345,
                login="TestUser",
                name="Test",
                bio="bio",
                public_repos=3,
            )
        ),
        list_user_repos=Mock(return_value=[]),
        get_repo_languages=Mock(return_value={}),
        get_readme=Mock(return_value=""),
    )
    monkeypatch.setattr("api.github.client.get_user", mocks.get_user)
    monkeypatch.setattr("api.github.client.list_user_repos", mocks.list_user_repos)
    monkeypatch.setattr(
        "api.github.client.get_repo_languages", mocks.get_repo_languages
    )
    monkeypatch.setattr("api.github.client.get_readme", mocks.get_readme)
    return mocks


def _profile(email: str = "gh@example.com") -> CandidateProfile:
    user = User.objects.create_user(email=email, password="Str0ng!Pass")
    profile, _ = CandidateProfile.objects.get_or_create(user=user)
    return cast(CandidateProfile, profile)


def _client(profile: CandidateProfile) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=profile.user)
    return client


def _repo(
    full_name: str = "testuser/demo",
    *,
    name: str = "demo",
    description: str = "",
    topics: list[str] | None = None,
    size_kb: int = 100,
    fork: bool = False,
    archived: bool = False,
) -> GitHubRepo:
    return GitHubRepo(
        full_name=full_name,
        name=name,
        description=description,
        topics=topics or [],
        size_kb=size_kb,
        fork=fork,
        archived=archived,
        pushed_at="2026-01-01T00:00:00Z",
    )


@pytest.mark.django_db
class TestAuthAndValidation:
    def test_unauthenticated_rejected(self, db):
        client = APIClient()
        assert client.post("/api/profile/github/", {}, format="json").status_code in (
            401,
            403,
        )
        assert client.get("/api/profile/github/").status_code in (401, 403)
        assert client.delete("/api/profile/github/").status_code in (401, 403)
        assert client.get("/api/profile/github/status/abc/").status_code in (
            401,
            403,
        )

    @pytest.mark.parametrize(
        "bad",
        [
            "",
            "not a user",
            "https://github.com/foo",
            "-lead",
            "trail-",
            "a" * 40,
            "user@x.com",
            None,
            123,
        ],
    )
    def test_invalid_usernames_rejected(self, bad, gh):
        profile = _profile()
        resp = _client(profile).post(
            "/api/profile/github/", {"github_username": bad}, format="json"
        )
        assert resp.status_code == 400
        assert resp.json()["error_category"] == "invalid_username"
        assert not CandidateGitHubProfile.objects.exists()

    def test_case_normalization(self, gh):
        profile = _profile()
        resp = _client(profile).post(
            "/api/profile/github/", {"github_username": "  TestUser "}, format="json"
        )
        assert resp.status_code == 202
        conn = CandidateGitHubProfile.objects.get(profile=profile)
        assert conn.github_username == "testuser"
        assert conn.github_login_raw == "TestUser"


@pytest.mark.django_db
class TestConnect:
    def test_successful_connect(self, gh):
        profile = _profile()
        resp = _client(profile).post(
            "/api/profile/github/", {"github_username": "testuser"}, format="json"
        )
        assert resp.status_code == 202
        body = resp.json()
        assert body["task_id"] and body["status_url"].endswith("/")

        conn = CandidateGitHubProfile.objects.get(profile=profile)
        assert conn.github_user_id == 12345
        assert conn.sync_token is not None
        # Eager task completed: snapshot written, pending task cleared.
        conn.refresh_from_db()
        assert conn.last_synced_at is not None
        assert conn.active_sync_task_id is None
        assert conn.github_name == "Test"
        assert conn.public_repo_count == 3

        record = github_status.get_status(body["task_id"])
        assert record["status"] == "completed"

    def test_unknown_user_404(self, gh):
        from api.github.client import GitHubUserNotFoundError

        gh.get_user.side_effect = GitHubUserNotFoundError("nf", status_code=404)
        profile = _profile()
        resp = _client(profile).post(
            "/api/profile/github/", {"github_username": "ghost"}, format="json"
        )
        assert resp.status_code == 404
        assert not CandidateGitHubProfile.objects.exists()

    def test_api_failure_503_no_state_change(self, gh):
        from api.github.client import GitHubServerError

        gh.get_user.side_effect = GitHubServerError("boom", status_code=500)
        profile = _profile()
        resp = _client(profile).post(
            "/api/profile/github/", {"github_username": "testuser"}, format="json"
        )
        assert resp.status_code == 503
        assert resp.json()["error_category"] == "github_unavailable"
        assert not CandidateGitHubProfile.objects.exists()

    def test_same_account_other_candidate_409(self, gh):
        other = _profile("other@example.com")
        CandidateGitHubProfile.objects.create(
            profile=other,
            github_user_id=12345,
            github_username="testuser",
        )
        profile = _profile()
        resp = _client(profile).post(
            "/api/profile/github/", {"github_username": "testuser"}, format="json"
        )
        assert resp.status_code == 409
        assert resp.json()["error_category"] == "account_conflict"

    def test_resync_rotates_token(self, gh):
        profile = _profile()
        c = _client(profile)
        c.post("/api/profile/github/", {"github_username": "testuser"}, format="json")
        conn = CandidateGitHubProfile.objects.get(profile=profile)
        first_token = conn.sync_token
        assert first_token is not None

        resp = c.post(
            "/api/profile/github/", {"github_username": "testuser"}, format="json"
        )
        assert resp.status_code == 202
        conn.refresh_from_db()
        assert conn.sync_token != first_token

    def test_different_account_same_candidate_409(self, gh):
        profile = _profile()
        c = _client(profile)
        c.post("/api/profile/github/", {"github_username": "testuser"}, format="json")
        conn = CandidateGitHubProfile.objects.get(profile=profile)
        original_id = conn.github_user_id

        gh.get_user.return_value = GitHubUser(id=99999, login="other", name="O")
        resp = c.post(
            "/api/profile/github/", {"github_username": "other"}, format="json"
        )
        assert resp.status_code == 409
        conn.refresh_from_db()
        assert conn.github_user_id == original_id
        assert conn.github_username == "testuser"

    def test_rename_same_id_allowed(self, gh):
        profile = _profile()
        conn = CandidateGitHubProfile.objects.create(
            profile=profile,
            github_user_id=12345,
            github_username="oldname",
            github_login_raw="OldName",
        )
        gh.get_user.return_value = GitHubUser(
            id=12345, login="NewName", name="N", public_repos=1
        )
        resp = _client(profile).post(
            "/api/profile/github/", {"github_username": "newname"}, format="json"
        )
        assert resp.status_code == 202
        conn.refresh_from_db()
        assert conn.github_username == "newname"
        assert conn.github_login_raw == "NewName"
        assert conn.github_user_id == 12345  # same immutable identity

    def test_dispatch_failure_rolls_back(self, gh, monkeypatch):
        profile = _profile()
        monkeypatch.setattr(
            "api.github.views.sync_github_profile_task.apply_async",
            Mock(side_effect=RuntimeError("broker down")),
        )
        resp = _client(profile).post(
            "/api/profile/github/", {"github_username": "testuser"}, format="json"
        )
        assert resp.status_code == 503
        assert not CandidateGitHubProfile.objects.filter(profile=profile).exists()


@pytest.mark.django_db
class TestGetAndStatus:
    def test_get_own_connection(self, gh):
        profile = _profile()
        c = _client(profile)
        c.post("/api/profile/github/", {"github_username": "testuser"}, format="json")
        resp = c.get("/api/profile/github/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["connected"] is True
        assert body["github_username"] == "testuser"
        assert "sync_token" not in str(body)
        assert "token" not in {k.lower() for k in body}

    def test_get_no_connection_404(self, db):
        profile = _profile()
        resp = _client(profile).get("/api/profile/github/")
        assert resp.status_code == 404

    def test_status_owner_only(self, gh):
        profile = _profile()
        other = _profile("other2@example.com")
        resp = _client(profile).post(
            "/api/profile/github/", {"github_username": "testuser"}, format="json"
        )
        task_id = resp.json()["task_id"]

        own = _client(profile).get(f"/api/profile/github/status/{task_id}/")
        assert own.status_code == 200
        assert own.json()["status"] == "completed"

        foreign = _client(other).get(f"/api/profile/github/status/{task_id}/")
        assert foreign.status_code == 404
        missing = _client(profile).get("/api/profile/github/status/nope/")
        assert missing.status_code == 404


@pytest.mark.django_db
class TestDisconnect:
    def _connected_with_evidence(self, gh):
        profile = _profile()
        c = _client(profile)
        c.post("/api/profile/github/", {"github_username": "testuser"}, format="json")
        # Simulate evidence from all three sources.
        skills = {
            n: Skill.objects.create(name=n, category="t")
            for n in ("Python", "Django", "React")
        }
        evidence.link_skill(profile, skills["Python"], source="manual")
        evidence.link_skill(profile, skills["Django"], source="resume")
        evidence.link_skill(profile, skills["React"], source="github")
        return profile, c, skills

    def test_disconnect_removes_only_github(self, gh):
        profile, c, skills = self._connected_with_evidence(gh)
        resp = c.delete("/api/profile/github/")
        assert resp.status_code == 204

        assert not CandidateGitHubProfile.objects.filter(profile=profile).exists()
        remaining = set(
            CandidateSkill.objects.filter(candidate=profile).values_list(
                "skill__name", flat=True
            )
        )
        assert remaining == {"Python", "Django"}  # React had only github evidence
        sources = set(
            CandidateSkillEvidence.objects.filter(candidate=profile).values_list(
                "source", flat=True
            )
        )
        assert sources == {"manual", "resume"}

    def test_disconnect_idempotent(self, gh):
        profile, c, _ = self._connected_with_evidence(gh)
        assert c.delete("/api/profile/github/").status_code == 204
        assert c.delete("/api/profile/github/").status_code == 204

    def test_disconnect_fails_pending_status(self, gh):
        profile = _profile()
        import uuid

        CandidateGitHubProfile.objects.create(
            profile=profile,
            github_user_id=1,
            github_username="testuser",
            sync_token=uuid.uuid4(),
            active_sync_task_id="pending-task",
        )
        github_status.create_status("pending-task", profile.id, "testuser")
        resp = _client(profile).delete("/api/profile/github/")
        assert resp.status_code == 204
        record = github_status.get_status("pending-task")
        assert record["status"] == "failed"
        assert record["error_category"] == "disconnected"


@pytest.mark.django_db
class TestSyncTask:
    def _connected(self, gh, profile=None, **conn_kwargs):
        profile = profile or _profile()
        import uuid

        conn = CandidateGitHubProfile.objects.create(
            profile=profile,
            github_user_id=12345,
            github_username="testuser",
            sync_token=uuid.uuid4(),
            **conn_kwargs,
        )
        return profile, conn

    def _run(self, profile, conn, token=None):
        task_id = github_status.new_task_id()
        github_status.create_status(task_id, profile.id, conn.github_username)
        try:
            sync_github_profile_task.apply(
                args=[
                    profile.id,
                    task_id,
                    str(token if token is not None else conn.sync_token),
                    conn.github_username,
                ]
            )
        except Ignore:
            pass
        return task_id

    def test_evidence_persisted_from_repo_metadata(self, gh):
        profile, conn = self._connected(gh)
        gh.list_user_repos.return_value = [
            _repo(description="Django REST API backend", topics=["api"]),
            _repo(
                full_name="testuser/fe",
                name="fe",
                description="React frontend",
                topics=["react"],
            ),
            _repo(full_name="testuser/fork", name="fork", fork=True),
            _repo(full_name="testuser/old", name="old", archived=True),
            _repo(full_name="testuser/empty", name="empty", size_kb=0),
        ]
        gh.get_repo_languages.side_effect = lambda fn: {
            "testuser/demo": {"Python": 5000},
            "testuser/fe": {"TypeScript": 3000},
        }.get(fn, {})
        gh.get_readme.return_value = "# Demo\nBuilt with Django and React."

        task_id = self._run(profile, conn)
        record = github_status.get_status(task_id)
        assert record["status"] == "completed"

        conn.refresh_from_db()
        assert conn.language_bytes == {"Python": 5000, "TypeScript": 3000}
        assert conn.last_synced_at is not None

        github_skills = set(
            CandidateSkillEvidence.objects.filter(
                candidate=profile, source="github"
            ).values_list("skill__name", flat=True)
        )
        assert "Django" in github_skills
        assert "React" in github_skills
        # Ineligible repos contributed nothing.
        evidence_rows = CandidateSkillEvidence.objects.filter(
            candidate=profile, source="github"
        )
        for row in evidence_rows:
            assert all(
                not o.startswith(
                    ("repo:testuser/fork", "repo:testuser/old", "repo:testuser/empty")
                )
                for o in row.detail.get("origins", [])
            )

    def test_resync_replaces_only_github_evidence(self, gh):
        profile, conn = self._connected(gh)
        skills = {
            n: Skill.objects.create(name=n, category="t") for n in ("Python", "Vue")
        }
        evidence.link_skill(profile, skills["Python"], source="resume")
        evidence.link_skill(profile, skills["Vue"], source="github")

        gh.list_user_repos.return_value = []
        self._run(profile, conn)

        # Empty repo set -> github evidence cleared; resume/manual intact.
        assert not CandidateSkillEvidence.objects.filter(
            candidate=profile, source="github"
        ).exists()
        assert CandidateSkillEvidence.objects.filter(
            candidate=profile, source="resume", skill=skills["Python"]
        ).exists()
        remaining = set(
            CandidateSkill.objects.filter(candidate=profile).values_list(
                "skill__name", flat=True
            )
        )
        assert remaining == {"Python"}

    def test_stale_token_superseded(self, gh):
        profile, conn = self._connected(gh)
        task_id = self._run(profile, conn, token="wrong-token")
        record = github_status.get_status(task_id)
        assert record["status"] == "failed"
        assert record["error_category"] == "superseded"

    def test_disconnect_during_pending_task(self, gh):
        profile, conn = self._connected(gh)
        task_id = github_status.new_task_id()
        github_status.create_status(task_id, profile.id, conn.github_username)
        conn.active_sync_task_id = task_id
        conn.save(update_fields=["active_sync_task_id"])

        # Disconnect before task runs.
        _client(profile).delete("/api/profile/github/")
        assert not CandidateGitHubProfile.objects.filter(profile=profile).exists()

        try:
            sync_github_profile_task.apply(
                args=[profile.id, task_id, str(conn.sync_token), conn.github_username]
            )
        except Ignore:
            pass
        record = github_status.get_status(task_id)
        assert record["status"] == "failed"
        assert record["error_category"] == "disconnected"
        # No evidence or connection was recreated.
        assert not CandidateSkillEvidence.objects.filter(
            candidate=profile, source="github"
        ).exists()
        assert not CandidateGitHubProfile.objects.filter(profile=profile).exists()

    def test_identity_mismatch_at_sync(self, gh):
        profile, conn = self._connected(gh)
        conn.github_user_id = 999
        conn.save(update_fields=["github_user_id"])
        # get_user returns id=12345 (default mock) != 999
        task_id = self._run(profile, conn)
        record = github_status.get_status(task_id)
        assert record["status"] == "failed"
        assert record["error_category"] == "identity_mismatch"

    def test_rate_limit_fails_after_retries(self, gh):
        from api.github.client import GitHubRateLimitError

        profile, conn = self._connected(gh)
        gh.get_user.side_effect = GitHubRateLimitError(
            "limited", status_code=403, retry_after=1
        )
        task_id = github_status.new_task_id()
        github_status.create_status(task_id, profile.id, conn.github_username)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(sync_github_profile_task, "max_retries", 0)
            sync_github_profile_task.apply(
                args=[profile.id, task_id, str(conn.sync_token), conn.github_username]
            )
        record = github_status.get_status(task_id)
        assert record["status"] == "failed"
        assert record["error_category"] == "rate_limited"

    def test_duplicate_delivery_safe(self, gh):
        profile, conn = self._connected(gh)
        task_id = self._run(profile, conn)
        assert github_status.get_status(task_id)["status"] == "completed"

        # Re-deliver same task: terminal status -> ignored, no corruption.
        try:
            sync_github_profile_task.apply(
                args=[profile.id, task_id, str(conn.sync_token), conn.github_username]
            )
        except Ignore:
            pass
        assert github_status.get_status(task_id)["status"] == "completed"


@pytest.mark.django_db
class TestPartialSyncSafety:
    """Gate 5 audit: incomplete snapshots must not replace last good state."""

    def _seeded_connection(self, gh):
        import uuid
        from datetime import UTC, datetime

        profile = _profile()
        skill = Skill.objects.create(name="Python", category="t")
        evidence.link_skill(
            profile, skill, source="github",
            detail={"origins": ["repo:old/repo"]},
        )
        conn = CandidateGitHubProfile.objects.create(
            profile=profile,
            github_user_id=12345,
            github_username="testuser",
            github_name="Old Name",
            language_bytes={"Python": 999},
            last_synced_at=datetime.now(UTC),
            sync_token=uuid.uuid4(),
        )
        return profile, conn

    def _run(self, profile, conn):
        task_id = github_status.new_task_id()
        github_status.create_status(task_id, profile.id, conn.github_username)
        try:
            sync_github_profile_task.apply(
                args=[profile.id, task_id, str(conn.sync_token),
                      conn.github_username]
            )
        except Ignore:
            pass
        return task_id

    def test_repo_metadata_failure_preserves_snapshot(self, gh):
        from api.github.client import GitHubAPIError

        profile, conn = self._seeded_connection(gh)
        old_synced = conn.last_synced_at
        gh.list_user_repos.return_value = [_repo()]
        gh.get_repo_languages.side_effect = GitHubAPIError(
            "bad", status_code=400
        )

        task_id = self._run(profile, conn)
        record = github_status.get_status(task_id)
        assert record["status"] == "partial"
        assert "repo_metadata" in record["result"]["stage_errors"]

        conn.refresh_from_db()
        assert conn.language_bytes == {"Python": 999}
        assert conn.github_name == "Old Name"
        assert conn.last_synced_at == old_synced
        # Prior github evidence untouched.
        assert CandidateSkillEvidence.objects.filter(
            candidate=profile, source="github", skill__name="Python"
        ).exists()

    def test_readme_failure_preserves_snapshot(self, gh):
        from api.github.client import GitHubAPIError

        profile, conn = self._seeded_connection(gh)
        old_synced = conn.last_synced_at
        gh.list_user_repos.return_value = [_repo()]
        gh.get_repo_languages.return_value = {"Python": 100}
        gh.get_readme.side_effect = GitHubAPIError("bad", status_code=400)

        task_id = self._run(profile, conn)
        record = github_status.get_status(task_id)
        assert record["status"] == "partial"
        assert "readme" in record["result"]["stage_errors"]
        conn.refresh_from_db()
        assert conn.language_bytes == {"Python": 999}
        assert conn.last_synced_at == old_synced

    def test_benign_repo_404_still_completes(self, gh):
        from api.github.client import GitHubUserNotFoundError

        profile, conn = self._seeded_connection(gh)
        gh.list_user_repos.return_value = [_repo()]
        gh.get_repo_languages.side_effect = GitHubUserNotFoundError(
            "gone", status_code=404
        )
        gh.get_readme.side_effect = GitHubUserNotFoundError(
            "gone", status_code=404
        )

        task_id = self._run(profile, conn)
        record = github_status.get_status(task_id)
        assert record["status"] == "completed"
        conn.refresh_from_db()
        assert conn.language_bytes == {}
        assert conn.last_synced_at is not None


class _FakeRedis:
    """Deterministic in-memory stand-in for the redis-py lock client.

    Implements exactly the primitives _ExecutionLock uses: SET NX EX,
    GET, and eval() for the compare-and-renew / compare-and-delete Lua
    scripts (matched by script content, same semantics as real Redis).
    """

    def __init__(self):
        self.store: dict[str, str] = {}
        self.fail = False

    def set(self, key, value, nx=False, ex=None):
        if self.fail:
            raise ConnectionError("redis down")
        if nx and key in self.store:
            return None
        self.store[key] = value
        return True

    def get(self, key):
        if self.fail:
            raise ConnectionError("redis down")
        return self.store.get(key)

    def eval(self, script, numkeys, key, *args):
        if self.fail:
            raise ConnectionError("redis down")
        token = args[0]
        if "pexpire" in script:  # compare-and-renew
            if self.store.get(key) == token:
                return 1
            return 0
        # RELEASE_LOCK_SCRIPT: compare-and-delete
        if self.store.get(key) == token:
            del self.store[key]
            return 1
        return 0


@pytest.fixture(autouse=True)
def lockredis(monkeypatch):
    """Route all execution-lock Redis access to a per-test fake."""
    fake = _FakeRedis()
    monkeypatch.setattr("api.tasks._lock_redis_client", lambda: fake)
    return fake


@pytest.mark.django_db
class TestExecutionLockOwnership:
    """Owned lock + DB fencing prevent stale executions overwriting."""

    def _conn_and_status(self, gh):
        import uuid

        profile = _profile()
        conn = CandidateGitHubProfile.objects.create(
            profile=profile,
            github_user_id=12345,
            github_username="testuser",
            sync_token=uuid.uuid4(),
        )
        task_id = github_status.new_task_id()
        github_status.create_status(task_id, profile.id, conn.github_username)
        return profile, conn, task_id

    def _apply(self, profile, conn, task_id):
        try:
            sync_github_profile_task.apply(
                args=[profile.id, task_id, str(conn.sync_token),
                      conn.github_username]
            )
        except Ignore:
            pass
        return github_status.get_status(task_id)

    def test_lock_held_by_other_execution_skips(self, gh, lockredis):
        profile, conn, task_id = self._conn_and_status(gh)
        lock_key = f"github:lock:{task_id}"
        lockredis.store[lock_key] = "other-owner"

        record = self._apply(profile, conn, task_id)
        assert record["status"] == "queued"  # untouched; we never ran
        assert lockredis.store[lock_key] == "other-owner"

    def test_lock_stolen_mid_fetch_aborts_before_persist(self, gh, lockredis):
        profile, conn, task_id = self._conn_and_status(gh)
        lock_key = f"github:lock:{task_id}"

        def steal_then_return(username):
            # Our lock expired mid-fetch; a newer execution acquired it.
            lockredis.store.pop(lock_key, None)
            lockredis.store[lock_key] = "newer-owner"
            return GitHubUser(id=12345, login="TestUser", public_repos=1)

        gh.get_user.side_effect = steal_then_return
        gh.list_user_repos.return_value = []

        record = self._apply(profile, conn, task_id)
        # Status left at processing: the newer execution owns it now.
        assert record["status"] == "processing"
        conn.refresh_from_db()
        assert conn.last_synced_at is None
        assert conn.language_bytes == {}
        assert not CandidateSkillEvidence.objects.filter(
            candidate=profile, source="github"
        ).exists()
        # Stale execution must not release the newer owner's lock.
        assert lockredis.store[lock_key] == "newer-owner"

    def test_lock_expired_without_successor_aborts(self, gh, lockredis):
        profile, conn, task_id = self._conn_and_status(gh)
        lock_key = f"github:lock:{task_id}"

        def expire_then_return(username):
            lockredis.store.pop(lock_key, None)  # expired; nobody re-acquired
            return GitHubUser(id=12345, login="TestUser", public_repos=1)

        gh.get_user.side_effect = expire_then_return
        gh.list_user_repos.return_value = []

        record = self._apply(profile, conn, task_id)
        assert record["status"] == "processing"
        conn.refresh_from_db()
        assert conn.last_synced_at is None

    def test_redis_failure_during_verify_fails_closed(self, gh, lockredis):
        profile, conn, task_id = self._conn_and_status(gh)
        lock_key = f"github:lock:{task_id}"
        state = {"armed": False}

        def gated_get(key):
            if state["armed"] and key == lock_key:
                raise ConnectionError("redis down")
            return lockredis.store.get(key)

        # Arm failure only for the persist-time ownership read.
        orig_get = lockredis.get
        def maybe_fail(key):
            if state["armed"] and key == lock_key:
                raise ConnectionError("redis down")
            return orig_get(key)
        lockredis.get = maybe_fail

        def arm_then_return(username):
            state["armed"] = True
            return GitHubUser(id=12345, login="TestUser", public_repos=1)

        gh.get_user.side_effect = arm_then_return
        gh.list_user_repos.return_value = []

        record = self._apply(profile, conn, task_id)
        assert record["status"] == "processing"
        conn.refresh_from_db()
        assert conn.last_synced_at is None

    def test_fencing_rejects_stale_execution(self, gh, lockredis):
        """Ownership/fencing change after the cache check, before persist.

        Simulates a newer execution claiming the DB fencing token while our
        execution is still fetching; the persist transaction must reject us.
        """
        from api.github import services as github_services

        profile, conn, task_id = self._conn_and_status(gh)

        def newer_claim_then_return(username):
            github_services.claim_execution_fencing(
                conn.id, str(conn.sync_token)
            )
            return GitHubUser(id=12345, login="TestUser", public_repos=1)

        gh.get_user.side_effect = newer_claim_then_return
        gh.list_user_repos.return_value = []

        record = self._apply(profile, conn, task_id)
        assert record["status"] == "failed"
        assert record["error_category"] == "superseded"
        conn.refresh_from_db()
        assert conn.last_synced_at is None
        assert conn.language_bytes == {}
        assert not CandidateSkillEvidence.objects.filter(
            candidate=profile, source="github"
        ).exists()

    def test_lock_unit_semantics(self, lockredis):
        from api.tasks import _ExecutionLock

        key = "github:lock:unit-test"
        lockredis.store.clear()
        a = _ExecutionLock(key, ttl=900, redis_client=lockredis)
        b = _ExecutionLock(key, ttl=900, redis_client=lockredis)

        assert a.acquire() is True
        assert b.acquire() is False  # held
        assert a.owns() is True
        assert a.renew() is True     # atomic compare-and-renew succeeds

        # Simulate expiry + successor acquisition.
        lockredis.store.pop(key)
        assert b.acquire() is True
        assert a.owns() is False     # lost ownership
        assert a.renew() is False    # stale renewal cannot extend successor
        assert lockredis.store[key] == b.token

        a.release()                  # stale release cannot delete successor
        assert lockredis.store[key] == b.token

        b.release()                  # owner release deletes
        assert key not in lockredis.store


@pytest.mark.django_db
class TestFencingOwnershipContract:
    """DB fencing claim — not Redis acquisition — is the ownership boundary."""

    def test_redis_acquisition_alone_does_not_fence_out_owner(self, gh, lockredis):
        from api.github import services as github_services

        profile = _profile()
        import uuid

        conn = CandidateGitHubProfile.objects.create(
            profile=profile,
            github_user_id=12345,
            github_username="testuser",
            sync_token=uuid.uuid4(),
        )
        task_id = github_status.new_task_id()

        # Execution A claims fencing.
        fencing_a = github_services.claim_execution_fencing(
            conn.id, str(conn.sync_token)
        )

        # A's Redis lock expires; execution B acquires it — but has NOT yet
        # claimed DB fencing. Ownership has NOT transferred.
        lockredis.store[f"github:lock:{task_id}"] = "execution-B"

        # A persists: still the legitimate owner (fencing unchanged).
        github_services.persist_github_sync(
            conn.id,
            str(conn.sync_token),
            12345,
            fields={"github_name": "Snapshot A"},
            evidence_items=None,
            fencing_token=fencing_a,
        )
        conn.refresh_from_db()
        assert conn.github_name == "Snapshot A"
        assert conn.last_synced_at is not None

        # B now formally claims fencing -> ownership transfers.
        fencing_b = github_services.claim_execution_fencing(
            conn.id, str(conn.sync_token)
        )
        assert fencing_b == fencing_a + 1

        # A's stale fencing token is now rejected under the row lock.
        with pytest.raises(github_services.SyncStateError) as exc_info:
            github_services.persist_github_sync(
                conn.id,
                str(conn.sync_token),
                12345,
                fields={"github_name": "Stale A"},
                evidence_items=None,
                fencing_token=fencing_a,
            )
        assert exc_info.value.category == "superseded"
        conn.refresh_from_db()
        assert conn.github_name == "Snapshot A"  # stale write rejected

        # B persists its newer snapshot successfully.
        github_services.persist_github_sync(
            conn.id,
            str(conn.sync_token),
            12345,
            fields={"github_name": "Snapshot B"},
            evidence_items=None,
            fencing_token=fencing_b,
        )
        conn.refresh_from_db()
        assert conn.github_name == "Snapshot B"
