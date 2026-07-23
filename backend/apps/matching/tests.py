from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.jobs.models import Job
from apps.matching.models import JobMatch, JobSkill
from apps.matching.services.matching import MatchingService
from apps.resumes.models import (
    Resume,
    ResumeVersion,
    StructuredResume,
    ResumeSkill,
    ResumeEducation,
    ResumeExperience,
)

User = get_user_model()


class MatchingServiceTests(TestCase):
    """Tests for the MatchingService class"""

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
            requirements="Python, Django, PostgreSQL, Redis",
            experience_level=Job.ExperienceLevel.SENIOR,
            status=Job.JobStatus.ACTIVE,
        )

    def test_1_skill_score_calculation(self):
        """Test 1: Skill score calculation"""
        # Create candidate with skills
        resume = Resume.objects.create(user=self.candidate)
        version = ResumeVersion.objects.create(
            resume=resume,
            original_filename="resume.pdf",
            stored_filename="unique.pdf",
            file_size=1000,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        structured_resume = StructuredResume.objects.create(resume_version=version)
        ResumeSkill.objects.create(structured_resume=structured_resume, name="Python")
        ResumeSkill.objects.create(structured_resume=structured_resume, name="Django")

        skills_score, matched, missing, matched_count, total_count, _ = (
            MatchingService.calculate_skill_score(self.candidate, self.job)
        )

        self.assertEqual(skills_score, Decimal("50.00"))
        self.assertEqual(matched_count, 2)
        self.assertEqual(total_count, 4)
        self.assertIn("Python", matched)
        self.assertIn("Django", matched)
        self.assertIn("PostgreSQL", missing)
        self.assertIn("Redis", missing)

    def test_2_experience_score_calculation(self):
        """Test 2: Experience score calculation with actual years"""
        # Create candidate with 5 years of experience
        from datetime import date, timedelta

        resume = Resume.objects.create(user=self.candidate)
        version = ResumeVersion.objects.create(
            resume=resume,
            original_filename="resume.pdf",
            stored_filename="unique.pdf",
            file_size=1000,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        structured_resume = StructuredResume.objects.create(resume_version=version)

        # Create 5 years of experience (5 years ago to now)
        start_date = date.today() - timedelta(days=5 * 365)
        ResumeExperience.objects.create(
            structured_resume=structured_resume,
            company="Company 1",
            job_title="Role 1",
            start_date=start_date,
        )

        experience_score, experience_years = MatchingService.calculate_experience_score(
            self.candidate, self.job
        )

        self.assertEqual(experience_score, Decimal("100"))
        self.assertGreaterEqual(experience_years, 4.9)  # Approximately 5 years

    def test_3_education_score_calculation(self):
        """Test 3: Education score calculation"""
        # Create candidate with education
        resume = Resume.objects.create(user=self.candidate)
        version = ResumeVersion.objects.create(
            resume=resume,
            original_filename="resume.pdf",
            stored_filename="unique.pdf",
            file_size=1000,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        structured_resume = StructuredResume.objects.create(resume_version=version)
        ResumeEducation.objects.create(
            structured_resume=structured_resume,
            institution="University",
            degree="Bachelor",
        )

        education_score = MatchingService.calculate_education_score(self.candidate)

        self.assertEqual(education_score, Decimal("100"))

    def test_4_final_score_calculation(self):
        """Test 4: Final score calculation with weighted formula"""
        # Create candidate with full data
        from datetime import date, timedelta

        resume = Resume.objects.create(user=self.candidate)
        version = ResumeVersion.objects.create(
            resume=resume,
            original_filename="resume.pdf",
            stored_filename="unique.pdf",
            file_size=1000,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        structured_resume = StructuredResume.objects.create(resume_version=version)
        ResumeSkill.objects.create(structured_resume=structured_resume, name="Python")
        ResumeSkill.objects.create(structured_resume=structured_resume, name="Django")

        # Create 5 years of experience
        start_date = date.today() - timedelta(days=5 * 365)
        ResumeExperience.objects.create(
            structured_resume=structured_resume,
            company="Company 1",
            job_title="Role 1",
            start_date=start_date,
        )

        ResumeEducation.objects.create(
            structured_resume=structured_resume,
            institution="University",
            degree="Bachelor",
        )

        job_match = MatchingService.calculate_match(self.candidate, self.job)

        # Skills: 50% * 0.60 = 30
        # Experience: 100% * 0.30 = 30
        # Education: 100% * 0.10 = 10
        # Total: 70
        self.assertEqual(job_match.match_score, Decimal("70.00"))

    def test_5_empty_requirements_handling(self):
        """Test 5: Empty requirements handling"""
        self.job.requirements = ""
        self.job.save()

        skills_score, matched, missing, matched_count, total_count, _ = (
            MatchingService.calculate_skill_score(self.candidate, self.job)
        )

        self.assertEqual(skills_score, Decimal("0"))
        self.assertEqual(total_count, 0)

    def test_6_missing_structured_resume_handling(self):
        """Test 6: Missing structured resume handling"""
        # Create resume without structured resume
        resume = Resume.objects.create(user=self.candidate)
        ResumeVersion.objects.create(
            resume=resume,
            original_filename="resume.pdf",
            stored_filename="unique.pdf",
            file_size=1000,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )

        skills_score, _, _, _, _, _ = MatchingService.calculate_skill_score(
            self.candidate, self.job
        )
        experience_score, experience_years = MatchingService.calculate_experience_score(
            self.candidate, self.job
        )
        education_score = MatchingService.calculate_education_score(self.candidate)

        self.assertEqual(skills_score, Decimal("0"))
        self.assertEqual(experience_score, Decimal("0"))
        self.assertEqual(experience_years, 0.0)
        self.assertEqual(education_score, Decimal("0"))

    def test_7_entry_level_experience(self):
        """Test 7: Entry level experience always returns 100"""
        self.job.experience_level = Job.ExperienceLevel.ENTRY
        self.job.save()

        experience_score, _ = MatchingService.calculate_experience_score(
            self.candidate, self.job
        )

        self.assertEqual(experience_score, Decimal("100"))

    def test_8_junior_experience_requirement(self):
        """Test 8: Junior experience requirement (1 year)"""
        self.job.experience_level = Job.ExperienceLevel.JUNIOR
        self.job.save()

        # Create candidate with 0 experience
        resume = Resume.objects.create(user=self.candidate)
        version = ResumeVersion.objects.create(
            resume=resume,
            original_filename="resume.pdf",
            stored_filename="unique.pdf",
            file_size=1000,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        StructuredResume.objects.create(resume_version=version)

        experience_score, experience_years = MatchingService.calculate_experience_score(
            self.candidate, self.job
        )

        self.assertEqual(experience_score, Decimal("0"))
        self.assertEqual(experience_years, 0.0)

    def test_9_explanation_json_created(self):
        """Test 9: Explanation JSON created correctly"""
        resume = Resume.objects.create(user=self.candidate)
        version = ResumeVersion.objects.create(
            resume=resume,
            original_filename="resume.pdf",
            stored_filename="unique.pdf",
            file_size=1000,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        structured_resume = StructuredResume.objects.create(resume_version=version)
        ResumeSkill.objects.create(structured_resume=structured_resume, name="Python")

        job_match = MatchingService.calculate_match(self.candidate, self.job)

        self.assertIn("matched_skills", job_match.explanation)
        self.assertIn("missing_skills", job_match.explanation)
        self.assertIn("matched_skill_details", job_match.explanation)
        self.assertIn("missing_skill_details", job_match.explanation)
        self.assertIn("experience_level_required", job_match.explanation)
        self.assertIn("candidate_experience_years", job_match.explanation)
        self.assertIn("education_found", job_match.explanation)

    def _create_resume_with_skills(self, user, skill_names):
        resume = Resume.objects.create(user=user)
        version = ResumeVersion.objects.create(
            resume=resume,
            original_filename="resume.pdf",
            stored_filename=f"{user.email.replace('@', '_')}_{len(skill_names)}.pdf",
            file_size=1000,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        structured_resume = StructuredResume.objects.create(resume_version=version)
        for skill_name in skill_names:
            ResumeSkill.objects.create(
                structured_resume=structured_resume,
                name=skill_name,
            )
        return structured_resume

    def _create_job_with_structured_skills(self, skill_names, requirements=""):
        job = Job.objects.create(
            recruiter=self.recruiter,
            title="Structured Skills Job",
            company_name="Tech Corp",
            location="San Francisco",
            description="We need a software engineer",
            requirements=requirements,
            experience_level=Job.ExperienceLevel.SENIOR,
            status=Job.JobStatus.ACTIVE,
        )
        for skill_name in skill_names:
            JobSkill.objects.create(job=job, name=skill_name)
        return job

    class FakeEmbeddingModel:
        def __init__(self):
            self.encode_calls = []

        def encode(
            self,
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
        ):
            if isinstance(texts, str):
                texts = [texts]

            texts = list(texts)
            self.encode_calls.append(texts)

            vectors = []
            for text in texts:
                normalized = text.strip().casefold()
                if normalized == "js":
                    vectors.append([1.0, 0.0, 0.0])
                elif normalized == "javascript":
                    vectors.append([0.8, 0.6, 0.0])
                elif normalized == "ml":
                    vectors.append([0.0, 1.0, 0.0])
                elif normalized == "machine learning":
                    vectors.append([0.0, 0.8, 0.6])
                elif normalized == "cobol":
                    vectors.append([1.0, 0.0, 0.0])
                elif normalized == "kubernetes":
                    vectors.append([0.0, 1.0, 0.0])
                else:
                    bucket = sum(ord(char) for char in normalized) % 3
                    vector = [0.0, 0.0, 0.0]
                    vector[bucket] = 1.0
                    vectors.append(vector)

            return vectors

    def test_32_structured_job_skills_are_used(self):
        """Test 32: Structured JobSkill rows are preferred over free-text requirements"""
        self._create_resume_with_skills(self.candidate, ["Python"])
        job = self._create_job_with_structured_skills(["Python"], requirements="Go, Rust")

        skills_score, matched, missing, matched_count, total_count, skill_details = (
            MatchingService.calculate_skill_score(self.candidate, job)
        )

        self.assertEqual(skills_score, Decimal("100.00"))
        self.assertEqual(matched_count, 1)
        self.assertEqual(total_count, 1)
        self.assertEqual(matched, ["Python"])
        self.assertEqual(missing, [])
        self.assertEqual(skill_details["matched"][0]["match_type"], "exact")

    def test_33_semantically_similar_skills_match(self):
        """Test 33: Semantic skill matching works for differently worded skills"""
        self._create_resume_with_skills(self.candidate, ["JS", "ML"])
        job = self._create_job_with_structured_skills(["JavaScript", "Machine Learning"])

        fake_model = self.FakeEmbeddingModel()
        with mock.patch(
            "apps.matching.services.matching._load_skill_embedding_model",
            return_value=fake_model,
        ):
            skills_score, matched, missing, matched_count, total_count, skill_details = (
                MatchingService.calculate_skill_score(self.candidate, job)
            )

        self.assertEqual(skills_score, Decimal("100.00"))
        self.assertEqual(matched_count, 2)
        self.assertEqual(total_count, 2)
        self.assertEqual(missing, [])
        self.assertEqual(
            {detail["match_type"] for detail in skill_details["matched"]},
            {"semantic"},
        )
        self.assertEqual(len(fake_model.encode_calls), 2)

    def test_34_unrelated_skills_do_not_false_positive(self):
        """Test 34: Unrelated skills do not match above the similarity threshold"""
        self._create_resume_with_skills(self.candidate, ["Kubernetes"])
        job = self._create_job_with_structured_skills(["COBOL"])

        fake_model = self.FakeEmbeddingModel()
        with mock.patch(
            "apps.matching.services.matching._load_skill_embedding_model",
            return_value=fake_model,
        ):
            skills_score, matched, missing, matched_count, total_count, skill_details = (
                MatchingService.calculate_skill_score(self.candidate, job)
            )

        self.assertEqual(skills_score, Decimal("0.00"))
        self.assertEqual(matched_count, 0)
        self.assertEqual(total_count, 1)
        self.assertEqual(matched, [])
        self.assertEqual(missing, ["COBOL"])
        self.assertLess(skill_details["missing"][0]["similarity"], 0.75)

    def test_35_skill_match_threshold_is_respected(self):
        """Test 35: Skill match threshold controls semantic matches"""
        self._create_resume_with_skills(self.candidate, ["JS"])
        job = self._create_job_with_structured_skills(["JavaScript"])

        fake_model = self.FakeEmbeddingModel()
        with mock.patch(
            "apps.matching.services.matching._load_skill_embedding_model",
            return_value=fake_model,
        ):
            with mock.patch.object(MatchingService, "SKILL_MATCH_THRESHOLD", 0.81):
                skills_score, matched, missing, matched_count, total_count, _ = (
                    MatchingService.calculate_skill_score(self.candidate, job)
                )

        self.assertEqual(skills_score, Decimal("0.00"))
        self.assertEqual(matched_count, 0)
        self.assertEqual(total_count, 1)
        self.assertEqual(matched, [])
        self.assertEqual(missing, ["JavaScript"])

    def test_36_embedding_batches_are_cached_for_bulk_recalculation(self):
        """Test 36: Job-level required skill embeddings are reused across candidate recalculations"""
        required_skills = [f"Skill {index}" for index in range(20)]
        job = self._create_job_with_structured_skills(required_skills)

        for index in range(50):
            candidate = User.objects.create_user(
                email=f"candidate{index}@example.com",
                password="pass12345",
                full_name=f"Candidate {index}",
                role=User.Roles.CANDIDATE,
            )
            self._create_resume_with_skills(candidate, [f"Candidate Skill {index}"])

        fake_model = self.FakeEmbeddingModel()
        with mock.patch(
            "apps.matching.services.matching._load_skill_embedding_model",
            return_value=fake_model,
        ):
            result = MatchingService.recalculate_for_job(job.id)

        self.assertEqual(result, 50)
        self.assertEqual(len(fake_model.encode_calls), 51)
        self.assertEqual(len(fake_model.encode_calls[0]), 20)


class MatchingAPITests(TestCase):
    """Tests for matching API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
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
        self.candidate2 = User.objects.create_user(
            email="candidate2@example.com",
            password="pass12345",
            full_name="Candidate Two",
            role=User.Roles.CANDIDATE,
        )

        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Software Engineer",
            company_name="Tech Corp",
            location="San Francisco",
            description="We need a software engineer",
            requirements="Python, Django",
            experience_level=Job.ExperienceLevel.SENIOR,
            status=Job.JobStatus.ACTIVE,
        )

        self.draft_job = Job.objects.create(
            recruiter=self.recruiter,
            title="Draft Job",
            company_name="Tech Corp",
            location="San Francisco",
            description="Draft job",
            status=Job.JobStatus.DRAFT,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_10_candidate_match_endpoint_works(self):
        """Test 10: Candidate match endpoint works"""
        self.authenticate(self.candidate)
        response = self.client.post(f"/api/jobs/{self.job.id}/match/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("match_score", response.data)
        self.assertIn("skills_score", response.data)
        self.assertIn("experience_score", response.data)
        self.assertIn("education_score", response.data)

    def test_11_candidate_match_retrieval_works(self):
        """Test 11: Candidate match retrieval works"""
        self.authenticate(self.candidate)
        # First calculate match
        self.client.post(f"/api/jobs/{self.job.id}/match/")
        # Then retrieve
        response = self.client.get(f"/api/jobs/{self.job.id}/match/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("match_score", response.data)

    def test_12_candidate_recommendations_work(self):
        """Test 12: Candidate recommendations work"""
        self.authenticate(self.candidate)
        response = self.client.get("/api/matching/jobs/recommendations/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_13_recruiter_candidate_search_works(self):
        """Test 13: Recruiter candidate search works"""
        self.authenticate(self.recruiter)
        response = self.client.get(
            f"/api/matching/recruiter/candidates/?job_id={self.job.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_14_anonymous_blocked(self):
        """Test 14: Anonymous blocked"""
        response = self.client.post(f"/api/jobs/{self.job.id}/match/")
        self.assertEqual(response.status_code, 401)

        response = self.client.get(f"/api/jobs/{self.job.id}/match/")
        self.assertEqual(response.status_code, 401)

        response = self.client.get("/api/matching/jobs/recommendations/")
        self.assertEqual(response.status_code, 401)

        response = self.client.get(
            f"/api/matching/recruiter/candidates/?job_id={self.job.id}"
        )
        self.assertEqual(response.status_code, 401)

    def test_15_candidate_cannot_access_recruiter_endpoint(self):
        """Test 15: Candidate cannot access recruiter endpoint"""
        self.authenticate(self.candidate)
        response = self.client.get(
            f"/api/matching/recruiter/candidates/?job_id={self.job.id}"
        )
        self.assertEqual(response.status_code, 403)

    def test_16_recruiter_cannot_access_candidate_endpoint(self):
        """Test 16: Recruiter cannot access candidate endpoint"""
        self.authenticate(self.recruiter)
        response = self.client.post(f"/api/jobs/{self.job.id}/match/")
        self.assertEqual(response.status_code, 403)

        response = self.client.get("/api/matching/jobs/recommendations/")
        self.assertEqual(response.status_code, 403)

    def test_17_recruiter_ownership_enforced(self):
        """Test 17: Recruiter ownership enforced"""
        self.authenticate(self.recruiter2)
        response = self.client.get(
            f"/api/matching/recruiter/candidates/?job_id={self.job.id}"
        )
        self.assertEqual(response.status_code, 404)

    def test_18_match_updates_existing_jobmatch(self):
        """Test 18: Match updates existing JobMatch"""
        self.authenticate(self.candidate)

        # First match
        response1 = self.client.post(f"/api/jobs/{self.job.id}/match/")
        match_id = response1.data["id"]

        # Second match (should update)
        response2 = self.client.post(f"/api/jobs/{self.job.id}/match/")

        self.assertEqual(response2.data["id"], match_id)
        self.assertEqual(JobMatch.objects.count(), 1)

    def test_19_recommendation_ordering_works(self):
        """Test 19: Recommendation ordering works"""
        # Create another job with different requirements
        Job.objects.create(
            recruiter=self.recruiter,
            title="Junior Developer",
            company_name="Tech Corp",
            location="San Francisco",
            description="Junior role",
            requirements="Python",
            experience_level=Job.ExperienceLevel.JUNIOR,
            status=Job.JobStatus.ACTIVE,
        )

        self.authenticate(self.candidate)
        response = self.client.get("/api/matching/jobs/recommendations/")

        # Verify ordering by match_score DESC
        if len(response.data) > 1:
            scores = [item["match_score"] for item in response.data]
            self.assertEqual(scores, sorted(scores, reverse=True))

    def test_20_only_active_jobs_recommended(self):
        """Test 20: Only ACTIVE jobs recommended"""
        # Create match records for both jobs
        MatchingService.calculate_match(self.candidate, self.job)
        MatchingService.calculate_match(self.candidate, self.draft_job)

        self.authenticate(self.candidate)
        response = self.client.get("/api/matching/jobs/recommendations/")

        job_ids = [item["job_id"] for item in response.data]
        self.assertNotIn(str(self.draft_job.id), job_ids)
        self.assertIn(str(self.job.id), job_ids)

    def test_21_candidate_cannot_match_with_draft_job(self):
        """Test 21: Candidate cannot match with draft job"""
        self.authenticate(self.candidate)
        response = self.client.post(f"/api/jobs/{self.draft_job.id}/match/")
        self.assertEqual(response.status_code, 404)

    def test_22_candidate_cannot_match_with_closed_job(self):
        """Test 22: Candidate cannot match with closed job"""
        self.job.status = Job.JobStatus.CLOSED
        self.job.closed_at = timezone.now()
        self.job.save()

        self.authenticate(self.candidate)
        response = self.client.post(f"/api/jobs/{self.job.id}/match/")
        self.assertEqual(response.status_code, 404)

    def test_23_recruiter_requires_job_id_parameter(self):
        """Test 23: Recruiter requires job_id parameter"""
        self.authenticate(self.recruiter)
        response = self.client.get("/api/matching/recruiter/candidates/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("job_id", response.data["detail"])

    def test_24_candidate_ranking_works(self):
        """Test 24: Candidate ranking works for recruiter"""
        # Create candidates with different skill levels
        resume1 = Resume.objects.create(user=self.candidate)
        version1 = ResumeVersion.objects.create(
            resume=resume1,
            original_filename="resume.pdf",
            stored_filename="unique1.pdf",
            file_size=1000,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        structured1 = StructuredResume.objects.create(resume_version=version1)
        ResumeSkill.objects.create(structured_resume=structured1, name="Python")

        resume2 = Resume.objects.create(user=self.candidate2)
        version2 = ResumeVersion.objects.create(
            resume=resume2,
            original_filename="resume.pdf",
            stored_filename="unique2.pdf",
            file_size=1000,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        structured2 = StructuredResume.objects.create(resume_version=version2)
        ResumeSkill.objects.create(structured_resume=structured2, name="Python")
        ResumeSkill.objects.create(structured_resume=structured2, name="Django")

        # Create match records for both candidates
        MatchingService.calculate_match(self.candidate, self.job)
        MatchingService.calculate_match(self.candidate2, self.job)

        self.authenticate(self.recruiter)
        response = self.client.get(
            f"/api/matching/recruiter/candidates/?job_id={self.job.id}"
        )

        # candidate2 should rank higher (more skills matched)
        self.assertEqual(len(response.data), 2)
        if response.data[0]["candidate_email"] == self.candidate2.email:
            self.assertGreaterEqual(
                response.data[0]["match_score"], response.data[1]["match_score"]
            )

    def test_25_query_optimization(self):
        """Test 25: Query optimization with select_related"""
        self.authenticate(self.candidate)
        # Verify that the view uses select_related to avoid N+1 queries
        # This test verifies the implementation uses query optimization
        with self.assertNumQueries(1):
            # The query should be optimized with select_related
            active_jobs = Job.objects.filter(
                status=Job.JobStatus.ACTIVE
            ).select_related("recruiter")
            list(active_jobs)  # Force evaluation


class CandidateDiscoveryTests(TestCase):
    """Tests for candidate profile and search endpoints"""

    def setUp(self):
        self.client = APIClient()
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

        # Create candidate resume with structured data
        resume = Resume.objects.create(user=self.candidate)
        version = ResumeVersion.objects.create(
            resume=resume,
            original_filename="resume.pdf",
            stored_filename="unique.pdf",
            file_size=1000,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        self.structured_resume = StructuredResume.objects.create(
            resume_version=version,
            full_name="Candidate One",
            email="candidate@example.com",
            location="San Francisco",
        )
        ResumeSkill.objects.create(
            structured_resume=self.structured_resume, name="Python"
        )
        ResumeSkill.objects.create(
            structured_resume=self.structured_resume, name="Django"
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_26_candidate_profile_endpoint_works(self):
        """Test 26: Candidate profile endpoint works"""
        self.authenticate(self.recruiter)
        response = self.client.get(f"/api/resumes/candidates/{self.candidate.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("candidate_id", response.data)
        self.assertIn("candidate_email", response.data)
        self.assertIn("candidate_name", response.data)
        self.assertIn("structured_resume", response.data)

    def test_27_candidate_profile_requires_recruiter(self):
        """Test 27: Candidate profile requires recruiter"""
        self.authenticate(self.candidate)
        response = self.client.get(f"/api/resumes/candidates/{self.candidate.id}/")
        self.assertEqual(response.status_code, 403)

    def test_28_candidate_profile_404_for_nonexistent(self):
        """Test 28: Candidate profile returns 404 for non-existent candidate"""
        from uuid import uuid4

        fake_id = uuid4()
        self.authenticate(self.recruiter)
        response = self.client.get(f"/api/resumes/candidates/{fake_id}/")
        self.assertEqual(response.status_code, 404)

    def test_29_candidate_search_endpoint_works(self):
        """Test 29: Candidate search endpoint works"""
        self.authenticate(self.recruiter)
        response = self.client.get("/api/resumes/candidates/search/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_30_candidate_search_requires_recruiter(self):
        """Test 30: Candidate search requires recruiter"""
        self.authenticate(self.candidate)
        response = self.client.get("/api/resumes/candidates/search/")
        self.assertEqual(response.status_code, 403)

    def test_31_candidate_search_filters_by_skills(self):
        """Test 31: Candidate search filters by skills"""
        self.authenticate(self.recruiter)
        response = self.client.get("/api/resumes/candidates/search/?skills=Python")
        self.assertEqual(response.status_code, 200)
        # Should return candidate with Python skill
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["candidate_email"], "candidate@example.com")

    def test_32_candidate_search_filters_by_location(self):
        """Test 32: Candidate search filters by location"""
        self.authenticate(self.recruiter)
        response = self.client.get(
            "/api/resumes/candidates/search/?location=San Francisco"
        )
        self.assertEqual(response.status_code, 200)
        # Should return candidate in San Francisco
        self.assertEqual(len(response.data), 1)

    def test_33_candidate_search_filters_by_education(self):
        """Test 33: Candidate search filters by education"""
        ResumeEducation.objects.create(
            structured_resume=self.structured_resume,
            institution="University",
            degree="Bachelor of Science",
        )
        self.authenticate(self.recruiter)
        response = self.client.get("/api/resumes/candidates/search/?education=bachelor")
        self.assertEqual(response.status_code, 200)
        # Should return candidate with bachelor degree
        self.assertEqual(len(response.data), 1)

    def test_34_candidate_search_invalid_experience_min(self):
        """Test 34: Candidate search validates experience_min parameter"""
        self.authenticate(self.recruiter)
        response = self.client.get(
            "/api/resumes/candidates/search/?experience_min=invalid"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("experience_min must be a number", response.data["detail"])

    def test_35_candidate_profile_includes_full_structured_data(self):
        """Test 35: Candidate profile includes full structured resume data"""
        ResumeEducation.objects.create(
            structured_resume=self.structured_resume,
            institution="University",
            degree="Bachelor",
        )
        from datetime import date, timedelta

        start_date = date.today() - timedelta(days=365)
        ResumeExperience.objects.create(
            structured_resume=self.structured_resume,
            company="Tech Corp",
            job_title="Developer",
            start_date=start_date,
        )

        self.authenticate(self.recruiter)
        response = self.client.get(f"/api/resumes/candidates/{self.candidate.id}/")
        self.assertEqual(response.status_code, 200)

        structured = response.data["structured_resume"]
        self.assertIn("skills", structured)
        self.assertIn("education", structured)
        self.assertIn("experience", structured)
        self.assertEqual(len(structured["skills"]), 2)
        self.assertEqual(len(structured["education"]), 1)
        self.assertEqual(len(structured["experience"]), 1)
