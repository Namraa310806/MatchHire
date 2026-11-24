"""Tests for the resume upload/status/delete API endpoints."""

from typing import cast
from unittest.mock import patch

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from api.models import User
from api.tests.test_resume.pdf_utils import SAMPLE_RESUME, make_pdf

UPLOAD_URL = "/api/resumes/"


def _user(email: str = "up@example.com") -> User:
    return cast(User, User.objects.create_user(email=email, password="Str0ng!Pass"))


def _client(user: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _pdf_upload(text: str = SAMPLE_RESUME, name: str = "resume.pdf") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, make_pdf(text), content_type="application/pdf")


@pytest.mark.django_db
class TestResumeUpload:
    def test_valid_upload_accepted_and_processed_eagerly(self):
        user = _user()
        client = _client(user)
        response = client.post(
            UPLOAD_URL, {"file": _pdf_upload(), "consent": "true"}, format="multipart"
        )
        assert response.status_code == 202
        data = response.json()
        assert data["task_id"]
        assert data["status_url"].endswith(f"{data['task_id']}/")
        # Eager mode: task already ran to completion
        assert data["status"] == "completed"

        profile = user.candidateprofile
        assert profile.resume_file
        assert default_storage.exists(profile.resume_file.name)
        assert profile.resume_consent_given is True
        assert profile.resume_uploaded_at is not None

    def test_missing_consent_rejected(self):
        user = _user()
        client = _client(user)
        response = client.post(UPLOAD_URL, {"file": _pdf_upload()}, format="multipart")
        assert response.status_code == 400
        assert response.json()["error_category"] == "missing_consent"
        assert not user.candidateprofile.resume_file

    def test_consent_false_rejected(self):
        user = _user()
        client = _client(user)
        response = client.post(
            UPLOAD_URL, {"file": _pdf_upload(), "consent": "false"}, format="multipart"
        )
        assert response.status_code == 400

    def test_missing_file(self):
        user = _user()
        client = _client(user)
        response = client.post(UPLOAD_URL, {"consent": "true"}, format="multipart")
        assert response.status_code == 400

    def test_wrong_magic_bytes_rejected(self):
        user = _user()
        client = _client(user)
        bad = SimpleUploadedFile("resume.pdf", b"this is not a pdf", content_type="application/pdf")
        response = client.post(
            UPLOAD_URL, {"file": bad, "consent": "true"}, format="multipart"
        )
        assert response.status_code == 400
        assert response.json()["error_category"] == "invalid_pdf"

    def test_mime_type_not_trusted(self):
        # A real PDF sent with a wrong content type must still be accepted
        user = _user()
        client = _client(user)
        fake = SimpleUploadedFile("resume.pdf", make_pdf(SAMPLE_RESUME), content_type="text/plain")
        response = client.post(
            UPLOAD_URL, {"file": fake, "consent": "true"}, format="multipart"
        )
        assert response.status_code == 202

    def test_oversized_file_rejected(self):
        user = _user()
        client = _client(user)
        big = SimpleUploadedFile(
            "resume.pdf", b"%PDF-" + b"0" * (11 * 1024 * 1024), content_type="application/pdf"
        )
        response = client.post(
            UPLOAD_URL, {"file": big, "consent": "true"}, format="multipart"
        )
        assert response.status_code == 400
        assert response.json()["error_category"] == "file_too_large"

    def test_corrupt_pdf_rejected(self):
        user = _user()
        client = _client(user)
        corrupt = SimpleUploadedFile(
            "resume.pdf", b"%PDF-1.4\n%%EOF garbage", content_type="application/pdf"
        )
        response = client.post(
            UPLOAD_URL, {"file": corrupt, "consent": "true"}, format="multipart"
        )
        assert response.status_code == 400
        assert response.json()["error_category"] in {"corrupt_pdf", "empty_pdf"}

    def test_scanned_pdf_accepted_but_task_fails(self):
        user = _user()
        client = _client(user)
        blank = SimpleUploadedFile("resume.pdf", make_pdf(""), content_type="application/pdf")
        response = client.post(
            UPLOAD_URL, {"file": blank, "consent": "true"}, format="multipart"
        )
        assert response.status_code == 202
        assert response.json()["status"] == "failed"

    def test_resume_replacement(self):
        user = _user()
        client = _client(user)
        client.post(
            UPLOAD_URL, {"file": _pdf_upload(), "consent": "true"}, format="multipart"
        )
        first_name = user.candidateprofile.resume_file.name
        r2 = client.post(
            UPLOAD_URL,
            {"file": _pdf_upload("Different resume text with Python skills"), "consent": "true"},
            format="multipart",
        )
        assert r2.status_code == 202
        profile = user.candidateprofile
        profile.refresh_from_db()
        assert profile.resume_file.name != first_name
        # Old file removed from storage
        assert not default_storage.exists(first_name)

    def test_dispatch_failure_rolls_back(self):
        user = _user()
        client = _client(user)
        with patch("api.resume.views.parse_resume_task.apply_async", side_effect=RuntimeError("broker down")):
            response = client.post(
                UPLOAD_URL, {"file": _pdf_upload(), "consent": "true"}, format="multipart"
            )
        assert response.status_code == 503
        profile = user.candidateprofile
        profile.refresh_from_db()
        assert not profile.resume_file
        assert profile.resume_consent_given is False

    def test_queued_status_when_dispatch_deferred(self):
        user = _user()
        client = _client(user)
        with patch("api.resume.views.parse_resume_task.apply_async") as mock_apply:
            response = client.post(
                UPLOAD_URL, {"file": _pdf_upload(), "consent": "true"}, format="multipart"
            )
        assert response.status_code == 202
        assert response.json()["status"] == "queued"
        # Task was dispatched to parse_queue with matching args
        _, kwargs = mock_apply.call_args
        assert kwargs["queue"] == "parse_queue"
        args = kwargs["args"]
        assert args[0] == user.candidateprofile.id
        assert args[1] == response.json()["task_id"]

    def test_status_endpoint_returns_own_task(self):
        user = _user()
        client = _client(user)
        upload = client.post(
            UPLOAD_URL, {"file": _pdf_upload(), "consent": "true"}, format="multipart"
        )
        task_id = upload.json()["task_id"]
        response = client.get(f"/api/resumes/status/{task_id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "completed"
        # No internal fields leaked
        assert "candidate_id" not in data
        assert "resume_name" not in data

    def test_cannot_access_other_users_task(self):
        user_a = _user("a@example.com")
        user_b = _user("b@example.com")
        client_a = _client(user_a)
        upload = client_a.post(
            UPLOAD_URL, {"file": _pdf_upload(), "consent": "true"}, format="multipart"
        )
        task_id = upload.json()["task_id"]

        client_b = _client(user_b)
        response = client_b.get(f"/api/resumes/status/{task_id}/")
        assert response.status_code == 404

    def test_missing_or_expired_status_404(self):
        user = _user()
        client = _client(user)
        response = client.get("/api/resumes/status/does-not-exist/")
        assert response.status_code == 404

    def test_delete_removes_file_but_keeps_profile_data(self):
        user = _user()
        client = _client(user)
        client.post(
            UPLOAD_URL, {"file": _pdf_upload(), "consent": "true"}, format="multipart"
        )
        profile = user.candidateprofile
        profile.refresh_from_db()
        assert profile.resume_file
        assert profile.candidateskill_set.exists()

        response = client.delete(UPLOAD_URL)
        assert response.status_code == 204
        profile.refresh_from_db()
        assert not profile.resume_file
        assert profile.resume_consent_given is False
        assert profile.resume_uploaded_at is None
        # Extracted profile data is retained per Decision 9
        assert profile.candidateskill_set.exists()
        assert profile.extracted_domain_keywords != []

    def test_delete_without_resume_is_idempotent(self):
        user = _user()
        client = _client(user)
        response = client.delete(UPLOAD_URL)
        assert response.status_code == 204
