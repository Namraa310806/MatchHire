from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.jobs.models import Job
from apps.resumes.models import Resume, ResumeVersion
from .models import Application, ApplicationStatusHistory

User = get_user_model()


class ApplicationModelTests(TestCase):
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

    def test_13_status_default_submitted(self):
        """Test 13: Status default = SUBMITTED"""
        application = Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            resume_version=self.resume_version,
        )
        self.assertEqual(application.status, Application.ApplicationStatus.SUBMITTED)

    def test_14_unique_constraint_works(self):
        """Test 14: Unique constraint works"""
        Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            resume_version=self.resume_version,
        )
        with self.assertRaises(Exception):
            Application.objects.create(
                job=self.job,
                candidate=self.candidate,
                resume_version=self.resume_version,
            )


class ApplicationAPITests(TestCase):
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
        self.active_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Active Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.ACTIVE,
        )
        self.draft_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Draft Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.DRAFT,
        )
        self.closed_job = Job.objects.create(
            recruiter=self.recruiter1,
            title="Closed Job",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.CLOSED,
            closed_at=timezone.now(),
        )
        self.recruiter2_job = Job.objects.create(
            recruiter=self.recruiter2,
            title="Other Job",
            company_name="Other Corp",
            location="NY",
            description="Desc",
            status=Job.JobStatus.ACTIVE,
        )

        # Create resumes
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

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_1_candidate_applies_successfully(self):
        """Test 1: Candidate applies successfully"""
        self.authenticate(self.candidate1)
        data = {"resume_version_id": str(self.resume_version1.id)}
        response = self.client.post(
            f"/api/jobs/{self.active_job.id}/apply/", data, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Application.objects.count(), 1)
        self.assertEqual(
            response.data["status"], Application.ApplicationStatus.SUBMITTED
        )
        self.assertEqual(str(response.data["job_id"]), str(self.active_job.id))
        self.assertEqual(str(response.data["candidate_id"]), str(self.candidate1.id))

    def test_2_recruiter_cannot_apply(self):
        """Test 2: Recruiter cannot apply"""
        self.authenticate(self.recruiter1)
        data = {"resume_version_id": str(self.resume_version1.id)}
        response = self.client.post(
            f"/api/jobs/{self.active_job.id}/apply/", data, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_3_anonymous_blocked(self):
        """Test 3: Anonymous blocked"""
        data = {"resume_version_id": str(self.resume_version1.id)}
        response = self.client.post(
            f"/api/jobs/{self.active_job.id}/apply/", data, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_4_cannot_apply_to_draft_job(self):
        """Test 4: Cannot apply to draft job"""
        self.authenticate(self.candidate1)
        data = {"resume_version_id": str(self.resume_version1.id)}
        response = self.client.post(
            f"/api/jobs/{self.draft_job.id}/apply/", data, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Cannot apply to draft or closed jobs", response.data["detail"])

    def test_5_cannot_apply_to_closed_job(self):
        """Test 5: Cannot apply to closed job"""
        self.authenticate(self.candidate1)
        data = {"resume_version_id": str(self.resume_version1.id)}
        response = self.client.post(
            f"/api/jobs/{self.closed_job.id}/apply/", data, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Cannot apply to draft or closed jobs", response.data["detail"])

    def test_6_cannot_apply_twice(self):
        """Test 6: Cannot apply twice"""
        self.authenticate(self.candidate1)
        data = {"resume_version_id": str(self.resume_version1.id)}

        # First application
        response = self.client.post(
            f"/api/jobs/{self.active_job.id}/apply/", data, format="json"
        )
        self.assertEqual(response.status_code, 201)

        # Second application
        response = self.client.post(
            f"/api/jobs/{self.active_job.id}/apply/", data, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("already applied", response.data["detail"])

    def test_7_resume_version_ownership_enforced(self):
        """Test 7: Resume version ownership enforced"""
        self.authenticate(self.candidate1)
        # Try to apply with candidate2's resume version
        data = {"resume_version_id": str(self.resume_version2.id)}
        response = self.client.post(
            f"/api/jobs/{self.active_job.id}/apply/", data, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("does not belong to you", response.data["detail"])

    def test_8_candidate_lists_own_applications(self):
        """Test 8: Candidate lists own applications"""
        # Create applications for both candidates
        Application.objects.create(
            job=self.active_job,
            candidate=self.candidate1,
            resume_version=self.resume_version1,
        )
        Application.objects.create(
            job=self.active_job,
            candidate=self.candidate2,
            resume_version=self.resume_version2,
        )

        self.authenticate(self.candidate1)
        response = self.client.get("/api/applications/my/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["candidate_id"], str(self.candidate1.id))

    def test_9_candidate_cannot_see_another_candidate_application(self):
        """Test 9: Candidate cannot see another candidate application"""
        application = Application.objects.create(
            job=self.active_job,
            candidate=self.candidate2,
            resume_version=self.resume_version2,
        )

        self.authenticate(self.candidate1)
        response = self.client.get(f"/api/applications/{application.id}/")
        self.assertEqual(response.status_code, 404)

    def test_10_recruiter_sees_applications_for_own_job(self):
        """Test 10: Recruiter sees applications for own job"""
        Application.objects.create(
            job=self.active_job,
            candidate=self.candidate1,
            resume_version=self.resume_version1,
        )
        Application.objects.create(
            job=self.active_job,
            candidate=self.candidate2,
            resume_version=self.resume_version2,
        )

        self.authenticate(self.recruiter1)
        response = self.client.get(f"/api/jobs/{self.active_job.id}/applications/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_11_recruiter_cannot_see_applications_for_another_recruiter_job(self):
        """Test 11: Recruiter cannot see applications for another recruiter job"""
        Application.objects.create(
            job=self.recruiter2_job,
            candidate=self.candidate1,
            resume_version=self.resume_version1,
        )

        self.authenticate(self.recruiter1)
        response = self.client.get(f"/api/jobs/{self.recruiter2_job.id}/applications/")
        self.assertEqual(response.status_code, 404)

    def test_12_application_detail_works(self):
        """Test 12: Application detail works"""
        application = Application.objects.create(
            job=self.active_job,
            candidate=self.candidate1,
            resume_version=self.resume_version1,
        )

        # Candidate can view own application
        self.authenticate(self.candidate1)
        response = self.client.get(f"/api/applications/{application.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(application.id))

        # Recruiter can view application for own job
        self.authenticate(self.recruiter1)
        response = self.client.get(f"/api/applications/{application.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(application.id))

    def test_resume_version_id_required(self):
        """Test: resume_version_id is required"""
        self.authenticate(self.candidate1)
        data = {}
        response = self.client.post(
            f"/api/jobs/{self.active_job.id}/apply/", data, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("resume_version_id", response.data["detail"])

    def test_invalid_resume_version_id(self):
        """Test: Invalid resume_version_id returns error"""
        self.authenticate(self.candidate1)
        data = {"resume_version_id": "00000000-0000-0000-0000-000000000000"}
        response = self.client.post(
            f"/api/jobs/{self.active_job.id}/apply/", data, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Resume version not found", response.data["detail"])

    def test_15_query_optimization(self):
        """Test 15: Query optimization with select_related"""
        application = Application.objects.create(
            job=self.active_job,
            candidate=self.candidate1,
            resume_version=self.resume_version1,
        )

        self.authenticate(self.candidate1)
        with self.assertNumQueries(1):
            self.client.get("/api/applications/my/")

        self.authenticate(self.recruiter1)
        # JobApplicationsListView needs 2 queries: 1 to verify job ownership, 1 for applications
        with self.assertNumQueries(2):
            self.client.get(f"/api/jobs/{self.active_job.id}/applications/")

        self.authenticate(self.candidate1)
        with self.assertNumQueries(1):
            self.client.get(f"/api/applications/{application.id}/")

    def test_applications_ordered_newest_first(self):
        """Test: Applications are ordered newest first"""
        import time

        # Create applications with time delay
        app1 = Application.objects.create(
            job=self.active_job,
            candidate=self.candidate1,
            resume_version=self.resume_version1,
        )
        time.sleep(0.01)
        app2 = Application.objects.create(
            job=self.active_job,
            candidate=self.candidate2,
            resume_version=self.resume_version2,
        )

        self.authenticate(self.recruiter1)
        response = self.client.get(f"/api/jobs/{self.active_job.id}/applications/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["id"], str(app2.id))
        self.assertEqual(response.data[1]["id"], str(app1.id))

    def test_recruiter_cannot_list_my_applications(self):
        """Test: Recruiter cannot list my applications endpoint"""
        self.authenticate(self.recruiter1)
        response = self.client.get("/api/applications/my/")
        self.assertEqual(response.status_code, 403)

    def test_candidate_cannot_list_job_applications(self):
        """Test: Candidate cannot list job applications endpoint"""
        self.authenticate(self.candidate1)
        response = self.client.get(f"/api/jobs/{self.active_job.id}/applications/")
        self.assertEqual(response.status_code, 403)


class ApplicationWorkflowTests(TestCase):
    """Tests for recruiter review workflow - status updates, history, and filtering"""

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
            title="Job One",
            company_name="Tech Corp",
            location="SF",
            description="Desc",
            status=Job.JobStatus.ACTIVE,
        )
        self.job2 = Job.objects.create(
            recruiter=self.recruiter2,
            title="Job Two",
            company_name="Other Corp",
            location="NY",
            description="Desc",
            status=Job.JobStatus.ACTIVE,
        )

        # Create resumes
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

        # Create applications
        self.application1 = Application.objects.create(
            job=self.job1,
            candidate=self.candidate1,
            resume_version=self.resume_version1,
            status=Application.ApplicationStatus.SUBMITTED,
        )
        self.application2 = Application.objects.create(
            job=self.job1,
            candidate=self.candidate2,
            resume_version=self.resume_version2,
            status=Application.ApplicationStatus.SUBMITTED,
        )
        self.application3 = Application.objects.create(
            job=self.job2,
            candidate=self.candidate1,
            resume_version=self.resume_version1,
            status=Application.ApplicationStatus.SUBMITTED,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    # Status Update Tests

    def test_status_update_submitted_to_under_review(self):
        """Test: Recruiter moves SUBMITTED → UNDER_REVIEW"""
        self.authenticate(self.recruiter1)
        data = {"status": "under_review"}
        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/", data, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "under_review")
        self.application1.refresh_from_db()
        self.assertEqual(
            self.application1.status, Application.ApplicationStatus.UNDER_REVIEW
        )

    def test_status_update_under_review_to_shortlisted(self):
        """Test: Recruiter moves UNDER_REVIEW → SHORTLISTED"""
        self.application1.status = Application.ApplicationStatus.UNDER_REVIEW
        self.application1.save()

        self.authenticate(self.recruiter1)
        data = {"status": "shortlisted"}
        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/", data, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "shortlisted")
        self.application1.refresh_from_db()
        self.assertEqual(
            self.application1.status, Application.ApplicationStatus.SHORTLISTED
        )

    def test_status_update_under_review_to_rejected(self):
        """Test: Recruiter moves UNDER_REVIEW → REJECTED"""
        self.application1.status = Application.ApplicationStatus.UNDER_REVIEW
        self.application1.save()

        self.authenticate(self.recruiter1)
        data = {"status": "rejected"}
        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/", data, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "rejected")
        self.application1.refresh_from_db()
        self.assertEqual(
            self.application1.status, Application.ApplicationStatus.REJECTED
        )

    def test_status_update_shortlisted_to_hired(self):
        """Test: Recruiter moves SHORTLISTED → HIRED"""
        self.application1.status = Application.ApplicationStatus.SHORTLISTED
        self.application1.save()

        self.authenticate(self.recruiter1)
        data = {"status": "hired"}
        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/", data, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "hired")
        self.application1.refresh_from_db()
        self.assertEqual(self.application1.status, Application.ApplicationStatus.HIRED)

    def test_status_update_shortlisted_to_rejected(self):
        """Test: Recruiter moves SHORTLISTED → REJECTED"""
        self.application1.status = Application.ApplicationStatus.SHORTLISTED
        self.application1.save()

        self.authenticate(self.recruiter1)
        data = {"status": "rejected"}
        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/", data, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "rejected")
        self.application1.refresh_from_db()
        self.assertEqual(
            self.application1.status, Application.ApplicationStatus.REJECTED
        )

    def test_status_update_invalid_transition(self):
        """Test: Invalid transition rejected (SUBMITTED → HIRED)"""
        self.authenticate(self.recruiter1)
        data = {"status": "hired"}
        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/", data, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid status transition", str(response.data))

    def test_status_update_submitted_to_rejected_invalid(self):
        """Test: Invalid transition SUBMITTED → REJECTED"""
        self.authenticate(self.recruiter1)
        data = {"status": "rejected"}
        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/", data, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid status transition", str(response.data))

    def test_status_update_hired_cannot_change(self):
        """Test: HIRED status cannot be changed"""
        self.application1.status = Application.ApplicationStatus.HIRED
        self.application1.save()

        self.authenticate(self.recruiter1)
        data = {"status": "rejected"}
        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/", data, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid status transition", str(response.data))

    def test_status_update_rejected_cannot_change(self):
        """Test: REJECTED status cannot be changed"""
        self.application1.status = Application.ApplicationStatus.REJECTED
        self.application1.save()

        self.authenticate(self.recruiter1)
        data = {"status": "under_review"}
        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/", data, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid status transition", str(response.data))

    # Permission Tests

    def test_candidate_cannot_update_status(self):
        """Test: Candidate cannot update status"""
        self.authenticate(self.candidate1)
        data = {"status": "under_review"}
        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/", data, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_update_status(self):
        """Test: Anonymous blocked from status update"""
        data = {"status": "under_review"}
        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/", data, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_recruiter_cannot_update_another_recruiter_application(self):
        """Test: Recruiter cannot update another recruiter's application"""
        self.authenticate(self.recruiter2)
        data = {"status": "under_review"}
        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/", data, format="json"
        )
        self.assertEqual(response.status_code, 404)

    # History Tests

    def test_history_row_created_on_status_change(self):
        """Test: History row created when status changes"""
        self.authenticate(self.recruiter1)
        data = {"status": "under_review"}
        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/", data, format="json"
        )
        self.assertEqual(response.status_code, 200)

        # Check history was created
        history_count = ApplicationStatusHistory.objects.filter(
            application=self.application1
        ).count()
        self.assertEqual(history_count, 1)

        history = ApplicationStatusHistory.objects.get(application=self.application1)
        self.assertEqual(history.old_status, "submitted")
        self.assertEqual(history.new_status, "under_review")
        self.assertEqual(history.changed_by, self.recruiter1)

    def test_candidate_can_view_own_history(self):
        """Test: Candidate can view own application history"""
        # Create some history
        ApplicationStatusHistory.objects.create(
            application=self.application1,
            old_status="submitted",
            new_status="under_review",
            changed_by=self.recruiter1,
        )

        self.authenticate(self.candidate1)
        response = self.client.get(f"/api/applications/{self.application1.id}/history/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["old_status"], "submitted")
        self.assertEqual(response.data[0]["new_status"], "under_review")
        self.assertEqual(response.data[0]["changed_by"], "recruiter1@example.com")

    def test_candidate_cannot_view_another_candidate_history(self):
        """Test: Candidate cannot view another candidate's history"""
        self.authenticate(self.candidate1)
        response = self.client.get(f"/api/applications/{self.application2.id}/history/")
        self.assertEqual(response.status_code, 404)

    def test_recruiter_can_view_owned_application_history(self):
        """Test: Recruiter can view history of applications for their jobs"""
        # Create some history
        ApplicationStatusHistory.objects.create(
            application=self.application1,
            old_status="submitted",
            new_status="under_review",
            changed_by=self.recruiter1,
        )

        self.authenticate(self.recruiter1)
        response = self.client.get(f"/api/applications/{self.application1.id}/history/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_recruiter_cannot_view_another_recruiter_history(self):
        """Test: Recruiter cannot view history of another recruiter's application"""
        self.authenticate(self.recruiter1)
        response = self.client.get(f"/api/applications/{self.application3.id}/history/")
        self.assertEqual(response.status_code, 404)

    def test_anonymous_cannot_view_history(self):
        """Test: Anonymous cannot view history"""
        response = self.client.get(f"/api/applications/{self.application1.id}/history/")
        self.assertEqual(response.status_code, 401)

    # Filtering Tests

    def test_filter_submitted_applications(self):
        """Test: Filter submitted applications"""
        self.application2.status = Application.ApplicationStatus.UNDER_REVIEW
        self.application2.save()

        self.authenticate(self.recruiter1)
        response = self.client.get(
            f"/api/jobs/{self.job1.id}/applications/?status=submitted"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.application1.id))

    def test_filter_under_review_applications(self):
        """Test: Filter under_review applications"""
        self.application1.status = Application.ApplicationStatus.UNDER_REVIEW
        self.application1.save()
        self.application2.status = Application.ApplicationStatus.SHORTLISTED
        self.application2.save()

        self.authenticate(self.recruiter1)
        response = self.client.get(
            f"/api/jobs/{self.job1.id}/applications/?status=under_review"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.application1.id))

    def test_filter_shortlisted_applications(self):
        """Test: Filter shortlisted applications"""
        self.application1.status = Application.ApplicationStatus.SHORTLISTED
        self.application1.save()
        self.application2.status = Application.ApplicationStatus.UNDER_REVIEW
        self.application2.save()

        self.authenticate(self.recruiter1)
        response = self.client.get(
            f"/api/jobs/{self.job1.id}/applications/?status=shortlisted"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.application1.id))

    def test_filter_rejected_applications(self):
        """Test: Filter rejected applications"""
        self.application1.status = Application.ApplicationStatus.REJECTED
        self.application1.save()
        self.application2.status = Application.ApplicationStatus.UNDER_REVIEW
        self.application2.save()

        self.authenticate(self.recruiter1)
        response = self.client.get(
            f"/api/jobs/{self.job1.id}/applications/?status=rejected"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.application1.id))

    def test_filter_hired_applications(self):
        """Test: Filter hired applications"""
        self.application1.status = Application.ApplicationStatus.HIRED
        self.application1.save()
        self.application2.status = Application.ApplicationStatus.SHORTLISTED
        self.application2.save()

        self.authenticate(self.recruiter1)
        response = self.client.get(
            f"/api/jobs/{self.job1.id}/applications/?status=hired"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.application1.id))

    def test_invalid_status_filter_returns_400(self):
        """Test: Invalid status filter returns 400"""
        self.authenticate(self.recruiter1)
        response = self.client.get(
            f"/api/jobs/{self.job1.id}/applications/?status=invalid_status"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid status", response.data["detail"])

    def test_no_filter_returns_all_applications(self):
        """Test: No status filter returns all applications"""
        self.authenticate(self.recruiter1)
        response = self.client.get(f"/api/jobs/{self.job1.id}/applications/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    # Query Optimization Tests

    def test_applications_list_query_optimization(self):
        """Test: Applications list query count optimized with select_related"""
        self.authenticate(self.recruiter1)
        # Should be 2 queries: 1 for job ownership check, 1 for applications with select_related
        with self.assertNumQueries(2):
            self.client.get(f"/api/jobs/{self.job1.id}/applications/")

    def test_applications_list_with_filter_query_optimization(self):
        """Test: Applications list with filter query count optimized"""
        self.authenticate(self.recruiter1)
        # Should be 2 queries: 1 for job ownership check, 1 for filtered applications
        with self.assertNumQueries(2):
            self.client.get(f"/api/jobs/{self.job1.id}/applications/?status=submitted")

    def test_history_endpoint_query_optimization(self):
        """Test: History endpoint query count optimized"""
        # Create some history
        ApplicationStatusHistory.objects.create(
            application=self.application1,
            old_status="submitted",
            new_status="under_review",
            changed_by=self.recruiter1,
        )

        self.authenticate(self.recruiter1)
        # Should be 3 queries: 1 for application with select_related, 1 for history with select_related, 1 for auth
        with self.assertNumQueries(3):
            self.client.get(f"/api/applications/{self.application1.id}/history/")

    def test_status_update_query_optimization(self):
        """Test: Status update query count optimized"""
        self.authenticate(self.recruiter1)
        data = {"status": "under_review"}
        # Should be optimized queries
        with self.assertNumQueries(
            4
        ):  # get application, validate, update, create history; notification is async
            self.client.patch(
                f"/api/applications/{self.application1.id}/status/", data, format="json"
            )
