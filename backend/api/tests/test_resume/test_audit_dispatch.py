"""Audit tests: cookie refresh-token rotation/reuse and dispatch ordering."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from rest_framework.test import APIClient

from api.models import User
from api.resume import status as resume_status
from api.tests.test_resume.pdf_utils import SAMPLE_RESUME, make_pdf


@pytest.mark.django_db
class TestCookieRefreshRotation:
    def _login(self, client: Client) -> None:
        client.post(
            "/api/auth/register/",
            '{"email": "rot@example.com", "password": "Str0ng!Pass"}',
            content_type="application/json",
        )
        client.post(
            "/api/auth/login/",
            '{"email": "rot@example.com", "password": "Str0ng!Pass"}',
            content_type="application/json",
        )

    def test_cookie_refresh_rotates_and_issues_new_cookies(self):
        client = Client()
        self._login(client)
        old_refresh = client.cookies["mh_refresh"].value
        response = client.post("/api/auth/cookie/refresh/")
        assert response.status_code == 200
        assert client.cookies["mh_refresh"].value != old_refresh
        assert "mh_access" in client.cookies

    def test_reused_cookie_refresh_token_rejected(self):
        client = Client()
        self._login(client)
        old_refresh = client.cookies["mh_refresh"].value
        # First refresh succeeds and rotates
        assert client.post("/api/auth/cookie/refresh/").status_code == 200
        # Replay the OLD refresh token -> must be rejected
        client.cookies.clear()
        client.cookies.load({"mh_refresh": old_refresh})
        response = client.post("/api/auth/cookie/refresh/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestDispatchOrdering:
    def test_status_record_exists_before_task_execution(self):
        """The Redis status record must exist before apply_async is invoked."""
        from unittest.mock import patch

        user = User.objects.create_user(email="ord@example.com", password="x")
        client = APIClient()
        client.force_authenticate(user=user)

        observed = {}

        def spy_apply_async(args=None, task_id=None, **kwargs):
            observed["status_at_dispatch"] = resume_status.get_status(task_id)
            observed["args"] = args
            observed["task_id"] = task_id
            observed["queue"] = kwargs.get("queue")

        with patch("api.resume.views.parse_resume_task.apply_async", side_effect=spy_apply_async):
            response = client.post(
                "/api/resumes/",
                {
                    "file": SimpleUploadedFile(
                        "r.pdf", make_pdf(SAMPLE_RESUME), content_type="application/pdf"
                    ),
                    "consent": "true",
                },
                format="multipart",
            )
        assert response.status_code == 202
        # Status record existed at dispatch time with queued state
        assert observed["status_at_dispatch"] is not None
        assert observed["status_at_dispatch"]["status"] == "queued"
        # Task ID propagation: celery task_id == status task_id == arg
        assert observed["task_id"] == response.json()["task_id"]
        assert observed["args"][1] == observed["task_id"]
        assert observed["queue"] == "parse_queue"

    def test_task_retry_budget_is_bounded(self):
        from api.tasks import parse_resume_task

        assert parse_resume_task.max_retries == 3
