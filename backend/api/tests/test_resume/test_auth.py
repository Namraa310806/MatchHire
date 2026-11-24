"""Tests for authentication endpoints and JWT transports."""

from typing import cast

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

REGISTER_URL = "/api/auth/register/"
LOGIN_URL = "/api/auth/login/"
TOKEN_URL = "/api/auth/token/"
TOKEN_REFRESH_URL = "/api/auth/token/refresh/"
COOKIE_REFRESH_URL = "/api/auth/cookie/refresh/"
LOGOUT_URL = "/api/auth/logout/"


def _register(
    client: APIClient, email: str = "cand@example.com", password: str = "Str0ng!Pass"
) -> dict:
    response = client.post(
        REGISTER_URL,
        {"email": email, "password": password, "first_name": "Test"},
        format="json",
    )
    assert response.status_code == 201, response.content
    return cast(dict, response.json())


@pytest.mark.django_db
class TestRegister:
    def test_register_creates_user_and_profile(self):
        client = APIClient()
        data = _register(client)
        user = User.objects.get(email="cand@example.com")
        assert user.candidateprofile is not None
        assert data["email"] == "cand@example.com"

    def test_register_duplicate_email(self):
        client = APIClient()
        _register(client)
        response = client.post(
            REGISTER_URL,
            {"email": "cand@example.com", "password": "An0ther!Pass"},
            format="json",
        )
        assert response.status_code == 400

    def test_register_weak_password(self):
        client = APIClient()
        response = client.post(
            REGISTER_URL,
            {"email": "weak@example.com", "password": "123"},
            format="json",
        )
        assert response.status_code == 400

    def test_register_missing_fields(self):
        client = APIClient()
        response = client.post(REGISTER_URL, {}, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestCookieLogin:
    def test_login_sets_http_only_cookies_no_tokens_in_body(self):
        client = APIClient()
        _register(client)
        response = client.post(
            LOGIN_URL, {"email": "cand@example.com", "password": "Str0ng!Pass"}, format="json"
        )
        assert response.status_code == 200
        assert "access" not in response.json()
        assert "refresh" not in response.json()
        cookies = response.cookies
        assert "mh_access" in cookies
        assert "mh_refresh" in cookies
        assert cookies["mh_access"]["httponly"]
        assert cookies["mh_refresh"]["httponly"]

    def test_login_wrong_password(self):
        client = APIClient()
        _register(client)
        response = client.post(
            LOGIN_URL, {"email": "cand@example.com", "password": "wrong"}, format="json"
        )
        assert response.status_code == 401

    def test_cookie_authenticates_resume_endpoint(self, settings):
        client = APIClient()
        _register(client)
        client.post(
            LOGIN_URL, {"email": "cand@example.com", "password": "Str0ng!Pass"}, format="json"
        )
        # Cookie auth should allow access to an authenticated endpoint
        response = client.get("/api/resumes/status/nonexistent-task/")
        assert response.status_code == 404  # authenticated, task missing


@pytest.mark.django_db
class TestBearerTokens:
    def test_token_obtain_returns_pair(self):
        client = APIClient()
        _register(client)
        response = client.post(
            TOKEN_URL, {"email": "cand@example.com", "password": "Str0ng!Pass"}, format="json"
        )
        assert response.status_code == 200
        data = response.json()
        assert "access" in data and "refresh" in data

    def test_bearer_token_accesses_resume_endpoint(self):
        client = APIClient()
        _register(client)
        tokens = client.post(
            TOKEN_URL, {"email": "cand@example.com", "password": "Str0ng!Pass"}, format="json"
        ).json()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = client.get("/api/resumes/status/nonexistent-task/")
        assert response.status_code == 404

    def test_token_refresh_rotates(self):
        client = APIClient()
        _register(client)
        tokens = client.post(
            TOKEN_URL, {"email": "cand@example.com", "password": "Str0ng!Pass"}, format="json"
        ).json()
        response = client.post(
            TOKEN_REFRESH_URL, {"refresh": tokens["refresh"]}, format="json"
        )
        assert response.status_code == 200
        new_tokens = response.json()
        assert new_tokens["refresh"] != tokens["refresh"]

    def test_old_refresh_token_blacklisted_after_rotation(self):
        client = APIClient()
        _register(client)
        tokens = client.post(
            TOKEN_URL, {"email": "cand@example.com", "password": "Str0ng!Pass"}, format="json"
        ).json()
        client.post(TOKEN_REFRESH_URL, {"refresh": tokens["refresh"]}, format="json")
        # Reusing the rotated-out refresh token must fail
        response = client.post(
            TOKEN_REFRESH_URL, {"refresh": tokens["refresh"]}, format="json"
        )
        assert response.status_code == 401

    def test_cookie_refresh(self):
        client = APIClient()
        _register(client)
        client.post(
            LOGIN_URL, {"email": "cand@example.com", "password": "Str0ng!Pass"}, format="json"
        )
        response = client.post(COOKIE_REFRESH_URL)
        assert response.status_code == 200
        assert "mh_access" in response.cookies

    def test_logout_blacklists_refresh(self):
        client = APIClient()
        _register(client)
        tokens = client.post(
            TOKEN_URL, {"email": "cand@example.com", "password": "Str0ng!Pass"}, format="json"
        ).json()
        response = client.post(LOGOUT_URL, {"refresh": tokens["refresh"]}, format="json")
        assert response.status_code == 204
        refresh_response = client.post(
            TOKEN_REFRESH_URL, {"refresh": tokens["refresh"]}, format="json"
        )
        assert refresh_response.status_code == 401


@pytest.mark.django_db
class TestUnauthenticated:
    def test_upload_requires_auth(self):
        client = APIClient()
        response = client.post("/api/resumes/", {}, format="multipart")
        assert response.status_code in (401, 403)

    def test_status_requires_auth(self):
        client = APIClient()
        response = client.get("/api/resumes/status/abc/")
        assert response.status_code in (401, 403)

    def test_delete_requires_auth(self):
        client = APIClient()
        response = client.delete("/api/resumes/")
        assert response.status_code in (401, 403)

    def test_health_is_public(self):
        client = APIClient()
        response = client.get("/api/health/")
        # Health endpoint is public; DB/Redis may be unavailable locally
        assert response.status_code in (200, 503)
