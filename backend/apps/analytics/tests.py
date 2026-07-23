from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.applications.models import Application
from apps.interviews.models import Interview
from apps.jobs.models import Job
from apps.matching.models import JobMatch
from apps.resumes.models import Resume, ResumeVersion
from apps.analytics.views import TOP_CANDIDATES_LIMIT

User = get_user_model()


class AnalyticsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create recruiters
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

        # Create candidates
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

        # Create resume containers for candidates
        self.resume_container1 = Resume.objects.create(user=self.candidate1)
        self.resume_container2 = Resume.objects.create(user=self.candidate2)
        self.resume_container3 = Resume.objects.create(user=self.candidate3)
        self.resume_container4 = Resume.objects.create(user=self.candidate4)
        self.resume_container5 = Resume.objects.create(user=self.candidate5)

        # Create resume versions for candidates
        self.resume1 = ResumeVersion.objects.create(
            resume=self.resume_container1,
            original_filename="resume1.pdf",
            stored_filename="resume1_v1.pdf",
            file=SimpleUploadedFile("resume1.pdf", b"fake pdf content"),
            file_size=100,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        self.resume2 = ResumeVersion.objects.create(
            resume=self.resume_container2,
            original_filename="resume2.pdf",
            stored_filename="resume2_v1.pdf",
            file=SimpleUploadedFile("resume2.pdf", b"fake pdf content"),
            file_size=100,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        self.resume3 = ResumeVersion.objects.create(
            resume=self.resume_container3,
            original_filename="resume3.pdf",
            stored_filename="resume3_v1.pdf",
            file=SimpleUploadedFile("resume3.pdf", b"fake pdf content"),
            file_size=100,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        self.resume4 = ResumeVersion.objects.create(
            resume=self.resume_container4,
            original_filename="resume4.pdf",
            stored_filename="resume4_v1.pdf",
            file=SimpleUploadedFile("resume4.pdf", b"fake pdf content"),
            file_size=100,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        self.resume5 = ResumeVersion.objects.create(
            resume=self.resume_container5,
            original_filename="resume5.pdf",
            stored_filename="resume5_v1.pdf",
            file=SimpleUploadedFile("resume5.pdf", b"fake pdf content"),
            file_size=100,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )

        # Create jobs for recruiter1
        self.job1 = Job.objects.create(
            recruiter=self.recruiter1,
            title="Software Engineer",
            company_name="Tech Corp",
            location="San Francisco",
            description="We need a software engineer",
            status=Job.JobStatus.ACTIVE,
        )
        self.job2 = Job.objects.create(
            recruiter=self.recruiter1,
            title="Data Scientist",
            company_name="Tech Corp",
            location="New York",
            description="We need a data scientist",
            status=Job.JobStatus.ACTIVE,
        )
        self.job3 = Job.objects.create(
            recruiter=self.recruiter1,
            title="Product Manager",
            company_name="Tech Corp",
            location="Austin",
            description="We need a product manager",
            status=Job.JobStatus.CLOSED,
        )
        self.job5 = Job.objects.create(
            recruiter=self.recruiter1,
            title="Senior Engineer",
            company_name="Tech Corp",
            location="Boston",
            description="We need a senior engineer",
            status=Job.JobStatus.ACTIVE,
        )

        # Create job for recruiter2
        self.job4 = Job.objects.create(
            recruiter=self.recruiter2,
            title="DevOps Engineer",
            company_name="Other Corp",
            location="Seattle",
            description="We need a devops engineer",
            status=Job.JobStatus.ACTIVE,
        )

        # Create applications for job1 (using unique candidates to avoid constraint violation)
        self.app1 = Application.objects.create(
            job=self.job1,
            candidate=self.candidate1,
            resume_version=self.resume1,
            status=Application.ApplicationStatus.SUBMITTED,
        )
        self.app2 = Application.objects.create(
            job=self.job1,
            candidate=self.candidate2,
            resume_version=self.resume2,
            status=Application.ApplicationStatus.UNDER_REVIEW,
        )
        self.app3 = Application.objects.create(
            job=self.job1,
            candidate=self.candidate3,
            resume_version=self.resume3,
            status=Application.ApplicationStatus.SHORTLISTED,
        )
        self.app4 = Application.objects.create(
            job=self.job1,
            candidate=self.candidate4,
            resume_version=self.resume4,
            status=Application.ApplicationStatus.REJECTED,
        )
        self.app5 = Application.objects.create(
            job=self.job1,
            candidate=self.candidate5,
            resume_version=self.resume5,
            status=Application.ApplicationStatus.HIRED,
        )

        # Create applications for job2
        self.app6 = Application.objects.create(
            job=self.job2,
            candidate=self.candidate2,
            resume_version=self.resume2,
            status=Application.ApplicationStatus.SUBMITTED,
        )

        # Create additional applications for candidate1 to test candidate dashboard
        self.app7 = Application.objects.create(
            job=self.job2,
            candidate=self.candidate1,
            resume_version=self.resume1,
            status=Application.ApplicationStatus.SHORTLISTED,
        )
        self.app8 = Application.objects.create(
            job=self.job5,
            candidate=self.candidate1,
            resume_version=self.resume1,
            status=Application.ApplicationStatus.HIRED,
        )

        # Create interviews
        self.interview1 = Interview.objects.create(
            application=self.app1,
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            duration_minutes=60,
            status=Interview.InterviewStatus.SCHEDULED,
        )
        self.interview2 = Interview.objects.create(
            application=self.app3,
            scheduled_at=timezone.now() - timezone.timedelta(days=1),
            duration_minutes=60,
            status=Interview.InterviewStatus.COMPLETED,
        )
        self.interview3 = Interview.objects.create(
            application=self.app5,
            scheduled_at=timezone.now() + timezone.timedelta(days=2),
            duration_minutes=60,
            status=Interview.InterviewStatus.CANCELLED,
        )

        # Create job matches
        self.match1 = JobMatch.objects.create(
            candidate=self.candidate1,
            job=self.job1,
            match_score=85.50,
            skills_score=90.00,
            experience_score=80.00,
            education_score=85.00,
            matched_skills_count=8,
            total_required_skills=10,
        )
        self.match2 = JobMatch.objects.create(
            candidate=self.candidate2,
            job=self.job1,
            match_score=72.40,
            skills_score=75.00,
            experience_score=70.00,
            education_score=72.00,
            matched_skills_count=6,
            total_required_skills=10,
        )
        self.match3 = JobMatch.objects.create(
            candidate=self.candidate1,
            job=self.job2,
            match_score=65.00,
            skills_score=70.00,
            experience_score=60.00,
            education_score=65.00,
            matched_skills_count=5,
            total_required_skills=10,
        )
        self.match4 = JobMatch.objects.create(
            candidate=self.candidate1,
            job=self.job5,
            match_score=78.00,
            skills_score=80.00,
            experience_score=75.00,
            education_score=78.00,
            matched_skills_count=7,
            total_required_skills=10,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_1_recruiter_dashboard_works(self):
        """Test 1: Recruiter dashboard works"""
        self.authenticate(self.recruiter1)
        response = self.client.get("/api/analytics/recruiter/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("total_jobs", response.data)
        self.assertIn("total_applications", response.data)
        self.assertIn("scheduled_interviews", response.data)

    def test_2_candidate_dashboard_works(self):
        """Test 2: Candidate dashboard works"""
        self.authenticate(self.candidate1)
        response = self.client.get("/api/analytics/candidate/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("total_applications", response.data)
        self.assertIn("total_matches", response.data)
        self.assertIn("average_match_score", response.data)

    def test_3_recruiter_blocked_from_candidate_dashboard(self):
        """Test 3: Recruiter blocked from candidate dashboard"""
        self.authenticate(self.recruiter1)
        response = self.client.get("/api/analytics/candidate/dashboard/")
        self.assertEqual(response.status_code, 403)

    def test_4_candidate_blocked_from_recruiter_dashboard(self):
        """Test 4: Candidate blocked from recruiter dashboard"""
        self.authenticate(self.candidate1)
        response = self.client.get("/api/analytics/recruiter/dashboard/")
        self.assertEqual(response.status_code, 403)

    def test_5_anonymous_blocked(self):
        """Test 5: Anonymous blocked"""
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/analytics/recruiter/dashboard/")
        self.assertEqual(response.status_code, 401)
        response = self.client.get("/api/analytics/candidate/dashboard/")
        self.assertEqual(response.status_code, 401)

    def test_6_total_jobs_correct(self):
        """Test 6: Total jobs correct"""
        self.authenticate(self.recruiter1)
        response = self.client.get("/api/analytics/recruiter/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_jobs"], 4)

    def test_7_active_jobs_correct(self):
        """Test 7: Active jobs correct"""
        self.authenticate(self.recruiter1)
        response = self.client.get("/api/analytics/recruiter/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["active_jobs"], 3)

    def test_8_application_counts_correct(self):
        """Test 8: Application counts correct"""
        self.authenticate(self.recruiter1)
        response = self.client.get("/api/analytics/recruiter/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_applications"], 8)
        self.assertEqual(response.data["submitted_applications"], 2)
        self.assertEqual(response.data["under_review_applications"], 1)
        self.assertEqual(response.data["shortlisted_applications"], 2)
        self.assertEqual(response.data["rejected_applications"], 1)
        self.assertEqual(response.data["hired_applications"], 2)

    def test_9_interview_counts_correct(self):
        """Test 9: Interview counts correct"""
        self.authenticate(self.recruiter1)
        response = self.client.get("/api/analytics/recruiter/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["scheduled_interviews"], 1)
        self.assertEqual(response.data["completed_interviews"], 1)
        self.assertEqual(response.data["cancelled_interviews"], 1)

    def test_10_candidate_application_counts_correct(self):
        """Test 10: Candidate application counts correct"""
        self.authenticate(self.candidate1)
        response = self.client.get("/api/analytics/candidate/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_applications"], 3)
        self.assertEqual(response.data["submitted"], 1)
        self.assertEqual(response.data["under_review"], 0)
        self.assertEqual(response.data["shortlisted"], 1)
        self.assertEqual(response.data["rejected"], 0)
        self.assertEqual(response.data["hired"], 1)

    def test_11_total_matches_correct(self):
        """Test 11: Total matches correct"""
        self.authenticate(self.candidate1)
        response = self.client.get("/api/analytics/candidate/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_matches"], 3)

    def test_12_average_match_score_correct(self):
        """Test 12: Average match score correct"""
        self.authenticate(self.candidate1)
        response = self.client.get("/api/analytics/candidate/dashboard/")
        self.assertEqual(response.status_code, 200)
        # (85.50 + 65.00 + 78.00) / 3 = 76.17
        expected_avg = (85.50 + 65.00 + 78.00) / 3
        self.assertAlmostEqual(
            response.data["average_match_score"], expected_avg, places=2
        )

    def test_13_job_analytics_works(self):
        """Test 13: Job analytics works"""
        self.authenticate(self.recruiter1)
        response = self.client.get(f"/api/analytics/recruiter/jobs/{self.job1.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("job_id", response.data)
        self.assertIn("total_applications", response.data)
        self.assertIn("conversion_rate", response.data)

    def test_14_conversion_rate_correct(self):
        """Test 14: Conversion rate correct"""
        self.authenticate(self.recruiter1)
        response = self.client.get(f"/api/analytics/recruiter/jobs/{self.job1.id}/")
        self.assertEqual(response.status_code, 200)
        # 1 hired out of 5 applications = 20%
        expected_rate = (1 / 5) * 100
        self.assertEqual(response.data["conversion_rate"], expected_rate)

    def test_15_recruiter_ownership_enforced(self):
        """Test 15: Recruiter ownership enforced"""
        self.authenticate(self.recruiter2)
        response = self.client.get(f"/api/analytics/recruiter/jobs/{self.job1.id}/")
        self.assertEqual(response.status_code, 404)

    def test_16_top_candidates_endpoint_works(self):
        """Test 16: Top candidates endpoint works"""
        self.authenticate(self.recruiter1)
        response = self.client.get(
            f"/api/analytics/recruiter/jobs/{self.job1.id}/top-candidates/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_17_top_candidates_ordering_correct(self):
        """Test 17: Top candidates ordering correct"""
        self.authenticate(self.recruiter1)
        response = self.client.get(
            f"/api/analytics/recruiter/jobs/{self.job1.id}/top-candidates/"
        )
        self.assertEqual(response.status_code, 200)
        # Should be ordered by match_score DESC
        self.assertEqual(len(response.data), 2)
        self.assertGreater(
            response.data[0]["match_score"], response.data[1]["match_score"]
        )
        self.assertEqual(str(response.data[0]["candidate_id"]), str(self.candidate1.id))
        self.assertEqual(str(response.data[1]["candidate_id"]), str(self.candidate2.id))

    def test_18_empty_dashboard_handled(self):
        """Test 18: Empty dashboard handled"""
        # Create new recruiter with no data
        new_recruiter = User.objects.create_user(
            email="newrecruiter@example.com",
            password="pass12345",
            full_name="New Recruiter",
            role=User.Roles.RECRUITER,
        )
        self.authenticate(new_recruiter)
        response = self.client.get("/api/analytics/recruiter/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_jobs"], 0)
        self.assertEqual(response.data["total_applications"], 0)
        self.assertEqual(response.data["scheduled_interviews"], 0)

    def test_19_empty_job_analytics_handled(self):
        """Test 19: Empty job analytics handled"""
        # Create new job with no applications
        new_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="New Job",
            company_name="Tech Corp",
            location="Remote",
            description="A new job",
            status=Job.JobStatus.ACTIVE,
        )
        self.authenticate(self.recruiter1)
        response = self.client.get(f"/api/analytics/recruiter/jobs/{new_job.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_applications"], 0)
        self.assertEqual(response.data["conversion_rate"], 0.0)

    def test_20_query_optimization_recruiter_dashboard(self):
        """Test 20: Query optimization recruiter dashboard"""
        self.authenticate(self.recruiter1)
        # Should execute exactly 3 aggregate queries (jobs, applications, interviews)
        with self.assertNumQueries(3):
            response = self.client.get("/api/analytics/recruiter/dashboard/")
        self.assertEqual(response.status_code, 200)

    def test_21_query_optimization_candidate_dashboard(self):
        """Test 21: Query optimization candidate dashboard"""
        self.authenticate(self.candidate1)
        # Should execute exactly 3 aggregate queries (applications, interviews, matches)
        with self.assertNumQueries(3):
            response = self.client.get("/api/analytics/candidate/dashboard/")
        self.assertEqual(response.status_code, 200)

    def test_22_query_optimization_job_analytics(self):
        """Test 22: Query optimization job analytics"""
        self.authenticate(self.recruiter1)
        # Should execute exactly 2 queries (1 job fetch + 1 aggregate)
        with self.assertNumQueries(2):
            response = self.client.get(f"/api/analytics/recruiter/jobs/{self.job1.id}/")
        self.assertEqual(response.status_code, 200)

    def test_23_query_optimization_top_candidates(self):
        """Test 23: Query optimization top candidates"""
        self.authenticate(self.recruiter1)
        # Should execute exactly 2 queries (1 job fetch + 1 select_related query)
        with self.assertNumQueries(2):
            response = self.client.get(
                f"/api/analytics/recruiter/jobs/{self.job1.id}/top-candidates/"
            )
        self.assertEqual(response.status_code, 200)

    def test_24_serializer_output_correct(self):
        """Test 24: Serializer output correct"""
        self.authenticate(self.recruiter1)
        response = self.client.get("/api/analytics/recruiter/dashboard/")
        self.assertEqual(response.status_code, 200)
        # Check all expected fields are present
        expected_fields = [
            "total_jobs",
            "active_jobs",
            "closed_jobs",
            "total_applications",
            "submitted_applications",
            "under_review_applications",
            "shortlisted_applications",
            "rejected_applications",
            "hired_applications",
            "scheduled_interviews",
            "completed_interviews",
            "cancelled_interviews",
        ]
        for field in expected_fields:
            self.assertIn(field, response.data)

    def test_25_pagination_not_required(self):
        """Test 25: Pagination not required"""
        self.authenticate(self.recruiter1)
        response = self.client.get("/api/analytics/recruiter/dashboard/")
        self.assertEqual(response.status_code, 200)
        # Dashboard endpoints should not return paginated data
        self.assertNotIn("count", response.data)
        self.assertNotIn("next", response.data)
        self.assertNotIn("previous", response.data)
        self.assertNotIn("results", response.data)

    def test_26_zero_matches_returns_zero_not_none(self):
        """Test 26: Zero matches returns 0 not None"""
        # Create candidate with no matches
        new_candidate = User.objects.create_user(
            email="newcandidate@example.com",
            password="pass12345",
            full_name="New Candidate",
            role=User.Roles.CANDIDATE,
        )
        self.authenticate(new_candidate)
        response = self.client.get("/api/analytics/candidate/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_matches"], 0)
        self.assertEqual(response.data["average_match_score"], 0.0)
        self.assertIsNotNone(response.data["average_match_score"])

    def test_27_zero_applications_conversion_rate_zero(self):
        """Test 27: Zero applications conversion rate returns 0.0"""
        # Create new job with no applications
        new_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="New Position",
            company_name="Tech Corp",
            location="Remote",
            description="A new position",
            status=Job.JobStatus.ACTIVE,
        )
        self.authenticate(self.recruiter1)
        response = self.client.get(f"/api/analytics/recruiter/jobs/{new_job.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_applications"], 0)
        self.assertEqual(response.data["conversion_rate"], 0.0)

    def test_28_top_candidates_limit_20(self):
        """Test 28: Top candidates limited to TOP_CANDIDATES_LIMIT"""
        # Create TOP_CANDIDATES_LIMIT + 5 candidates with matches for job1
        for i in range(TOP_CANDIDATES_LIMIT + 5):
            candidate = User.objects.create_user(
                email=f"limit_test_candidate{i}@example.com",
                password="pass12345",
                full_name=f"Limit Test Candidate {i}",
                role=User.Roles.CANDIDATE,
            )
            resume_container = Resume.objects.create(user=candidate)
            ResumeVersion.objects.create(
                resume=resume_container,
                original_filename=f"limit_test_resume{i}.pdf",
                stored_filename=f"limit_test_resume{i}_v1.pdf",
                file=SimpleUploadedFile(
                    f"limit_test_resume{i}.pdf", b"fake pdf content"
                ),
                file_size=100,
                mime_type="application/pdf",
                version_number=1,
                is_current=True,
            )
            JobMatch.objects.create(
                candidate=candidate,
                job=self.job1,
                match_score=50.0 + i,
                skills_score=50.0 + i,
                experience_score=50.0 + i,
                education_score=50.0 + i,
                matched_skills_count=5,
                total_required_skills=10,
            )

        self.authenticate(self.recruiter1)
        response = self.client.get(
            f"/api/analytics/recruiter/jobs/{self.job1.id}/top-candidates/"
        )
        self.assertEqual(response.status_code, 200)
        # Should return exactly TOP_CANDIDATES_LIMIT candidates
        self.assertEqual(len(response.data), TOP_CANDIDATES_LIMIT)

    def test_29_recruiter_cannot_access_other_recruiter_dashboard(self):
        """Test 29: Recruiter cannot access other recruiter's dashboard"""
        self.authenticate(self.recruiter2)
        response = self.client.get("/api/analytics/recruiter/dashboard/")
        # Should return recruiter2's own dashboard data, not recruiter1's
        self.assertEqual(response.status_code, 200)
        # recruiter2 has 1 job, recruiter1 has 4 jobs
        self.assertEqual(response.data["total_jobs"], 1)

    def test_30_recruiter_cannot_access_candidate_dashboard(self):
        """Test 30: Recruiter cannot access candidate dashboard"""
        self.authenticate(self.recruiter1)
        response = self.client.get("/api/analytics/candidate/dashboard/")
        self.assertEqual(response.status_code, 403)

    def test_31_candidate_cannot_access_job_analytics(self):
        """Test 31: Candidate cannot access job analytics"""
        self.authenticate(self.candidate1)
        response = self.client.get(f"/api/analytics/recruiter/jobs/{self.job1.id}/")
        self.assertEqual(response.status_code, 403)

    def test_32_candidate_cannot_access_top_candidates(self):
        """Test 32: Candidate cannot access top candidates"""
        self.authenticate(self.candidate1)
        response = self.client.get(
            f"/api/analytics/recruiter/jobs/{self.job1.id}/top-candidates/"
        )
        self.assertEqual(response.status_code, 403)

    def test_33_empty_data_returns_zero_not_null(self):
        """Test 33: Empty data returns 0 not null"""
        # Create new recruiter with no data
        new_recruiter = User.objects.create_user(
            email="emptyrecruiter@example.com",
            password="pass12345",
            full_name="Empty Recruiter",
            role=User.Roles.RECRUITER,
        )
        self.authenticate(new_recruiter)
        response = self.client.get("/api/analytics/recruiter/dashboard/")
        self.assertEqual(response.status_code, 200)
        # All counts should be 0, not null
        self.assertEqual(response.data["total_jobs"], 0)
        self.assertEqual(response.data["active_jobs"], 0)
        self.assertEqual(response.data["closed_jobs"], 0)
        self.assertEqual(response.data["total_applications"], 0)
        self.assertEqual(response.data["submitted_applications"], 0)
        self.assertEqual(response.data["under_review_applications"], 0)
        self.assertEqual(response.data["shortlisted_applications"], 0)
        self.assertEqual(response.data["rejected_applications"], 0)
        self.assertEqual(response.data["hired_applications"], 0)
        self.assertEqual(response.data["scheduled_interviews"], 0)
        self.assertEqual(response.data["completed_interviews"], 0)
        self.assertEqual(response.data["cancelled_interviews"], 0)

    def test_34_top_candidates_secondary_ordering(self):
        """Test 34: Top candidates secondary ordering by calculated_at"""
        # Create two candidates with same match score but different calculated_at
        candidate_a = User.objects.create_user(
            email="candidate_a@example.com",
            password="pass12345",
            full_name="Candidate A",
            role=User.Roles.CANDIDATE,
        )
        resume_container_a = Resume.objects.create(user=candidate_a)
        ResumeVersion.objects.create(
            resume=resume_container_a,
            original_filename="resume_a.pdf",
            stored_filename="resume_a_v1.pdf",
            file=SimpleUploadedFile("resume_a.pdf", b"fake pdf content"),
            file_size=100,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        match_a = JobMatch.objects.create(
            candidate=candidate_a,
            job=self.job1,
            match_score=90.0,
            skills_score=90.0,
            experience_score=90.0,
            education_score=90.0,
            matched_skills_count=9,
            total_required_skills=10,
        )
        # Update calculated_at to be older
        match_a.calculated_at = timezone.now() - timezone.timedelta(days=2)
        match_a.save()

        candidate_b = User.objects.create_user(
            email="candidate_b@example.com",
            password="pass12345",
            full_name="Candidate B",
            role=User.Roles.CANDIDATE,
        )
        resume_container_b = Resume.objects.create(user=candidate_b)
        ResumeVersion.objects.create(
            resume=resume_container_b,
            original_filename="resume_b.pdf",
            stored_filename="resume_b_v1.pdf",
            file=SimpleUploadedFile("resume_b.pdf", b"fake pdf content"),
            file_size=100,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        JobMatch.objects.create(
            candidate=candidate_b,
            job=self.job1,
            match_score=90.0,
            skills_score=90.0,
            experience_score=90.0,
            education_score=90.0,
            matched_skills_count=9,
            total_required_skills=10,
        )
        # match_b has newer calculated_at by default

        self.authenticate(self.recruiter1)
        response = self.client.get(
            f"/api/analytics/recruiter/jobs/{self.job1.id}/top-candidates/"
        )
        self.assertEqual(response.status_code, 200)

        # Find candidates with 90.0 score
        candidates_with_90 = [c for c in response.data if c["match_score"] == 90.0]
        self.assertEqual(len(candidates_with_90), 2)

        # candidate_b (newer calculated_at) should come before candidate_a (older)
        self.assertEqual(
            str(candidates_with_90[0]["candidate_id"]), str(candidate_b.id)
        )
        self.assertEqual(
            str(candidates_with_90[1]["candidate_id"]), str(candidate_a.id)
        )
