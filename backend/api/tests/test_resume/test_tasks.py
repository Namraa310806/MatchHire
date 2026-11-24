"""Tests for the parse_resume_task Celery task lifecycle."""

from typing import cast
from unittest.mock import patch

import pytest
from celery.exceptions import Ignore
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from api.models import CandidateProfile, User
from api.resume import status as resume_status
from api.tasks import parse_resume_task
from api.tests.test_resume.pdf_utils import SAMPLE_RESUME, make_pdf


def _profile(email: str = "task@example.com") -> CandidateProfile:
    user = User.objects.create_user(email=email, password="Str0ng!Pass")
    profile, _ = CandidateProfile.objects.get_or_create(user=user)
    return cast(CandidateProfile, profile)


def _store_resume(profile: CandidateProfile, text: str = SAMPLE_RESUME) -> str:
    name = f"resumes/{profile.id}/test-{id(text)}.pdf"
    default_storage.save(name, ContentFile(make_pdf(text)))
    profile.resume_file = name
    profile.resume_consent_given = True
    profile.save(update_fields=["resume_file", "resume_consent_given"])
    return name


def _run(profile_id: int, task_id: str, resume_name: str):
    return parse_resume_task.apply(args=[profile_id, task_id, resume_name])


@pytest.mark.django_db
class TestParseResumeTask:
    def test_completed_task_persists_profile(self):
        profile = _profile()
        name = _store_resume(profile)
        task_id = resume_status.new_task_id()
        resume_status.create_status(task_id, profile.id, name)

        result = _run(profile.id, task_id, name)
        assert result.get() == "completed" or result.result["status"] == "completed"

        record = resume_status.get_status(task_id)
        assert record["status"] == "completed"
        assert record["result"]["skills_found"] > 0
        assert record["result"]["sections_found"]

        profile.refresh_from_db()
        assert profile.candidateskill_set.count() > 0
        assert profile.extracted_domain_keywords != []

    def test_scanned_pdf_fails_with_no_text_layer(self):
        profile = _profile()
        name = _store_resume(profile, text="")
        task_id = resume_status.new_task_id()
        resume_status.create_status(task_id, profile.id, name)

        _run(profile.id, task_id, name)
        record = resume_status.get_status(task_id)
        assert record["status"] == "failed"
        assert record["error_category"] == "no_text_layer"
        assert "scanned" in record["error_message"].lower() or "text layer" in record[
            "error_message"
        ].lower()

    def test_missing_status_record_ignored(self):
        profile = _profile()
        name = _store_resume(profile)
        try:
            _run(profile.id, "nonexistent-task-id", name)
        except Ignore:
            pass
        # No status record created, no profile mutation
        assert resume_status.get_status("nonexistent-task-id") is None
        profile.refresh_from_db()
        assert profile.candidateskill_set.count() == 0

    def test_terminal_status_not_reprocessed(self):
        profile = _profile()
        name = _store_resume(profile)
        task_id = resume_status.new_task_id()
        resume_status.create_status(task_id, profile.id, name)
        resume_status.update_status(task_id, status=resume_status.STATUS_COMPLETED)

        try:
            _run(profile.id, task_id, name)
        except Ignore:
            pass
        assert resume_status.get_status(task_id)["status"] == "completed"

    def test_duplicate_delivery_does_not_corrupt(self):
        profile = _profile()
        name = _store_resume(profile)
        task_id = resume_status.new_task_id()
        resume_status.create_status(task_id, profile.id, name)

        _run(profile.id, task_id, name)
        first_skills = profile.candidateskill_set.count()

        # Simulate duplicate delivery after completion
        try:
            _run(profile.id, task_id, name)
        except Ignore:
            pass
        profile.refresh_from_db()
        assert profile.candidateskill_set.count() == first_skills

    def test_old_task_cannot_overwrite_newer_resume(self):
        profile = _profile()
        name_a = _store_resume(profile, "Resume A with Python and Django")
        name_b = f"resumes/{profile.id}/newer.pdf"
        default_storage.save(name_b, ContentFile(make_pdf("Resume B content")))
        profile.resume_file = name_b
        profile.save(update_fields=["resume_file"])

        task_id = resume_status.new_task_id()
        resume_status.create_status(task_id, profile.id, name_a)

        _run(profile.id, task_id, name_a)
        record = resume_status.get_status(task_id)
        assert record["status"] == "failed"
        assert record["error_category"] == "resume_replaced"

    def test_missing_consent_fails(self):
        profile = _profile()
        name = _store_resume(profile)
        profile.resume_consent_given = False
        profile.save(update_fields=["resume_consent_given"])

        task_id = resume_status.new_task_id()
        resume_status.create_status(task_id, profile.id, name)
        _run(profile.id, task_id, name)
        record = resume_status.get_status(task_id)
        assert record["status"] == "failed"
        assert record["error_category"] == "missing_consent"

    def test_deleted_resume_fails(self):
        profile = _profile()
        name = _store_resume(profile)
        default_storage.delete(name)
        profile.resume_file = ""
        profile.save(update_fields=["resume_file"])

        task_id = resume_status.new_task_id()
        resume_status.create_status(task_id, profile.id, name)
        _run(profile.id, task_id, name)
        record = resume_status.get_status(task_id)
        assert record["status"] == "failed"
        assert record["error_category"] == "resume_deleted"

    def test_missing_file_in_storage_retries_then_fails(self):
        profile = _profile()
        name = f"resumes/{profile.id}/ghost.pdf"
        profile.resume_file = name
        profile.resume_consent_given = True
        profile.save(update_fields=["resume_file", "resume_consent_given"])
        # File was never written to storage

        task_id = resume_status.new_task_id()
        resume_status.create_status(task_id, profile.id, name)
        with patch.object(parse_resume_task, "max_retries", 0):
            _run(profile.id, task_id, name)
        record = resume_status.get_status(task_id)
        assert record["status"] == "failed"
        assert record["error_category"] == "file_unavailable"

    def test_experience_estimate_persisted_when_unset(self):
        profile = _profile()
        name = _store_resume(profile)
        task_id = resume_status.new_task_id()
        resume_status.create_status(task_id, profile.id, name)
        _run(profile.id, task_id, name)

        profile.refresh_from_db()
        # SAMPLE_RESUME contains "2 years of experience" -> high confidence 2.0
        assert profile.total_experience_years is not None
        assert float(profile.total_experience_years) == 2.0

    def test_experience_not_overwritten_when_set(self):
        profile = _profile()
        from decimal import Decimal

        profile.total_experience_years = Decimal("7.5")
        profile.save(update_fields=["total_experience_years"])
        name = _store_resume(profile)
        task_id = resume_status.new_task_id()
        resume_status.create_status(task_id, profile.id, name)
        _run(profile.id, task_id, name)

        profile.refresh_from_db()
        assert float(profile.total_experience_years) == 7.5

    def test_no_duplicate_candidate_skills(self):
        profile = _profile()
        name = _store_resume(profile)
        task_id = resume_status.new_task_id()
        resume_status.create_status(task_id, profile.id, name)
        _run(profile.id, task_id, name)
        count_after_first = profile.candidateskill_set.count()

        # Re-run same task id is ignored; simulate fresh task on same resume
        task_id2 = resume_status.new_task_id()
        resume_status.create_status(task_id2, profile.id, name)
        _run(profile.id, task_id2, name)
        profile.refresh_from_db()
        assert profile.candidateskill_set.count() == count_after_first
