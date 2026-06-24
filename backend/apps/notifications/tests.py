from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.notifications.models import Notification
from apps.notifications.services.notification_service import NotificationService
from apps.jobs.models import Job
from apps.applications.models import Application
from apps.interviews.models import Interview
from apps.matching.models import JobMatch
from apps.resumes.models import Resume, ResumeVersion, StructuredResume

User = get_user_model()


class NotificationModelTests(TestCase):
    """Test Notification model functionality."""

    def test_1_notification_created(self):
        """Test that a notification can be created."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        notification = Notification.objects.create(
            recipient=user,
            title="Test Notification",
            message="This is a test message",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
            metadata={"test": "data"},
        )
        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.recipient, user)
        self.assertEqual(notification.title, "Test Notification")
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.metadata, {"test": "data"})

    def test_18_metadata_stored_correctly(self):
        """Test that metadata is stored correctly as JSON."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        metadata = {
            "application_id": "123",
            "job_id": "456",
            "candidate_id": "789",
        }
        notification = Notification.objects.create(
            recipient=user,
            title="Test",
            message="Test",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
            metadata=metadata,
        )
        self.assertEqual(notification.metadata, metadata)

    def test_29_read_state_persists(self):
        """Test that read state persists after save."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        notification = Notification.objects.create(
            recipient=user,
            title="Test",
            message="Test",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        self.assertFalse(notification.is_read)
        notification.is_read = True
        notification.save()
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_30_notification_ordering_verified(self):
        """Test that notifications are ordered newest first by default."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        # Create notifications with explicit timestamps to ensure ordering
        import time
        notification1 = Notification.objects.create(
            recipient=user,
            title="First",
            message="First",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        time.sleep(0.01)  # Small delay to ensure different timestamps
        notification2 = Notification.objects.create(
            recipient=user,
            title="Second",
            message="Second",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        notifications = list(Notification.objects.filter(recipient=user))
        self.assertEqual(notifications[0].id, notification2.id)
        self.assertEqual(notifications[1].id, notification1.id)


class NotificationServiceTests(TestCase):
    """Test NotificationService functionality."""

    def test_19_notification_service_create_notification(self):
        """Test NotificationService.create_notification."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        notification = NotificationService.create_notification(
            recipient=user,
            title="Test",
            message="Test message",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
            metadata={"key": "value"},
        )
        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.recipient, user)
        self.assertEqual(notification.title, "Test")

    def test_20_notification_service_mark_as_read(self):
        """Test NotificationService.mark_as_read."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        notification = Notification.objects.create(
            recipient=user,
            title="Test",
            message="Test",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        updated = NotificationService.mark_as_read(str(notification.id), user)
        self.assertTrue(updated.is_read)

    def test_21_notification_service_mark_all_as_read(self):
        """Test NotificationService.mark_all_as_read."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        Notification.objects.create(
            recipient=user,
            title="Test 1",
            message="Test 1",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        Notification.objects.create(
            recipient=user,
            title="Test 2",
            message="Test 2",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        count = NotificationService.mark_all_as_read(user)
        self.assertEqual(count, 2)
        self.assertEqual(
            Notification.objects.filter(recipient=user, is_read=False).count(), 0
        )


class NotificationFactoryTests(TestCase):
    """Test notification factory methods."""

    def test_2_recruiter_notified_on_application_submission(self):
        """Test that recruiter is notified when application is submitted."""
        recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="testpass123",
            role=User.Roles.RECRUITER,
        )
        notification = NotificationService.notify_application_submitted(
            recruiter=recruiter,
            application_id="app-123",
            job_id="job-456",
            candidate_id="cand-789",
        )
        self.assertEqual(notification.recipient, recruiter)
        self.assertEqual(
            notification.notification_type,
            Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        self.assertEqual(
            notification.metadata,
            {"application_id": "app-123", "job_id": "job-456", "candidate_id": "cand-789"},
        )

    def test_3_candidate_notified_on_application_status_change(self):
        """Test that candidate is notified when application status changes."""
        candidate = User.objects.create_user(
            email="candidate@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        notification = NotificationService.notify_application_status_changed(
            candidate=candidate,
            application_id="app-123",
            old_status="SUBMITTED",
            new_status="UNDER_REVIEW",
        )
        self.assertEqual(notification.recipient, candidate)
        self.assertEqual(
            notification.notification_type,
            Notification.NotificationType.APPLICATION_STATUS_CHANGED,
        )
        self.assertEqual(
            notification.metadata,
            {"application_id": "app-123", "old_status": "SUBMITTED", "new_status": "UNDER_REVIEW"},
        )

    def test_4_candidate_notified_on_interview_scheduled(self):
        """Test that candidate is notified when interview is scheduled."""
        candidate = User.objects.create_user(
            email="candidate@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        notification = NotificationService.notify_interview_scheduled(
            candidate=candidate,
            interview_id="int-123",
            application_id="app-456",
        )
        self.assertEqual(notification.recipient, candidate)
        self.assertEqual(
            notification.notification_type,
            Notification.NotificationType.INTERVIEW_SCHEDULED,
        )
        self.assertEqual(
            notification.metadata, {"interview_id": "int-123", "application_id": "app-456"}
        )

    def test_5_candidate_notified_on_interview_completed(self):
        """Test that candidate is notified when interview is completed."""
        candidate = User.objects.create_user(
            email="candidate@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        notification = NotificationService.notify_interview_completed(
            candidate=candidate,
            interview_id="int-123",
            application_id="app-456",
        )
        self.assertEqual(notification.recipient, candidate)
        self.assertEqual(
            notification.notification_type,
            Notification.NotificationType.INTERVIEW_COMPLETED,
        )

    def test_6_candidate_notified_on_interview_cancelled(self):
        """Test that candidate is notified when interview is cancelled."""
        candidate = User.objects.create_user(
            email="candidate@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        notification = NotificationService.notify_interview_cancelled(
            candidate=candidate,
            interview_id="int-123",
            application_id="app-456",
        )
        self.assertEqual(notification.recipient, candidate)
        self.assertEqual(
            notification.notification_type,
            Notification.NotificationType.INTERVIEW_CANCELLED,
        )

    def test_7_candidate_notified_on_match_creation(self):
        """Test that candidate is notified when match is created."""
        candidate = User.objects.create_user(
            email="candidate@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        notification = NotificationService.notify_match_created(
            candidate=candidate, job_id="job-123", match_score=82.5
        )
        self.assertEqual(notification.recipient, candidate)
        self.assertEqual(
            notification.notification_type, Notification.NotificationType.MATCH_CREATED
        )
        self.assertEqual(notification.metadata, {"job_id": "job-123", "match_score": 82.5})


class NotificationAPITests(TestCase):
    """Test notification API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="testpass123",
            role=User.Roles.RECRUITER,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.candidate)

    def test_8_user_lists_notifications(self):
        """Test that user can list their notifications."""
        Notification.objects.create(
            recipient=self.candidate,
            title="Test 1",
            message="Test 1",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        Notification.objects.create(
            recipient=self.candidate,
            title="Test 2",
            message="Test 2",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_9_notifications_ordered_newest_first(self):
        """Test that notifications are ordered newest first."""
        import time
        notification1 = Notification.objects.create(
            recipient=self.candidate,
            title="First",
            message="First",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        time.sleep(0.01)  # Small delay to ensure different timestamps
        notification2 = Notification.objects.create(
            recipient=self.candidate,
            title="Second",
            message="Second",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["id"], str(notification2.id))
        self.assertEqual(response.data["results"][1]["id"], str(notification1.id))

    def test_10_pagination_works(self):
        """Test that pagination works correctly."""
        # Create 25 notifications
        for i in range(25):
            Notification.objects.create(
                recipient=self.candidate,
                title=f"Test {i}",
                message=f"Test {i}",
                notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
            )
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 20)  # Default page size
        self.assertIn("next", response.data)

    def test_11_mark_read_works(self):
        """Test that marking a notification as read works."""
        notification = Notification.objects.create(
            recipient=self.candidate,
            title="Test",
            message="Test",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        response = self.client.patch(f"/api/notifications/{notification.id}/read/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_read"])
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_12_mark_all_read_works(self):
        """Test that marking all notifications as read works."""
        Notification.objects.create(
            recipient=self.candidate,
            title="Test 1",
            message="Test 1",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        Notification.objects.create(
            recipient=self.candidate,
            title="Test 2",
            message="Test 2",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        response = self.client.post("/api/notifications/read-all/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["updated_count"], 2)
        self.assertEqual(
            Notification.objects.filter(recipient=self.candidate, is_read=False).count(),
            0,
        )

    def test_13_ownership_enforced(self):
        """Test that users cannot access other users' notifications."""
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        notification = Notification.objects.create(
            recipient=other_user,
            title="Test",
            message="Test",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        response = self.client.patch(f"/api/notifications/{notification.id}/read/")
        self.assertEqual(response.status_code, 404)

    def test_14_anonymous_blocked(self):
        """Test that anonymous users are blocked."""
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, 401)

    def test_15_unread_count_endpoint_works(self):
        """Test that unread count endpoint works."""
        Notification.objects.create(
            recipient=self.candidate,
            title="Test 1",
            message="Test 1",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        Notification.objects.create(
            recipient=self.candidate,
            title="Test 2",
            message="Test 2",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
            is_read=True,
        )
        response = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["unread_count"], 1)

    def test_16_unread_count_updates_after_mark_read(self):
        """Test that unread count updates after marking as read."""
        notification = Notification.objects.create(
            recipient=self.candidate,
            title="Test",
            message="Test",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        response = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(response.data["unread_count"], 1)
        self.client.patch(f"/api/notifications/{notification.id}/read/")
        response = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(response.data["unread_count"], 0)

    def test_17_unread_count_updates_after_mark_all_read(self):
        """Test that unread count updates after marking all as read."""
        Notification.objects.create(
            recipient=self.candidate,
            title="Test 1",
            message="Test 1",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        Notification.objects.create(
            recipient=self.candidate,
            title="Test 2",
            message="Test 2",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        response = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(response.data["unread_count"], 2)
        self.client.post("/api/notifications/read-all/")
        response = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(response.data["unread_count"], 0)

    def test_28_query_optimization_verified(self):
        """Test that notification list endpoint uses query optimization."""
        # Create 5 notifications
        for i in range(5):
            Notification.objects.create(
                recipient=self.candidate,
                title=f"Test {i}",
                message=f"Test {i}",
                notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
            )
        # Test with assertNumQueries to ensure select_related is used
        with self.assertNumQueries(2):  # 1 for count, 1 for data
            self.client.get("/api/notifications/")


class WorkflowIntegrationTests(TestCase):
    """Test notification integration with workflows."""

    def setUp(self):
        """Set up test data."""
        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="testpass123",
            role=User.Roles.RECRUITER,
        )
        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Software Engineer",
            company_name="Tech Corp",
            location="San Francisco",
            description="Job description",
            requirements="Python,Django",
            status=Job.JobStatus.ACTIVE,
        )

    def test_22_application_submit_triggers_notification(self):
        """Test that application submission triggers notification."""
        # Create resume for candidate
        resume = Resume.objects.create(user=self.candidate)
        file_content = SimpleUploadedFile(
            "resume.pdf", b"test content", content_type="application/pdf"
        )
        resume_version = ResumeVersion.objects.create(
            resume=resume,
            original_filename="resume.pdf",
            stored_filename="unique_resume.pdf",
            file=file_content,
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        # Submit application via API
        client = APIClient()
        client.force_authenticate(user=self.candidate)
        response = client.post(
            f"/api/jobs/{self.job.id}/apply/",
            {"resume_version_id": str(resume_version.id)},
        )
        self.assertEqual(response.status_code, 201)
        application_id = response.data["id"]
        # Check that recruiter was notified
        notifications = Notification.objects.filter(
            recipient=self.recruiter,
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
        )
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(
            notifications.first().metadata["application_id"], application_id
        )

    def test_23_status_change_triggers_notification(self):
        """Test that application status change triggers notification."""
        resume = Resume.objects.create(user=self.candidate)
        file_content = SimpleUploadedFile(
            "resume.pdf", b"test content", content_type="application/pdf"
        )
        resume_version = ResumeVersion.objects.create(
            resume=resume,
            original_filename="resume.pdf",
            stored_filename="unique_resume.pdf",
            file=file_content,
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        application = Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            resume_version=resume_version,
        )
        # Clear any notifications from creation
        Notification.objects.all().delete()
        # Change status
        from apps.applications.services.workflow import ApplicationWorkflowService

        ApplicationWorkflowService.change_status(
            application, Application.ApplicationStatus.UNDER_REVIEW, self.recruiter
        )
        # Check that candidate was notified
        notifications = Notification.objects.filter(
            recipient=self.candidate,
            notification_type=Notification.NotificationType.APPLICATION_STATUS_CHANGED,
        )
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(
            notifications.first().metadata["new_status"], "under_review"
        )

    def test_24_interview_schedule_triggers_notification(self):
        """Test that interview scheduling triggers notification."""
        resume = Resume.objects.create(user=self.candidate)
        file_content = SimpleUploadedFile(
            "resume.pdf", b"test content", content_type="application/pdf"
        )
        resume_version = ResumeVersion.objects.create(
            resume=resume,
            original_filename="resume.pdf",
            stored_filename="unique_resume.pdf",
            file=file_content,
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        application = Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            resume_version=resume_version,
            status=Application.ApplicationStatus.UNDER_REVIEW,
        )
        Notification.objects.all().delete()
        # Schedule interview via API
        client = APIClient()
        client.force_authenticate(user=self.recruiter)
        response = client.post(
            f"/api/applications/{application.id}/interviews/",
            {
                "scheduled_at": (timezone.now() + timedelta(days=7)).isoformat(),
                "duration_minutes": 60,
                "interview_type": Interview.InterviewType.VIDEO,
                "meeting_link": "https://example.com/meet",
            },
        )
        self.assertEqual(response.status_code, 201)
        interview_id = response.data["id"]
        # Check that candidate was notified
        notifications = Notification.objects.filter(
            recipient=self.candidate,
            notification_type=Notification.NotificationType.INTERVIEW_SCHEDULED,
        )
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(
            notifications.first().metadata["interview_id"], interview_id
        )

    def test_25_interview_completion_triggers_notification(self):
        """Test that interview completion triggers notification."""
        resume = Resume.objects.create(user=self.candidate)
        file_content = SimpleUploadedFile(
            "resume.pdf", b"test content", content_type="application/pdf"
        )
        resume_version = ResumeVersion.objects.create(
            resume=resume,
            original_filename="resume.pdf",
            stored_filename="unique_resume.pdf",
            file=file_content,
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        application = Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            resume_version=resume_version,
        )
        interview = Interview.objects.create(
            application=application,
            scheduled_at=timezone.now() + timedelta(days=7),
            duration_minutes=60,
            interview_type=Interview.InterviewType.VIDEO,
            meeting_link="https://example.com/meet",
            created_by=self.recruiter,
        )
        Notification.objects.all().delete()
        # Complete interview
        from apps.interviews.services.workflow import InterviewWorkflowService

        InterviewWorkflowService.change_status(
            interview, Interview.InterviewStatus.COMPLETED, self.recruiter
        )
        # Check that candidate was notified
        notifications = Notification.objects.filter(
            recipient=self.candidate,
            notification_type=Notification.NotificationType.INTERVIEW_COMPLETED,
        )
        self.assertEqual(notifications.count(), 1)

    def test_26_interview_cancellation_triggers_notification(self):
        """Test that interview cancellation triggers notification."""
        resume = Resume.objects.create(user=self.candidate)
        file_content = SimpleUploadedFile(
            "resume.pdf", b"test content", content_type="application/pdf"
        )
        resume_version = ResumeVersion.objects.create(
            resume=resume,
            original_filename="resume.pdf",
            stored_filename="unique_resume.pdf",
            file=file_content,
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        application = Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            resume_version=resume_version,
        )
        interview = Interview.objects.create(
            application=application,
            scheduled_at=timezone.now() + timedelta(days=7),
            duration_minutes=60,
            interview_type=Interview.InterviewType.VIDEO,
            meeting_link="https://example.com/meet",
            created_by=self.recruiter,
        )
        Notification.objects.all().delete()
        # Cancel interview
        from apps.interviews.services.workflow import InterviewWorkflowService

        InterviewWorkflowService.change_status(
            interview, Interview.InterviewStatus.CANCELLED, self.recruiter
        )
        # Check that candidate was notified
        notifications = Notification.objects.filter(
            recipient=self.candidate,
            notification_type=Notification.NotificationType.INTERVIEW_CANCELLED,
        )
        self.assertEqual(notifications.count(), 1)

    def test_27_match_creation_triggers_notification(self):
        """Test that match creation triggers notification."""
        # Create resume with structured data
        resume = Resume.objects.create(user=self.candidate)
        file_content = SimpleUploadedFile(
            "resume.pdf", b"test content", content_type="application/pdf"
        )
        resume_version = ResumeVersion.objects.create(
            resume=resume,
            original_filename="resume.pdf",
            stored_filename="unique_resume.pdf",
            file=file_content,
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        structured_resume = StructuredResume.objects.create(
            resume_version=resume_version
        )
        Notification.objects.all().delete()
        # Create match
        from apps.matching.services.matching import MatchingService

        MatchingService.calculate_match(self.candidate, self.job)
        # Check that candidate was notified
        notifications = Notification.objects.filter(
            recipient=self.candidate,
            notification_type=Notification.NotificationType.MATCH_CREATED,
        )
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications.first().metadata["job_id"], str(self.job.id))
