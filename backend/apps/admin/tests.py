from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework.test import APIClient
from rest_framework import status

from apps.admin.models import ModerationLog
from apps.applications.models import Application
from apps.jobs.models import Job
from apps.resumes.models import Resume, ResumeVersion
from apps.users.models import User

User = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class AdminModerationTestCase(TestCase):
    """Base test case for admin moderation tests"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create admin user
        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="adminpass123",
            full_name="Admin User",
            role=User.Roles.ADMIN,
        )

        # Create candidate user
        self.candidate = User.objects.create_user(
            email="candidate@test.com",
            password="candidatepass123",
            full_name="Candidate User",
            role=User.Roles.CANDIDATE,
        )

        # Create recruiter user
        self.recruiter = User.objects.create_user(
            email="recruiter@test.com",
            password="recruiterpass123",
            full_name="Recruiter User",
            role=User.Roles.RECRUITER,
        )

        # Create inactive user
        self.inactive_user = User.objects.create_user(
            email="inactive@test.com",
            password="inactivepass123",
            full_name="Inactive User",
            role=User.Roles.CANDIDATE,
            is_active=False,
        )


class AdminUserListViewTests(AdminModerationTestCase):
    """Tests for admin user list view"""

    def test_1_admin_lists_users(self):
        """Admin can list all users"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 4)

    def test_2_pagination_works(self):
        """Pagination works correctly"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/users/?page=1&page_size=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIn("next", response.data)

    def test_3_ordering_works(self):
        """Ordering works correctly"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/users/?ordering=email")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = [user["email"] for user in response.data["results"]]
        self.assertEqual(emails, sorted(emails))

    def test_4_filter_candidates(self):
        """Filter by candidate role works"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/users/?role=candidate")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        for user in response.data["results"]:
            self.assertEqual(user["role"], "candidate")

    def test_5_filter_recruiters(self):
        """Filter by recruiter role works"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/users/?role=recruiter")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["role"], "recruiter")

    def test_6_search_email(self):
        """Search by email works"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/users/?search=candidate")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_7_search_name(self):
        """Search by name works"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/users/?search=Candidate")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)


class AdminUserDetailViewTests(AdminModerationTestCase):
    """Tests for admin user detail view"""

    def test_8_admin_updates_user(self):
        """Admin can update user"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/admin/users/{self.candidate.id}/",
            {"is_active": False, "reason": "Violation"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.candidate.refresh_from_db()
        self.assertFalse(self.candidate.is_active)

    def test_9_moderation_log_created(self):
        """Moderation log is created on user update"""
        self.client.force_authenticate(user=self.admin)
        initial_log_count = ModerationLog.objects.count()
        self.client.patch(
            f"/api/admin/users/{self.candidate.id}/",
            {"is_active": False, "reason": "Violation"},
        )
        self.assertEqual(ModerationLog.objects.count(), initial_log_count + 1)
        log = ModerationLog.objects.latest("created_at")
        self.assertEqual(log.resource_type, ModerationLog.ResourceType.USER)
        self.assertEqual(log.resource_id, self.candidate.id)

    def test_10_recruiter_blocked(self):
        """Recruiter cannot access admin endpoints"""
        self.client.force_authenticate(user=self.recruiter)
        response = self.client.get("/api/admin/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_11_candidate_blocked(self):
        """Candidate cannot access admin endpoints"""
        self.client.force_authenticate(user=self.candidate)
        response = self.client.get("/api/admin/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_12_anonymous_blocked(self):
        """Anonymous user cannot access admin endpoints"""
        response = self.client.get("/api/admin/users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_25_user_detail_endpoint(self):
        """Admin can get user detail"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/admin/users/{self.candidate.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.candidate.id))

    def test_26_inactive_user_update(self):
        """Admin can update inactive user"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/admin/users/{self.inactive_user.id}/",
            {"is_active": True, "reason": "Reactivated"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.inactive_user.refresh_from_db()
        self.assertTrue(self.inactive_user.is_active)

    def test_27_role_update(self):
        """Admin can update user role"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/admin/users/{self.candidate.id}/",
            {"role": User.Roles.RECRUITER, "reason": "Role change"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.role, User.Roles.RECRUITER)


class AdminJobListViewTests(AdminModerationTestCase):
    """Tests for admin job list view"""

    def setUp(self):
        super().setUp()
        # Create test jobs
        self.job1 = Job.objects.create(
            recruiter=self.recruiter,
            title="Software Engineer",
            company_name="Tech Corp",
            location="Remote",
            description="Python developer role",
            status=Job.JobStatus.ACTIVE,
        )
        self.job2 = Job.objects.create(
            recruiter=self.recruiter,
            title="Data Scientist",
            company_name="Data Inc",
            location="NYC",
            description="ML role",
            status=Job.JobStatus.DRAFT,
        )
        self.job3 = Job.objects.create(
            recruiter=self.recruiter,
            title="Product Manager",
            company_name="Product Co",
            location="SF",
            description="PM role",
            status=Job.JobStatus.CLOSED,
        )

    def test_13_admin_lists_jobs(self):
        """Admin can list all jobs"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/jobs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_14_admin_filters_jobs(self):
        """Admin can filter jobs by status"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/jobs/?status=active")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["status"], "active")


class AdminJobDetailViewTests(AdminModerationTestCase):
    """Tests for admin job detail view"""

    def setUp(self):
        super().setUp()
        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Software Engineer",
            company_name="Tech Corp",
            location="Remote",
            description="Python developer role",
            status=Job.JobStatus.ACTIVE,
        )

    def test_15_admin_updates_job(self):
        """Admin can update job status"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/admin/jobs/{self.job.id}/",
            {"status": Job.JobStatus.CLOSED, "reason": "Policy violation"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.JobStatus.CLOSED)

    def test_16_job_moderation_log_created(self):
        """Moderation log is created on job update"""
        self.client.force_authenticate(user=self.admin)
        initial_log_count = ModerationLog.objects.count()
        self.client.patch(
            f"/api/admin/jobs/{self.job.id}/",
            {"status": Job.JobStatus.CLOSED, "reason": "Policy violation"},
        )
        self.assertEqual(ModerationLog.objects.count(), initial_log_count + 1)
        log = ModerationLog.objects.latest("created_at")
        self.assertEqual(log.resource_type, ModerationLog.ResourceType.JOB)
        self.assertEqual(log.resource_id, self.job.id)


class AdminResumeListViewTests(AdminModerationTestCase):
    """Tests for admin resume list view"""

    def setUp(self):
        super().setUp()
        # Create resumes
        self.resume1 = Resume.objects.create(user=self.candidate)
        self.resume2 = Resume.objects.create(user=self.inactive_user)

    def test_17_admin_lists_resumes(self):
        """Admin can list all resumes"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/resumes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)


class AdminResumeDetailViewTests(AdminModerationTestCase):
    """Tests for admin resume detail view"""

    def setUp(self):
        super().setUp()
        self.resume = Resume.objects.create(user=self.candidate)

    def test_18_admin_updates_resume(self):
        """Admin can update resume (deactivate user)"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/admin/resumes/{self.resume.id}/",
            {"is_active": False, "reason": "Violation"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.candidate.refresh_from_db()
        self.assertFalse(self.candidate.is_active)

    def test_19_resume_moderation_log_created(self):
        """Moderation log is created on resume update"""
        self.client.force_authenticate(user=self.admin)
        initial_log_count = ModerationLog.objects.count()
        self.client.patch(
            f"/api/admin/resumes/{self.resume.id}/",
            {"is_active": False, "reason": "Violation"},
        )
        self.assertEqual(ModerationLog.objects.count(), initial_log_count + 1)
        log = ModerationLog.objects.latest("created_at")
        self.assertEqual(log.resource_type, ModerationLog.ResourceType.RESUME)
        self.assertEqual(log.resource_id, self.resume.id)


class AdminApplicationListViewTests(AdminModerationTestCase):
    """Tests for admin application list view"""

    def setUp(self):
        super().setUp()
        # Create job and resume version
        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Software Engineer",
            company_name="Tech Corp",
            location="Remote",
            description="Python developer role",
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
            status=Application.ApplicationStatus.SUBMITTED,
        )

    def test_20_admin_lists_applications(self):
        """Admin can list all applications"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/applications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_21_application_filtering(self):
        """Admin can filter applications by status"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/applications/?status=submitted")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_35_read_only_application_moderation_enforced(self):
        """Application moderation is read-only (no PATCH endpoint)"""
        self.client.force_authenticate(user=self.admin)
        # Attempt to patch application status (should fail - no endpoint exists)
        response = self.client.patch(
            f"/api/admin/applications/{self.application.id}/",
            {"status": "shortlisted"},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminDashboardViewTests(AdminModerationTestCase):
    """Tests for admin dashboard view"""

    def setUp(self):
        super().setUp()
        # Create additional test data
        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Software Engineer",
            company_name="Tech Corp",
            location="Remote",
            description="Python developer role",
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
            status=Application.ApplicationStatus.SUBMITTED,
        )

    def test_22_dashboard_endpoint_works(self):
        """Dashboard endpoint works"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_23_dashboard_counts_correct(self):
        """Dashboard counts are correct"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/admin/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_users"], 4)
        self.assertEqual(response.data["total_candidates"], 2)
        self.assertEqual(response.data["total_recruiters"], 1)
        self.assertEqual(response.data["active_users"], 3)
        self.assertEqual(response.data["inactive_users"], 1)
        self.assertEqual(response.data["total_jobs"], 1)
        self.assertEqual(response.data["active_jobs"], 1)
        self.assertEqual(response.data["draft_jobs"], 0)
        self.assertEqual(response.data["closed_jobs"], 0)
        self.assertEqual(response.data["total_resumes"], 1)
        self.assertEqual(response.data["total_applications"], 1)


class QueryOptimizationTests(AdminModerationTestCase):
    """Tests for query optimization"""

    def setUp(self):
        super().setUp()
        # Create additional test data
        for i in range(5):
            candidate = User.objects.create_user(
                email=f"candidate{i}@test.com",
                password="pass123",
                full_name=f"Candidate {i}",
                role=User.Roles.CANDIDATE,
            )
            job = Job.objects.create(
                recruiter=self.recruiter,
                title=f"Job {i}",
                company_name=f"Company {i}",
                location="Remote",
                description=f"Description {i}",
                status=Job.JobStatus.ACTIVE,
            )
            resume = Resume.objects.create(user=candidate)
            resume_version = ResumeVersion.objects.create(
                resume=resume,
                original_filename="resume.pdf",
                stored_filename=f"resume_{i}.pdf",
                file_size=1024,
                mime_type="application/pdf",
                version_number=1,
                is_current=True,
            )
            Application.objects.create(
                job=job,
                candidate=candidate,
                resume_version=resume_version,
                status=Application.ApplicationStatus.SUBMITTED,
            )

    def test_24_aggregate_query_optimization(self):
        """Dashboard uses aggregate queries efficiently"""
        self.client.force_authenticate(user=self.admin)
        with self.assertNumQueries(6):  # 6 aggregate queries
            self.client.get("/api/admin/dashboard/")

    def test_30_query_optimization_user_list(self):
        """User list uses select_related efficiently"""
        self.client.force_authenticate(user=self.admin)
        with self.assertNumQueries(2):  # 1 for count, 1 for data
            self.client.get("/api/admin/users/")

    def test_31_query_optimization_job_list(self):
        """Job list uses select_related efficiently"""
        self.client.force_authenticate(user=self.admin)
        with self.assertNumQueries(2):  # 1 for count, 1 for data
            self.client.get("/api/admin/jobs/")

    def test_32_query_optimization_resume_list(self):
        """Resume list uses select_related efficiently"""
        self.client.force_authenticate(user=self.admin)
        with self.assertNumQueries(2):  # 1 for count, 1 for data
            self.client.get("/api/admin/resumes/")

    def test_33_query_optimization_application_list(self):
        """Application list uses select_related efficiently"""
        self.client.force_authenticate(user=self.admin)
        with self.assertNumQueries(2):  # 1 for count, 1 for data
            self.client.get("/api/admin/applications/")

    def test_34_query_optimization_dashboard(self):
        """Dashboard uses aggregate queries (no N+1)"""
        self.client.force_authenticate(user=self.admin)
        with self.assertNumQueries(6):  # 6 aggregate queries
            self.client.get("/api/admin/dashboard/")


class ModerationLogTests(AdminModerationTestCase):
    """Tests for moderation log functionality"""

    def test_28_moderation_metadata_stored(self):
        """Moderation metadata is stored correctly"""
        self.client.force_authenticate(user=self.admin)
        self.client.patch(
            f"/api/admin/users/{self.candidate.id}/",
            {"is_active": False, "reason": "Violation"},
        )
        log = ModerationLog.objects.latest("created_at")
        self.assertIn("old_is_active", log.metadata)
        self.assertIn("new_is_active", log.metadata)
        self.assertTrue(log.metadata["old_is_active"])
        self.assertFalse(log.metadata["new_is_active"])

    def test_29_moderation_reason_stored(self):
        """Moderation reason is stored correctly"""
        self.client.force_authenticate(user=self.admin)
        reason = "Policy violation - spam"
        self.client.patch(
            f"/api/admin/users/{self.candidate.id}/",
            {"is_active": False, "reason": reason},
        )
        log = ModerationLog.objects.latest("created_at")
        self.assertEqual(log.reason, reason)
