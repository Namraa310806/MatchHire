from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.applications.models import Application
from apps.interviews.models import Interview, InterviewStatusHistory
from apps.interviews.services.workflow import InterviewWorkflowService
from apps.jobs.models import Job
from apps.resumes.models import Resume, ResumeVersion

User = get_user_model()


class InterviewModelTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="pass12345",
            full_name="Recruiter One",
            role=User.Roles.RECRUITER,
        )
        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            password="pass12345",
            full_name="Candidate One",
            role=User.Roles.CANDIDATE,
        )
        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Software Engineer",
            company_name="Tech Corp",
            location="San Francisco",
            description="We need a software engineer",
            status=Job.JobStatus.ACTIVE,
        )
        self.resume = Resume.objects.create(user=self.candidate)
        self.resume_version = ResumeVersion.objects.create(
            resume=self.resume,
            original_filename="resume.pdf",
            stored_filename="unique_resume.pdf",
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        self.application = Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            resume_version=self.resume_version,
            status=Application.ApplicationStatus.UNDER_REVIEW,
        )

    def test_10_video_interview_requires_meeting_link(self):
        """Test 10: VIDEO interview requires meeting_link"""
        with self.assertRaises(Exception):
            interview = Interview(
                application=self.application,
                scheduled_at=timezone.now() + timezone.timedelta(days=1),
                duration_minutes=60,
                interview_type=Interview.InterviewType.VIDEO,
                meeting_link="",
                location="",
                created_by=self.recruiter,
            )
            interview.full_clean()

    def test_11_onsite_interview_requires_location(self):
        """Test 11: ONSITE interview requires location"""
        with self.assertRaises(Exception):
            interview = Interview(
                application=self.application,
                scheduled_at=timezone.now() + timezone.timedelta(days=1),
                duration_minutes=60,
                interview_type=Interview.InterviewType.ONSITE,
                meeting_link="",
                location="",
                created_by=self.recruiter,
            )
            interview.full_clean()

    def test_12_duration_must_be_positive(self):
        """Test 12: duration must be positive"""
        with self.assertRaises(Exception):
            interview = Interview(
                application=self.application,
                scheduled_at=timezone.now() + timezone.timedelta(days=1),
                duration_minutes=0,
                interview_type=Interview.InterviewType.PHONE,
                created_by=self.recruiter,
            )
            interview.full_clean()


class InterviewWorkflowServiceTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="pass12345",
            full_name="Recruiter One",
            role=User.Roles.RECRUITER,
        )
        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            password="pass12345",
            full_name="Candidate One",
            role=User.Roles.CANDIDATE,
        )
        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Software Engineer",
            company_name="Tech Corp",
            location="San Francisco",
            description="We need a software engineer",
            status=Job.JobStatus.ACTIVE,
        )
        self.resume = Resume.objects.create(user=self.candidate)
        self.resume_version = ResumeVersion.objects.create(
            resume=self.resume,
            original_filename="resume.pdf",
            stored_filename="unique_resume.pdf",
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        self.application = Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            resume_version=self.resume_version,
            status=Application.ApplicationStatus.UNDER_REVIEW,
        )
        self.interview = Interview.objects.create(
            application=self.application,
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            duration_minutes=60,
            interview_type=Interview.InterviewType.VIDEO,
            meeting_link="https://zoom.us/j/123456",
            created_by=self.recruiter,
        )

    def test_20_invalid_transition_blocked(self):
        """Test 20: invalid transition blocked"""
        with self.assertRaises(ValueError):
            InterviewWorkflowService.change_status(
                self.interview, Interview.InterviewStatus.SCHEDULED, self.recruiter
            )

    def test_21_completed_cannot_transition(self):
        """Test 21: completed cannot transition"""
        self.interview.status = Interview.InterviewStatus.COMPLETED
        self.interview.save()
        result = InterviewWorkflowService.validate_transition(
            Interview.InterviewStatus.COMPLETED, Interview.InterviewStatus.SCHEDULED
        )
        self.assertFalse(result)

    def test_22_cancelled_cannot_transition(self):
        """Test 22: cancelled cannot transition"""
        self.interview.status = Interview.InterviewStatus.CANCELLED
        self.interview.save()
        result = InterviewWorkflowService.validate_transition(
            Interview.InterviewStatus.CANCELLED, Interview.InterviewStatus.SCHEDULED
        )
        self.assertFalse(result)

    def test_23_history_record_created(self):
        """Test 23: history record created"""
        initial_count = InterviewStatusHistory.objects.count()
        InterviewWorkflowService.change_status(
            self.interview, Interview.InterviewStatus.COMPLETED, self.recruiter
        )
        self.assertEqual(InterviewStatusHistory.objects.count(), initial_count + 1)
        history = InterviewStatusHistory.objects.first()
        self.assertEqual(history.old_status, Interview.InterviewStatus.SCHEDULED)
        self.assertEqual(history.new_status, Interview.InterviewStatus.COMPLETED)


class InterviewAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.recruiter1 = User.objects.create_user(
            email="recruiter1@example.com",
            password="pass12345",
            full_name="Recruiter One",
            role=User.Roles.RECRUITER,
        )
        self.recruiter2 = User.objects.create_user(
            email="recruiter2@example.com",
            password="pass12345",
            full_name="Recruiter Two",
            role=User.Roles.RECRUITER,
        )
        self.candidate1 = User.objects.create_user(
            email="candidate1@example.com",
            password="pass12345",
            full_name="Candidate One",
            role=User.Roles.CANDIDATE,
        )
        self.candidate2 = User.objects.create_user(
            email="candidate2@example.com",
            password="pass12345",
            full_name="Candidate Two",
            role=User.Roles.CANDIDATE,
        )

        # Create jobs
        self.job1 = Job.objects.create(
            recruiter=self.recruiter1,
            title="Software Engineer",
            company_name="Tech Corp",
            location="San Francisco",
            description="We need a software engineer",
            status=Job.JobStatus.ACTIVE,
        )
        self.job2 = Job.objects.create(
            recruiter=self.recruiter2,
            title="Data Scientist",
            company_name="Data Corp",
            location="New York",
            description="We need a data scientist",
            status=Job.JobStatus.ACTIVE,
        )

        # Create additional candidates for different application statuses
        self.candidate3 = User.objects.create_user(
            email="candidate3@example.com",
            password="pass12345",
            full_name="Candidate Three",
            role=User.Roles.CANDIDATE,
        )
        self.candidate4 = User.objects.create_user(
            email="candidate4@example.com",
            password="pass12345",
            full_name="Candidate Four",
            role=User.Roles.CANDIDATE,
        )
        self.candidate5 = User.objects.create_user(
            email="candidate5@example.com",
            password="pass12345",
            full_name="Candidate Five",
            role=User.Roles.CANDIDATE,
        )
        self.candidate6 = User.objects.create_user(
            email="candidate6@example.com",
            password="pass12345",
            full_name="Candidate Six",
            role=User.Roles.CANDIDATE,
        )

        # Create resumes for all candidates
        self.resume1 = Resume.objects.create(user=self.candidate1)
        self.resume_version1 = ResumeVersion.objects.create(
            resume=self.resume1,
            original_filename="resume1.pdf",
            stored_filename="unique_resume1.pdf",
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        self.resume2 = Resume.objects.create(user=self.candidate2)
        self.resume_version2 = ResumeVersion.objects.create(
            resume=self.resume2,
            original_filename="resume2.pdf",
            stored_filename="unique_resume2.pdf",
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        self.resume3 = Resume.objects.create(user=self.candidate3)
        self.resume_version3 = ResumeVersion.objects.create(
            resume=self.resume3,
            original_filename="resume3.pdf",
            stored_filename="unique_resume3.pdf",
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        self.resume4 = Resume.objects.create(user=self.candidate4)
        self.resume_version4 = ResumeVersion.objects.create(
            resume=self.resume4,
            original_filename="resume4.pdf",
            stored_filename="unique_resume4.pdf",
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        self.resume5 = Resume.objects.create(user=self.candidate5)
        self.resume_version5 = ResumeVersion.objects.create(
            resume=self.resume5,
            original_filename="resume5.pdf",
            stored_filename="unique_resume5.pdf",
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        self.resume6 = Resume.objects.create(user=self.candidate6)
        self.resume_version6 = ResumeVersion.objects.create(
            resume=self.resume6,
            original_filename="resume6.pdf",
            stored_filename="unique_resume6.pdf",
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )

        # Create applications with different statuses (each for a different candidate)
        self.app_submitted = Application.objects.create(
            job=self.job1,
            candidate=self.candidate3,
            resume_version=self.resume_version3,
            status=Application.ApplicationStatus.SUBMITTED,
        )
        self.app_under_review = Application.objects.create(
            job=self.job1,
            candidate=self.candidate1,
            resume_version=self.resume_version1,
            status=Application.ApplicationStatus.UNDER_REVIEW,
        )
        self.app_shortlisted = Application.objects.create(
            job=self.job1,
            candidate=self.candidate4,
            resume_version=self.resume_version4,
            status=Application.ApplicationStatus.SHORTLISTED,
        )
        self.app_rejected = Application.objects.create(
            job=self.job1,
            candidate=self.candidate5,
            resume_version=self.resume_version5,
            status=Application.ApplicationStatus.REJECTED,
        )
        self.app_hired = Application.objects.create(
            job=self.job1,
            candidate=self.candidate6,
            resume_version=self.resume_version6,
            status=Application.ApplicationStatus.HIRED,
        )
        self.app_other_candidate = Application.objects.create(
            job=self.job1,
            candidate=self.candidate2,
            resume_version=self.resume_version2,
            status=Application.ApplicationStatus.UNDER_REVIEW,
        )
        self.app_other_recruiter = Application.objects.create(
            job=self.job2,
            candidate=self.candidate1,
            resume_version=self.resume_version1,
            status=Application.ApplicationStatus.UNDER_REVIEW,
        )

    def test_1_recruiter_schedules_interview(self):
        """Test 1: recruiter schedules interview"""
        self.client.force_authenticate(user=self.recruiter1)
        data = {
            "scheduled_at": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            "duration_minutes": 60,
            "interview_type": Interview.InterviewType.VIDEO,
            "meeting_link": "https://zoom.us/j/123456",
            "notes": "Technical interview",
        }
        response = self.client.post(
            f"/api/applications/{self.app_under_review.id}/interviews/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Interview.objects.count(), 1)

    def test_2_candidate_cannot_schedule(self):
        """Test 2: candidate cannot schedule"""
        self.client.force_authenticate(user=self.candidate1)
        data = {
            "scheduled_at": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            "duration_minutes": 60,
            "interview_type": Interview.InterviewType.VIDEO,
            "meeting_link": "https://zoom.us/j/123456",
        }
        response = self.client.post(
            f"/api/applications/{self.app_under_review.id}/interviews/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_3_anonymous_blocked(self):
        """Test 3: anonymous blocked"""
        data = {
            "scheduled_at": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            "duration_minutes": 60,
            "interview_type": Interview.InterviewType.VIDEO,
            "meeting_link": "https://zoom.us/j/123456",
        }
        response = self.client.post(
            f"/api/applications/{self.app_under_review.id}/interviews/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_4_recruiter_ownership_enforced(self):
        """Test 4: recruiter ownership enforced"""
        self.client.force_authenticate(user=self.recruiter2)
        data = {
            "scheduled_at": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            "duration_minutes": 60,
            "interview_type": Interview.InterviewType.VIDEO,
            "meeting_link": "https://zoom.us/j/123456",
        }
        response = self.client.post(
            f"/api/applications/{self.app_under_review.id}/interviews/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_5_cannot_schedule_for_submitted(self):
        """Test 5: cannot schedule for submitted application"""
        self.client.force_authenticate(user=self.recruiter1)
        data = {
            "scheduled_at": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            "duration_minutes": 60,
            "interview_type": Interview.InterviewType.VIDEO,
            "meeting_link": "https://zoom.us/j/123456",
        }
        response = self.client.post(
            f"/api/applications/{self.app_submitted.id}/interviews/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_6_can_schedule_for_under_review(self):
        """Test 6: can schedule for under_review"""
        self.client.force_authenticate(user=self.recruiter1)
        data = {
            "scheduled_at": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            "duration_minutes": 60,
            "interview_type": Interview.InterviewType.VIDEO,
            "meeting_link": "https://zoom.us/j/123456",
        }
        response = self.client.post(
            f"/api/applications/{self.app_under_review.id}/interviews/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_7_can_schedule_for_shortlisted(self):
        """Test 7: can schedule for shortlisted"""
        self.client.force_authenticate(user=self.recruiter1)
        data = {
            "scheduled_at": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            "duration_minutes": 60,
            "interview_type": Interview.InterviewType.VIDEO,
            "meeting_link": "https://zoom.us/j/123456",
        }
        response = self.client.post(
            f"/api/applications/{self.app_shortlisted.id}/interviews/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_8_cannot_schedule_for_rejected(self):
        """Test 8: cannot schedule for rejected"""
        self.client.force_authenticate(user=self.recruiter1)
        data = {
            "scheduled_at": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            "duration_minutes": 60,
            "interview_type": Interview.InterviewType.VIDEO,
            "meeting_link": "https://zoom.us/j/123456",
        }
        response = self.client.post(
            f"/api/applications/{self.app_rejected.id}/interviews/", data, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_9_cannot_schedule_for_hired(self):
        """Test 9: cannot schedule for hired"""
        self.client.force_authenticate(user=self.recruiter1)
        data = {
            "scheduled_at": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            "duration_minutes": 60,
            "interview_type": Interview.InterviewType.VIDEO,
            "meeting_link": "https://zoom.us/j/123456",
        }
        response = self.client.post(
            f"/api/applications/{self.app_hired.id}/interviews/", data, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_13_candidate_lists_own_interviews(self):
        """Test 13: candidate lists own interviews"""
        # Create an interview for candidate1
        Interview.objects.create(
            application=self.app_under_review,
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            duration_minutes=60,
            interview_type=Interview.InterviewType.VIDEO,
            meeting_link="https://zoom.us/j/123456",
            created_by=self.recruiter1,
        )
        self.client.force_authenticate(user=self.candidate1)
        response = self.client.get(
            f"/api/applications/{self.app_under_review.id}/interviews/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_14_candidate_cannot_view_another_interview(self):
        """Test 14: candidate cannot view another interview"""
        # Create an interview for candidate2
        Interview.objects.create(
            application=self.app_other_candidate,
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            duration_minutes=60,
            interview_type=Interview.InterviewType.VIDEO,
            meeting_link="https://zoom.us/j/123456",
            created_by=self.recruiter1,
        )
        self.client.force_authenticate(user=self.candidate1)
        response = self.client.get(
            f"/api/applications/{self.app_other_candidate.id}/interviews/"
        )
        self.assertEqual(response.status_code, 404)

    def test_15_recruiter_lists_interviews(self):
        """Test 15: recruiter lists interviews"""
        Interview.objects.create(
            application=self.app_under_review,
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            duration_minutes=60,
            interview_type=Interview.InterviewType.VIDEO,
            meeting_link="https://zoom.us/j/123456",
            created_by=self.recruiter1,
        )
        self.client.force_authenticate(user=self.recruiter1)
        response = self.client.get(
            f"/api/applications/{self.app_under_review.id}/interviews/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_16_recruiter_cannot_access_another_recruiter_interview(self):
        """Test 16: recruiter cannot access another recruiter interview"""
        Interview.objects.create(
            application=self.app_other_recruiter,
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            duration_minutes=60,
            interview_type=Interview.InterviewType.VIDEO,
            meeting_link="https://zoom.us/j/123456",
            created_by=self.recruiter2,
        )
        self.client.force_authenticate(user=self.recruiter1)
        response = self.client.get(
            f"/api/applications/{self.app_other_recruiter.id}/interviews/"
        )
        self.assertEqual(response.status_code, 404)

    def test_17_detail_endpoint_works(self):
        """Test 17: detail endpoint works"""
        interview = Interview.objects.create(
            application=self.app_under_review,
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            duration_minutes=60,
            interview_type=Interview.InterviewType.VIDEO,
            meeting_link="https://zoom.us/j/123456",
            created_by=self.recruiter1,
        )
        self.client.force_authenticate(user=self.recruiter1)
        response = self.client.get(f"/api/interviews/{interview.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(interview.id))

    def test_18_complete_interview_works(self):
        """Test 18: complete interview works"""
        interview = Interview.objects.create(
            application=self.app_under_review,
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            duration_minutes=60,
            interview_type=Interview.InterviewType.VIDEO,
            meeting_link="https://zoom.us/j/123456",
            created_by=self.recruiter1,
        )
        self.client.force_authenticate(user=self.recruiter1)
        data = {"status": Interview.InterviewStatus.COMPLETED}
        response = self.client.patch(
            f"/api/interviews/{interview.id}/status/", data, format="json"
        )
        self.assertEqual(response.status_code, 200)
        interview.refresh_from_db()
        self.assertEqual(interview.status, Interview.InterviewStatus.COMPLETED)

    def test_19_cancel_interview_works(self):
        """Test 19: cancel interview works"""
        interview = Interview.objects.create(
            application=self.app_under_review,
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            duration_minutes=60,
            interview_type=Interview.InterviewType.VIDEO,
            meeting_link="https://zoom.us/j/123456",
            created_by=self.recruiter1,
        )
        self.client.force_authenticate(user=self.recruiter1)
        data = {"status": Interview.InterviewStatus.CANCELLED}
        response = self.client.patch(
            f"/api/interviews/{interview.id}/status/", data, format="json"
        )
        self.assertEqual(response.status_code, 200)
        interview.refresh_from_db()
        self.assertEqual(interview.status, Interview.InterviewStatus.CANCELLED)

    def test_24_history_endpoint_works(self):
        """Test 24: history endpoint works"""
        interview = Interview.objects.create(
            application=self.app_under_review,
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            duration_minutes=60,
            interview_type=Interview.InterviewType.VIDEO,
            meeting_link="https://zoom.us/j/123456",
            created_by=self.recruiter1,
        )
        # Change status to create history
        InterviewWorkflowService.change_status(
            interview, Interview.InterviewStatus.COMPLETED, self.recruiter1
        )
        self.client.force_authenticate(user=self.recruiter1)
        response = self.client.get(f"/api/interviews/{interview.id}/history/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["new_status"], Interview.InterviewStatus.COMPLETED
        )

    def test_25_query_optimization_verified(self):
        """Test 25: query optimization verified"""
        interview = Interview.objects.create(
            application=self.app_under_review,
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            duration_minutes=60,
            interview_type=Interview.InterviewType.VIDEO,
            meeting_link="https://zoom.us/j/123456",
            created_by=self.recruiter1,
        )
        self.client.force_authenticate(user=self.recruiter1)

        # Test list endpoint - should use select_related to avoid N+1
        # The interviews query uses select_related for all related objects
        with self.assertNumQueries(3):
            response = self.client.get(
                f"/api/applications/{self.app_under_review.id}/interviews/"
            )
            # Verify the response contains interview data
            self.assertEqual(response.status_code, 200)

        # Test detail endpoint - should use select_related
        # Single query fetches interview with all related objects (plus auth query)
        with self.assertNumQueries(2):
            response = self.client.get(f"/api/interviews/{interview.id}/")
            self.assertEqual(response.status_code, 200)

        # Test history endpoint - should use select_related on changed_by
        InterviewWorkflowService.change_status(
            interview, Interview.InterviewStatus.COMPLETED, self.recruiter1
        )
        with self.assertNumQueries(3):
            response = self.client.get(f"/api/interviews/{interview.id}/history/")
            self.assertEqual(response.status_code, 200)
