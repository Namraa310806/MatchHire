from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Job

User = get_user_model()


class JobModelTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="pass12345",
            full_name="Recruiter One",
            role=User.Roles.RECRUITER,
        )

    def test_job_creation_defaults(self):
        job = Job.objects.create(
            recruiter=self.recruiter,
            title="Software Engineer",
            company_name="Tech Corp",
            location="San Francisco",
            description="We need a software engineer",
        )
        self.assertEqual(job.status, Job.JobStatus.DRAFT)
        self.assertEqual(job.employment_type, Job.EmploymentType.FULL_TIME)
        self.assertEqual(job.experience_level, Job.ExperienceLevel.MID)
        self.assertIsNone(job.closed_at)

    def test_salary_validation_in_model_clean(self):
        job = Job(
            recruiter=self.recruiter,
            title="Software Engineer",
            company_name="Tech Corp",
            location="San Francisco",
            description="We need a software engineer",
            salary_min=100000,
            salary_max=50000,
        )
        with self.assertRaises(Exception):
            job.full_clean()


class JobAPITests(TestCase):
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
        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            password="pass12345",
            full_name="Candidate One",
            role=User.Roles.CANDIDATE,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_1_recruiter_creates_job(self):
        """Test 1: Recruiter creates job"""
        self.authenticate(self.recruiter1)
        data = {
            "title": "Software Engineer",
            "company_name": "Tech Corp",
            "location": "San Francisco",
            "employment_type": Job.EmploymentType.FULL_TIME,
            "experience_level": Job.ExperienceLevel.SENIOR,
            "description": "We need a senior software engineer",
            "requirements": "Python, Django",
            "responsibilities": "Build APIs",
            "salary_min": 100000,
            "salary_max": 150000,
            "currency": "USD",
            "is_remote": True,
            "status": Job.JobStatus.ACTIVE,
        }
        response = self.client.post("/api/jobs/create/", data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "Software Engineer")
        self.assertEqual(response.data["recruiter_email"], self.recruiter1.email)
        self.assertEqual(Job.objects.count(), 1)

    def test_2_candidate_cannot_create_job(self):
        """Test 2: Candidate cannot create job"""
        self.authenticate(self.candidate)
        data = {
            "title": "Software Engineer",
            "company_name": "Tech Corp",
            "location": "San Francisco",
            "description": "We need a software engineer",
        }
        response = self.client.post("/api/jobs/create/", data, format="json")
        self.assertEqual(response.status_code, 403)

    def test_3_anonymous_blocked(self):
        """Test 3: Anonymous blocked"""
        data = {
            "title": "Software Engineer",
            "company_name": "Tech Corp",
            "location": "San Francisco",
            "description": "We need a software engineer",
        }
        response = self.client.post("/api/jobs/create/", data, format="json")
        self.assertEqual(response.status_code, 401)

    def test_4_recruiter_lists_own_jobs(self):
        """Test 4: Recruiter lists own jobs"""
        self.authenticate(self.recruiter1)
        Job.objects.create(
            recruiter=self.recruiter1,
            title="Job 1",
            company_name="Tech Corp",
            location="SF",
            description="Desc 1",
            status=Job.JobStatus.ACTIVE,
        )
        Job.objects.create(
            recruiter=self.recruiter1,
            title="Job 2",
            company_name="Tech Corp",
            location="SF",
            description="Desc 2",
            status=Job.JobStatus.DRAFT,
        )
        Job.objects.create(
            recruiter=self.recruiter2,
            title="Job 3",
            company_name="Other Corp",
            location="NY",
            description="Desc 3",
            status=Job.JobStatus.ACTIVE,
        )

        response = self.client.get("/api/jobs/my/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        job_ids = [job["id"] for job in response.data]
        self.assertEqual(
            Job.objects.filter(id__in=job_ids, recruiter=self.recruiter1).count(), 2
        )

    def test_5_recruiter_cannot_view_another_recruiters_draft_job(self):
        """Test 5: Recruiter cannot view another recruiter's draft job"""
        job = Job.objects.create(
            recruiter=self.recruiter2,
            title="Secret Job",
            company_name="Other Corp",
            location="NY",
            description="Secret",
            status=Job.JobStatus.DRAFT,
        )

        self.authenticate(self.recruiter1)
        response = self.client.get(f"/api/jobs/{job.id}/")
        self.assertEqual(response.status_code, 404)

    def test_6_recruiter_updates_own_job(self):
        """Test 6: Recruiter updates own job"""
        job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Old Title",
            company_name="Tech Corp",
            location="SF",
            description="Old description",
            status=Job.JobStatus.DRAFT,
        )

        self.authenticate(self.recruiter1)
        data = {"title": "New Title", "description": "New description"}
        response = self.client.patch(f"/api/jobs/{job.id}/", data, format="json")
        self.assertEqual(response.status_code, 200)
        job.refresh_from_db()
        self.assertEqual(job.title, "New Title")
        self.assertEqual(job.description, "New description")

    def test_7_recruiter_cannot_update_another_recruiters_job(self):
        """Test 7: Recruiter cannot update another recruiter's job"""
        job = Job.objects.create(
            recruiter=self.recruiter2,
            title="Job",
            company_name="Other Corp",
            location="NY",
            description="Desc",
            status=Job.JobStatus.ACTIVE,
        )

        self.authenticate(self.recruiter1)
        data = {"title": "Hacked Title"}
        response = self.client.patch(f"/api/jobs/{job.id}/", data, format="json")
        self.assertEqual(response.status_code, 404)
        job.refresh_from_db()
        self.assertEqual(job.title, "Job")

    def test_8_close_job_works(self):
        """Test 8: Close job works"""
        job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.ACTIVE,
        )
        self.assertIsNone(job.closed_at)

        self.authenticate(self.recruiter1)
        response = self.client.post(f"/api/jobs/{job.id}/close/")
        self.assertEqual(response.status_code, 200)
        job.refresh_from_db()
        self.assertEqual(job.status, Job.JobStatus.CLOSED)
        self.assertIsNotNone(job.closed_at)

    def test_9_closed_job_disappears_from_candidate_listing(self):
        """Test 9: Closed job disappears from candidate listing"""
        active_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Active Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.ACTIVE,
        )
        closed_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Closed Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.CLOSED,
            closed_at=timezone.now(),
        )

        self.authenticate(self.candidate)
        response = self.client.get("/api/jobs/")
        self.assertEqual(response.status_code, 200)
        job_ids = [job["id"] for job in response.data]
        self.assertIn(str(active_job.id), job_ids)
        self.assertNotIn(str(closed_job.id), job_ids)

    def test_10_draft_job_hidden_from_candidates(self):
        """Test 10: Draft job hidden from candidates"""
        draft_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Draft Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.DRAFT,
        )
        active_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Active Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.ACTIVE,
        )

        self.authenticate(self.candidate)
        response = self.client.get("/api/jobs/")
        self.assertEqual(response.status_code, 200)
        job_ids = [job["id"] for job in response.data]
        self.assertNotIn(str(draft_job.id), job_ids)
        self.assertIn(str(active_job.id), job_ids)

    def test_11_active_job_visible_to_candidates(self):
        """Test 11: Active job visible to candidates"""
        active_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Active Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.ACTIVE,
        )

        self.authenticate(self.candidate)
        response = self.client.get("/api/jobs/")
        self.assertEqual(response.status_code, 200)
        job_ids = [job["id"] for job in response.data]
        self.assertIn(str(active_job.id), job_ids)

    def test_12_salary_validation(self):
        """Test 12: Salary validation"""
        self.authenticate(self.recruiter1)
        data = {
            "title": "Software Engineer",
            "company_name": "Tech Corp",
            "location": "SF",
            "description": "Desc",
            "salary_min": 150000,
            "salary_max": 100000,
        }
        response = self.client.post("/api/jobs/create/", data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("salary_min", response.data)

    def test_13_query_optimization(self):
        """Test 13: Query optimization with select_related"""
        Job.objects.create(
            recruiter=self.recruiter1,
            title="Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.ACTIVE,
        )

        self.authenticate(self.recruiter1)
        with self.assertNumQueries(1):
            self.client.get("/api/jobs/my/")

        self.authenticate(self.candidate)
        with self.assertNumQueries(1):
            self.client.get("/api/jobs/")

    def test_title_required_validation(self):
        """Test title is required"""
        self.authenticate(self.recruiter1)
        data = {
            "title": "",
            "company_name": "Tech Corp",
            "location": "SF",
            "description": "Desc",
        }
        response = self.client.post("/api/jobs/create/", data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.data)

    def test_description_required_validation(self):
        """Test description is required"""
        self.authenticate(self.recruiter1)
        data = {
            "title": "Job",
            "company_name": "Tech Corp",
            "location": "SF",
            "description": "",
        }
        response = self.client.post("/api/jobs/create/", data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("description", response.data)

    def test_close_already_closed_job(self):
        """Test closing an already closed job returns error"""
        job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.CLOSED,
            closed_at=timezone.now(),
        )

        self.authenticate(self.recruiter1)
        response = self.client.post(f"/api/jobs/{job.id}/close/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "Job is already closed.")

    def test_candidate_can_retrieve_active_job(self):
        """Test: Candidate can retrieve active job"""
        active_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Active Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.ACTIVE,
        )

        self.authenticate(self.candidate)
        response = self.client.get(f"/api/jobs/{active_job.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(active_job.id))

    def test_candidate_cannot_retrieve_draft_job(self):
        """Test: Candidate cannot retrieve draft job"""
        draft_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Draft Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.DRAFT,
        )

        self.authenticate(self.candidate)
        response = self.client.get(f"/api/jobs/{draft_job.id}/")
        self.assertEqual(response.status_code, 404)

    def test_candidate_cannot_retrieve_closed_job(self):
        """Test: Candidate cannot retrieve closed job"""
        closed_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Closed Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.CLOSED,
            closed_at=timezone.now(),
        )

        self.authenticate(self.candidate)
        response = self.client.get(f"/api/jobs/{closed_job.id}/")
        self.assertEqual(response.status_code, 404)

    def test_recruiter_owner_can_retrieve_draft_job(self):
        """Test: Recruiter owner can retrieve draft job"""
        draft_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Draft Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.DRAFT,
        )

        self.authenticate(self.recruiter1)
        response = self.client.get(f"/api/jobs/{draft_job.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(draft_job.id))

    def test_recruiter_owner_can_retrieve_closed_job(self):
        """Test: Recruiter owner can retrieve closed job"""
        closed_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Closed Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.CLOSED,
            closed_at=timezone.now(),
        )

        self.authenticate(self.recruiter1)
        response = self.client.get(f"/api/jobs/{closed_job.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(closed_job.id))

    def test_other_recruiter_can_retrieve_active_job(self):
        """Test: Other recruiter can retrieve active job"""
        active_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Active Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.ACTIVE,
        )

        self.authenticate(self.recruiter2)
        response = self.client.get(f"/api/jobs/{active_job.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(active_job.id))

    def test_other_recruiter_cannot_retrieve_draft_job(self):
        """Test: Other recruiter cannot retrieve draft job"""
        draft_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Draft Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.DRAFT,
        )

        self.authenticate(self.recruiter2)
        response = self.client.get(f"/api/jobs/{draft_job.id}/")
        self.assertEqual(response.status_code, 404)

    def test_other_recruiter_cannot_retrieve_closed_job(self):
        """Test: Other recruiter cannot retrieve closed job"""
        closed_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Closed Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.CLOSED,
            closed_at=timezone.now(),
        )

        self.authenticate(self.recruiter2)
        response = self.client.get(f"/api/jobs/{closed_job.id}/")
        self.assertEqual(response.status_code, 404)

    def test_candidate_cannot_patch_job(self):
        """Test: Candidate cannot patch job"""
        active_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Active Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.ACTIVE,
        )

        self.authenticate(self.candidate)
        response = self.client.patch(f"/api/jobs/{active_job.id}/", {"title": "Hacked"}, format="json")
        self.assertEqual(response.status_code, 403)
        active_job.refresh_from_db()
        self.assertEqual(active_job.title, "Active Job")
