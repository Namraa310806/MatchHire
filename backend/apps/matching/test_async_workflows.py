from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TestCase
from django.utils import timezone

from apps.applications.models import Application, ApplicationStatusHistory
from apps.analytics.services import AnalyticsRefreshService
from apps.analytics.tasks import refresh_recruiter_analytics
from apps.interviews.models import Interview, InterviewStatusHistory
from apps.jobs.models import Job
from apps.matching.models import JobMatch
from apps.matching.services.matching import MatchingService
from apps.matching.tasks import recalculate_candidate_matches, recalculate_job_matches
from apps.notifications.models import Notification
from apps.notifications.tasks import (
    notify_application_status_changed,
    notify_application_submitted,
    notify_interview_cancelled,
    notify_interview_completed,
    notify_interview_scheduled,
    notify_match_created,
)
from apps.resumes.models import Resume, ResumeVersion, StructuredResume, ResumeSkill

User = get_user_model()


class AsyncWorkflowTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="pass12345",
            full_name="Recruiter",
            role=User.Roles.RECRUITER,
        )
        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            password="pass12345",
            full_name="Candidate",
            role=User.Roles.CANDIDATE,
        )
        self.resume = Resume.objects.create(user=self.candidate)
        self.version = ResumeVersion.objects.create(
            resume=self.resume,
            original_filename="resume.pdf",
            stored_filename="async-resume.pdf",
            file_size=100,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        self.structured_resume = StructuredResume.objects.create(resume_version=self.version)
        ResumeSkill.objects.create(structured_resume=self.structured_resume, name="Python")
        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Backend Engineer",
            company_name="MatchHire",
            location="Remote",
            description="Build APIs",
            requirements="Python",
            status=Job.JobStatus.ACTIVE,
        )

    def create_application(self):
        return Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            resume_version=self.version,
        )

    def create_interview(self):
        application = self.create_application()
        return Interview.objects.create(
            application=application,
            scheduled_at=timezone.now() + timedelta(days=1),
            duration_minutes=30,
            interview_type=Interview.InterviewType.VIDEO,
            meeting_link="https://example.com/meet",
            created_by=self.recruiter,
        )

    def test_resume_update_enqueues_recalculation(self):
        with patch("apps.matching.tasks.recalculate_candidate_profile.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                with transaction.atomic():
                    self.version.change_reason = "updated"
                    self.version.save(update_fields=["change_reason"])
            delay.assert_called_with(str(self.candidate.id))

    def test_structured_resume_update_enqueues_recalculation(self):
        with patch("apps.matching.tasks.recalculate_candidate_profile.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                with transaction.atomic():
                    self.structured_resume.summary = "updated"
                    self.structured_resume.save(update_fields=["summary"])
            delay.assert_called_with(str(self.candidate.id))

    def test_job_creation_enqueues_matching(self):
        with patch("apps.matching.tasks.recalculate_job_matches.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                with transaction.atomic():
                    Job.objects.create(
                        recruiter=self.recruiter,
                        title="New Active",
                        company_name="MatchHire",
                        location="Remote",
                        description="Build",
                        requirements="Python",
                        status=Job.JobStatus.ACTIVE,
                    )
            self.assertTrue(delay.called)

    def test_job_update_enqueues_recalculation(self):
        with patch("apps.matching.tasks.recalculate_job_matches.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                with transaction.atomic():
                    self.job.requirements = "Python,Django"
                    self.job.save(update_fields=["requirements"])
            delay.assert_called_with(str(self.job.id))

    def test_job_closed_refreshes_analytics(self):
        with patch("apps.analytics.tasks.refresh_recruiter_analytics.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                with transaction.atomic():
                    self.job.status = Job.JobStatus.CLOSED
                    self.job.save(update_fields=["status"])
            delay.assert_called_with(str(self.recruiter.id))

    def test_match_notification_task(self):
        match = MatchingService.calculate_match(self.candidate, self.job)
        notify_match_created(str(match.id))
        self.assertEqual(Notification.objects.filter(notification_type=Notification.NotificationType.MATCH_CREATED).count(), 1)

    def test_application_submitted_notification_task(self):
        application = self.create_application()
        notify_application_submitted(str(application.id))
        self.assertEqual(Notification.objects.filter(notification_type=Notification.NotificationType.APPLICATION_SUBMITTED).count(), 1)

    def test_status_changed_notification_task(self):
        application = self.create_application()
        history = ApplicationStatusHistory.objects.create(
            application=application,
            old_status="submitted",
            new_status="under_review",
            changed_by=self.recruiter,
        )
        notify_application_status_changed(str(history.id))
        self.assertEqual(Notification.objects.filter(notification_type=Notification.NotificationType.APPLICATION_STATUS_CHANGED).count(), 1)

    def test_interview_scheduled_notification_task(self):
        interview = self.create_interview()
        notify_interview_scheduled(str(interview.id))
        self.assertEqual(Notification.objects.filter(notification_type=Notification.NotificationType.INTERVIEW_SCHEDULED).count(), 1)

    def test_interview_completed_notification_task(self):
        interview = self.create_interview()
        history = InterviewStatusHistory.objects.create(
            interview=interview,
            old_status="scheduled",
            new_status="completed",
            changed_by=self.recruiter,
        )
        notify_interview_completed(str(history.id))
        self.assertEqual(Notification.objects.filter(notification_type=Notification.NotificationType.INTERVIEW_COMPLETED).count(), 1)

    def test_interview_cancelled_notification_task(self):
        interview = self.create_interview()
        history = InterviewStatusHistory.objects.create(
            interview=interview,
            old_status="scheduled",
            new_status="cancelled",
            changed_by=self.recruiter,
        )
        notify_interview_cancelled(str(history.id))
        self.assertEqual(Notification.objects.filter(notification_type=Notification.NotificationType.INTERVIEW_CANCELLED).count(), 1)

    def test_transaction_on_commit_used_for_resume_signal(self):
        with patch("django.db.transaction.on_commit") as on_commit:
            self.version.save(update_fields=["change_reason"])
            self.assertTrue(on_commit.called)

    def test_retry_configuration_exists(self):
        self.assertEqual(recalculate_job_matches.retry_kwargs["max_retries"], 3)
        self.assertTrue(recalculate_job_matches.retry_backoff)

    def test_notification_task_idempotent(self):
        application = self.create_application()
        notify_application_submitted(str(application.id))
        notify_application_submitted(str(application.id))
        self.assertEqual(Notification.objects.filter(notification_type=Notification.NotificationType.APPLICATION_SUBMITTED).count(), 1)

    def test_matching_task_idempotent(self):
        recalculate_job_matches(str(self.job.id))
        recalculate_job_matches(str(self.job.id))
        self.assertEqual(JobMatch.objects.filter(candidate=self.candidate, job=self.job).count(), 1)

    def test_multiple_rapid_updates_safe(self):
        recalculate_candidate_matches(str(self.candidate.id))
        recalculate_candidate_matches(str(self.candidate.id))
        recalculate_candidate_matches(str(self.candidate.id))
        self.assertEqual(JobMatch.objects.filter(candidate=self.candidate, job=self.job).count(), 1)

    def test_concurrent_execution_safe(self):
        MatchingService.calculate_match(self.candidate, self.job)
        MatchingService.calculate_match(self.candidate, self.job)
        self.assertEqual(JobMatch.objects.count(), 1)

    def test_bulk_matching_creates_matches(self):
        self.assertEqual(recalculate_job_matches(str(self.job.id)), 1)
        self.assertEqual(JobMatch.objects.count(), 1)

    def test_bulk_matching_updates_matches(self):
        recalculate_job_matches(str(self.job.id))
        self.job.requirements = "Python,Django"
        self.job.save(update_fields=["requirements"])
        recalculate_job_matches(str(self.job.id))
        self.assertEqual(JobMatch.objects.count(), 1)

    def test_existing_match_updated_instead_of_duplicated(self):
        match = MatchingService.calculate_match(self.candidate, self.job)
        self.job.requirements = "Python,Django"
        self.job.save(update_fields=["requirements"])
        updated = MatchingService.calculate_match(self.candidate, self.job)
        self.assertEqual(match.id, updated.id)

    def test_analytics_refresh_triggered_by_application(self):
        with patch("apps.analytics.tasks.refresh_recruiter_analytics.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                with transaction.atomic():
                    self.create_application()
            delay.assert_called_with(str(self.recruiter.id))

    def test_dashboard_values_remain_correct(self):
        self.create_application()
        data = AnalyticsRefreshService.refresh_recruiter_dashboard(str(self.recruiter.id))
        self.assertEqual(data["total_applications"], 1)

    def test_signals_enqueue_celery_tasks(self):
        with patch("apps.notifications.tasks.notify_application_submitted.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                with transaction.atomic():
                    self.create_application()
            self.assertTrue(delay.called)

    def test_signals_contain_no_matching_business_logic(self):
        with patch("apps.matching.services.matching.MatchingService.recalculate_for_job") as service:
            with self.captureOnCommitCallbacks(execute=True):
                with transaction.atomic():
                    self.job.save(update_fields=["updated_at"])
            service.assert_not_called()

    def test_tasks_call_service_layer(self):
        with patch("apps.matching.tasks.MatchingService.recalculate_for_job", return_value=0) as service:
            recalculate_job_matches(str(self.job.id))
            service.assert_called_once_with(str(self.job.id))

    def test_matching_service_invoked(self):
        with patch("apps.matching.services.matching.MatchingService.calculate_match", wraps=MatchingService.calculate_match) as service:
            recalculate_job_matches(str(self.job.id))
            self.assertTrue(service.called)

    def test_notification_service_invoked(self):
        application = self.create_application()
        with patch("apps.notifications.tasks.NotificationService.notify_application_submitted") as service:
            notify_application_submitted(str(application.id))
            self.assertTrue(service.called)

    def test_query_optimization_uses_iterator(self):
        with patch("apps.matching.services.matching.StructuredResume.objects") as manager:
            manager.filter.return_value.select_related.return_value.only.return_value.iterator.return_value = []
            MatchingService.recalculate_for_job(str(self.job.id))
            self.assertTrue(manager.filter.return_value.select_related.return_value.only.return_value.iterator.called)

    def test_bulk_processing_returns_processed_count(self):
        self.assertEqual(MatchingService.recalculate_for_job(str(self.job.id)), 1)

    def test_full_async_workflow_end_to_end(self):
        recalculate_job_matches(str(self.job.id))
        match = JobMatch.objects.get(candidate=self.candidate, job=self.job)
        notify_match_created(str(match.id))
        application = self.create_application()
        notify_application_submitted(str(application.id))
        self.assertEqual(JobMatch.objects.count(), 1)
        self.assertEqual(Notification.objects.count(), 2)
