"""CSRF enforcement tests for cookie-authenticated requests (Decision 8).

These use Django's test Client with ``enforce_csrf_checks=True`` because
DRF's APIClient disables CSRF checks by default — which would hide exactly
the vulnerability being audited.
"""

import pytest
from django.test import Client


@pytest.fixture
def csrf_client(db):
    return Client(enforce_csrf_checks=True)


def _register_and_login(client: Client) -> None:
    client.post(
        "/api/auth/register/",
        '{"email": "csrf@example.com", "password": "Str0ng!Pass"}',
        content_type="application/json",
    )
    client.post(
        "/api/auth/login/",
        '{"email": "csrf@example.com", "password": "Str0ng!Pass"}',
        content_type="application/json",
    )


def _csrf_token(client: Client) -> str:
    return str(client.cookies["csrftoken"].value)


@pytest.mark.django_db
class TestCookieCSRF:
    def test_login_issues_csrf_cookie(self, csrf_client):
        _register_and_login(csrf_client)
        assert "csrftoken" in csrf_client.cookies
        assert "mh_access" in csrf_client.cookies
        assert "mh_refresh" in csrf_client.cookies

    def test_cookie_post_without_csrf_rejected(self, csrf_client):
        _register_and_login(csrf_client)
        # DELETE is a state-changing method; no CSRF token sent
        response = csrf_client.delete("/api/resumes/")
        assert response.status_code == 403

    def test_cookie_post_with_invalid_csrf_rejected(self, csrf_client):
        _register_and_login(csrf_client)
        response = csrf_client.delete(
            "/api/resumes/", HTTP_X_CSRFTOKEN="invalid-token-value"
        )
        assert response.status_code == 403

    def test_cookie_post_with_valid_csrf_accepted(self, csrf_client):
        _register_and_login(csrf_client)
        token = _csrf_token(csrf_client)
        response = csrf_client.delete(
            "/api/resumes/", HTTP_X_CSRFTOKEN=token
        )
        assert response.status_code == 204

    def test_cookie_get_does_not_require_csrf(self, csrf_client):
        _register_and_login(csrf_client)
        response = csrf_client.get("/api/resumes/status/some-task-id/")
        assert response.status_code == 404  # authenticated, task missing

    def test_bearer_post_exempt_from_csrf(self, csrf_client):
        """Non-browser Bearer clients are CSRF-exempt per Decision 8."""
        _register_and_login(csrf_client)
        # Obtain a bearer token via the non-browser endpoint
        token_resp = csrf_client.post(
            "/api/auth/token/",
            '{"email": "csrf@example.com", "password": "Str0ng!Pass"}',
            content_type="application/json",
        )
        access = token_resp.json()["access"]
        # New client: no cookies at all, only Bearer header
        bearer_client = Client(enforce_csrf_checks=True)
        response = bearer_client.delete(
            "/api/resumes/", HTTP_AUTHORIZATION=f"Bearer {access}"
        )
        assert response.status_code == 204
