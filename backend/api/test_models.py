from django.db import IntegrityError
from django.test import TestCase

from .models import (
    ApplicationClick,
    CandidateProfile,
    CandidateSkill,
    Company,
    FetchRun,
    IngestionSource,
    Job,
    JobSkill,
    MatchScore,
    Skill,
    User,
    WorkExperience,
)


class UserModelTest(TestCase):
    """Tests for custom User model."""

    def test_create_user(self):
        """Test user creation with email and password."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_email_normalization(self):
        """Test email normalization."""
        user = User.objects.create_user(
            email="Test@Example.COM", password="testpass123"
        )
        self.assertEqual(
            user.email, "Test@example.com"
        )  # Django normalizes domain to lowercase

    def test_email_uniqueness(self):
        """Test email uniqueness constraint."""
        User.objects.create_user(email="test@example.com", password="testpass123")
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email="test@example.com", password="testpass123")

    def test_create_superuser(self):
        """Test superuser creation."""
        user = User.objects.create_superuser(
            email="admin@example.com", password="admin123"
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_password_hashing(self):
        """Test password is hashed."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.assertNotEqual(user.password, "testpass123")
        self.assertTrue(user.check_password("testpass123"))


class CandidateProfileTest(TestCase):
    """Tests for CandidateProfile model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="candidate@example.com", password="testpass123"
        )

    def test_profile_creation(self):
        """Test candidate profile creation."""
        profile = CandidateProfile.objects.create(
            user=self.user,
            location="Bangalore",
            remote_preference="remote",
            total_experience_years=2.5,
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.location, "Bangalore")

    def test_user_profile_uniqueness(self):
        """Test one-to-one relationship uniqueness."""
        CandidateProfile.objects.create(user=self.user, location="Bangalore")
        with self.assertRaises(IntegrityError):
            CandidateProfile.objects.create(user=self.user, location="Mumbai")

    def test_cascade_delete(self):
        """Test profile deleted when user is deleted."""
        profile = CandidateProfile.objects.create(user=self.user, location="Bangalore")
        self.user.delete()
        self.assertFalse(CandidateProfile.objects.filter(id=profile.id).exists())

    def test_nullable_fields(self):
        """Test optional fields can be null."""
        profile = CandidateProfile.objects.create(user=self.user)
        self.assertIsNone(profile.phone)
        self.assertIsNone(profile.salary_min)
        self.assertIsNone(profile.total_experience_years)


class SkillTest(TestCase):
    """Tests for Skill model."""

    def test_skill_creation(self):
        """Test skill creation."""
        skill = Skill.objects.create(name="Python", category="programming")
        self.assertEqual(skill.name, "Python")
        self.assertEqual(skill.category, "programming")

    def test_skill_name_uniqueness(self):
        """Test skill name uniqueness."""
        Skill.objects.create(name="Python", category="programming")
        with self.assertRaises(IntegrityError):
            Skill.objects.create(name="Python", category="framework")


class CandidateSkillTest(TestCase):
    """Tests for CandidateSkill model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="candidate@example.com", password="testpass123"
        )
        self.profile = CandidateProfile.objects.create(user=self.user)
        self.skill = Skill.objects.create(name="Python", category="programming")

    def test_candidate_skill_creation(self):
        """Test candidate-skill association."""
        cand_skill = CandidateSkill.objects.create(
            candidate=self.profile, skill=self.skill, proficiency="intermediate"
        )
        self.assertEqual(cand_skill.candidate, self.profile)
        self.assertEqual(cand_skill.skill, self.skill)

    def test_duplicate_prevention(self):
        """Test duplicate candidate-skill prevention."""
        CandidateSkill.objects.create(candidate=self.profile, skill=self.skill)
        with self.assertRaises(IntegrityError):
            CandidateSkill.objects.create(candidate=self.profile, skill=self.skill)

    def test_cascade_delete_profile(self):
        """Test candidate-skill deleted when profile deleted."""
        cand_skill = CandidateSkill.objects.create(
            candidate=self.profile, skill=self.skill
        )
        self.profile.delete()
        self.assertFalse(CandidateSkill.objects.filter(id=cand_skill.id).exists())

    def test_protect_delete_skill(self):
        """Test skill protected from deletion when in use."""
        CandidateSkill.objects.create(candidate=self.profile, skill=self.skill)
        with self.assertRaises(IntegrityError):
            self.skill.delete()


class WorkExperienceTest(TestCase):
    """Tests for WorkExperience model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="candidate@example.com", password="testpass123"
        )
        self.profile = CandidateProfile.objects.create(user=self.user)

    def test_experience_creation(self):
        """Test work experience creation."""
        exp = WorkExperience.objects.create(
            candidate=self.profile,
            company_name="Acme Corp",
            role="Software Engineer",
            start_date="2020-01-01",
            end_date="2022-01-01",
        )
        self.assertEqual(exp.company_name, "Acme Corp")
        self.assertEqual(exp.role, "Software Engineer")

    def test_null_end_date(self):
        """Test null end date for current role."""
        exp = WorkExperience.objects.create(
            candidate=self.profile,
            company_name="Acme Corp",
            role="Software Engineer",
            start_date="2020-01-01",
        )
        self.assertIsNone(exp.end_date)

    def test_cascade_delete(self):
        """Test experience deleted when profile deleted."""
        exp = WorkExperience.objects.create(
            candidate=self.profile, company_name="Acme Corp", role="Software Engineer"
        )
        self.profile.delete()
        self.assertFalse(WorkExperience.objects.filter(id=exp.id).exists())


class CompanyTest(TestCase):
    """Tests for Company model."""

    def test_company_creation(self):
        """Test company creation."""
        company = Company.objects.create(name="Acme Corp", website="https://acme.com")
        self.assertEqual(company.name, "Acme Corp")

    def test_company_name_uniqueness(self):
        """Test company name uniqueness."""
        Company.objects.create(name="Acme Corp")
        with self.assertRaises(IntegrityError):
            Company.objects.create(name="Acme Corp")


class IngestionSourceTest(TestCase):
    """Tests for IngestionSource model."""

    def setUp(self):
        self.company = Company.objects.create(name="Acme Corp")

    def test_source_creation(self):
        """Test ingestion source creation."""
        source = IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
        )
        self.assertEqual(source.company, self.company)
        self.assertEqual(source.source_type, "career_page")

    def test_unique_company_base_url(self):
        """Test unique constraint on company + base_url."""
        IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
        )
        with self.assertRaises(IntegrityError):
            IngestionSource.objects.create(
                company=self.company,
                name="Another Source",
                source_type="api",
                base_url="https://acme.com/careers",
            )

    def test_protect_delete_company(self):
        """Test company protected from deletion when sources exist."""
        IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
        )
        with self.assertRaises(IntegrityError):
            self.company.delete()


class FetchRunTest(TestCase):
    """Tests for FetchRun model."""

    def setUp(self):
        self.company = Company.objects.create(name="Acme Corp")
        self.source = IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
        )

    def test_fetch_run_creation(self):
        """Test fetch run creation."""
        run = FetchRun.objects.create(source=self.source, status="success")
        self.assertEqual(run.source, self.source)
        self.assertEqual(run.status, "success")

    def test_cascade_delete_source(self):
        """Test fetch run deleted when source deleted."""
        run = FetchRun.objects.create(source=self.source, status="success")
        self.source.delete()
        self.assertFalse(FetchRun.objects.filter(id=run.id).exists())


class JobTest(TestCase):
    """Tests for Job model."""

    def setUp(self):
        self.company = Company.objects.create(name="Acme Corp")
        self.source = IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
        )

    def test_job_creation(self):
        """Test job creation."""
        job = Job.objects.create(
            source=self.source,
            company=self.company,
            external_id="12345",
            title="Software Engineer",
            description="Job description",
            application_url="https://acme.com/jobs/12345",
        )
        self.assertEqual(job.title, "Software Engineer")
        self.assertEqual(job.source, self.source)
        self.assertEqual(job.company, self.company)

    def test_unique_source_external_id(self):
        """Test unique constraint on source + external_id."""
        Job.objects.create(
            source=self.source,
            company=self.company,
            external_id="12345",
            title="Software Engineer",
            description="Job description",
            application_url="https://acme.com/jobs/12345",
        )
        with self.assertRaises(IntegrityError):
            Job.objects.create(
                source=self.source,
                company=self.company,
                external_id="12345",
                title="Another Job",
                description="Another description",
                application_url="https://acme.com/jobs/67890",
            )

    def test_null_external_id_allowed(self):
        """Test null external_id is allowed."""
        job = Job.objects.create(
            source=self.source,
            company=self.company,
            title="Software Engineer",
            description="Job description",
            application_url="https://acme.com/jobs/12345",
        )
        self.assertIsNone(job.external_id)

    def test_protect_delete_source(self):
        """Test source protected from deletion when jobs exist."""
        Job.objects.create(
            source=self.source,
            company=self.company,
            title="Software Engineer",
            description="Job description",
            application_url="https://acme.com/jobs/12345",
        )
        with self.assertRaises(IntegrityError):
            self.source.delete()

    def test_protect_delete_company(self):
        """Test company protected from deletion when jobs exist."""
        Job.objects.create(
            source=self.source,
            company=self.company,
            title="Software Engineer",
            description="Job description",
            application_url="https://acme.com/jobs/12345",
        )
        with self.assertRaises(IntegrityError):
            self.company.delete()


class JobSkillTest(TestCase):
    """Tests for JobSkill model."""

    def setUp(self):
        self.company = Company.objects.create(name="Acme Corp")
        self.source = IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
        )
        self.job = Job.objects.create(
            source=self.source,
            company=self.company,
            title="Software Engineer",
            description="Job description",
            application_url="https://acme.com/jobs/12345",
        )
        self.skill = Skill.objects.create(name="Python", category="programming")

    def test_job_skill_creation(self):
        """Test job-skill association."""
        job_skill = JobSkill.objects.create(
            job=self.job, skill=self.skill, is_required=True
        )
        self.assertEqual(job_skill.job, self.job)
        self.assertEqual(job_skill.skill, self.skill)

    def test_duplicate_prevention(self):
        """Test duplicate job-skill prevention."""
        JobSkill.objects.create(job=self.job, skill=self.skill)
        with self.assertRaises(IntegrityError):
            JobSkill.objects.create(job=self.job, skill=self.skill)

    def test_cascade_delete_job(self):
        """Test job-skill deleted when job deleted."""
        job_skill = JobSkill.objects.create(job=self.job, skill=self.skill)
        self.job.delete()
        self.assertFalse(JobSkill.objects.filter(id=job_skill.id).exists())

    def test_protect_delete_skill(self):
        """Test skill protected from deletion when in use."""
        JobSkill.objects.create(job=self.job, skill=self.skill)
        with self.assertRaises(IntegrityError):
            self.skill.delete()


class MatchScoreTest(TestCase):
    """Tests for MatchScore model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="candidate@example.com", password="testpass123"
        )
        self.profile = CandidateProfile.objects.create(user=self.user)
        self.company = Company.objects.create(name="Acme Corp")
        self.source = IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
        )
        self.job = Job.objects.create(
            source=self.source,
            company=self.company,
            title="Software Engineer",
            description="Job description",
            application_url="https://acme.com/jobs/12345",
        )

    def test_match_score_creation(self):
        """Test match score creation."""
        score = MatchScore.objects.create(
            candidate=self.profile,
            job=self.job,
            base_score=0.75,
            final_score=0.80,
            skill_similarity=0.85,
            experience_match=0.70,
            keyword_overlap=0.60,
        )
        self.assertEqual(score.candidate, self.profile)
        self.assertEqual(score.job, self.job)
        self.assertEqual(float(score.base_score), 0.75)

    def test_candidate_job_uniqueness(self):
        """Test unique constraint on candidate + job."""
        MatchScore.objects.create(
            candidate=self.profile, job=self.job, base_score=0.75, final_score=0.80
        )
        with self.assertRaises(IntegrityError):
            MatchScore.objects.create(
                candidate=self.profile, job=self.job, base_score=0.50, final_score=0.55
            )

    def test_cascade_delete_candidate(self):
        """Test match score deleted when candidate deleted."""
        score = MatchScore.objects.create(
            candidate=self.profile, job=self.job, base_score=0.75, final_score=0.80
        )
        self.profile.delete()
        self.assertFalse(MatchScore.objects.filter(id=score.id).exists())

    def test_cascade_delete_job(self):
        """Test match score deleted when job deleted."""
        score = MatchScore.objects.create(
            candidate=self.profile, job=self.job, base_score=0.75, final_score=0.80
        )
        self.job.delete()
        self.assertFalse(MatchScore.objects.filter(id=score.id).exists())


class ApplicationClickTest(TestCase):
    """Tests for ApplicationClick model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="candidate@example.com", password="testpass123"
        )
        self.profile = CandidateProfile.objects.create(user=self.user)
        self.company = Company.objects.create(name="Acme Corp")
        self.source = IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
        )
        self.job = Job.objects.create(
            source=self.source,
            company=self.company,
            title="Software Engineer",
            description="Job description",
            application_url="https://acme.com/jobs/12345",
        )

    def test_application_click_creation(self):
        """Test application click creation."""
        click = ApplicationClick.objects.create(
            candidate=self.profile, job=self.job, ip_address="127.0.0.1"
        )
        self.assertEqual(click.candidate, self.profile)
        self.assertEqual(click.job, self.job)
        self.assertEqual(click.ip_address, "127.0.0.1")

    def test_multiple_clicks_allowed(self):
        """Test multiple clicks are allowed (no uniqueness constraint)."""
        ApplicationClick.objects.create(candidate=self.profile, job=self.job)
        ApplicationClick.objects.create(candidate=self.profile, job=self.job)
        self.assertEqual(
            ApplicationClick.objects.filter(
                candidate=self.profile, job=self.job
            ).count(),
            2,
        )

    def test_cascade_delete_candidate(self):
        """Test application click deleted when candidate deleted."""
        click = ApplicationClick.objects.create(candidate=self.profile, job=self.job)
        self.profile.delete()
        self.assertFalse(ApplicationClick.objects.filter(id=click.id).exists())

    def test_cascade_delete_job(self):
        """Test application click deleted when job deleted."""
        click = ApplicationClick.objects.create(candidate=self.profile, job=self.job)
        self.job.delete()
        self.assertFalse(ApplicationClick.objects.filter(id=click.id).exists())


class AdminSecurityTest(TestCase):
    """Tests for admin write-boundary restrictions."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@example.com",
            password="admin123",
            is_staff=True,
            is_superuser=True,
        )
        self.company = Company.objects.create(name="Acme Corp")

    def test_skill_read_only(self):
        """Test Skill model is read-only in admin."""
        from django.contrib.admin.sites import AdminSite

        from .admin import SkillAdmin

        admin = SkillAdmin(Skill, AdminSite())
        self.assertFalse(admin.has_add_permission(None))
        self.assertFalse(admin.has_change_permission(None))
        self.assertFalse(admin.has_delete_permission(None))

    def test_company_read_only(self):
        """Test Company model is read-only in admin."""
        from django.contrib.admin.sites import AdminSite

        from .admin import CompanyAdmin

        admin = CompanyAdmin(Company, AdminSite())
        self.assertFalse(admin.has_add_permission(None))
        self.assertFalse(admin.has_change_permission(None))
        self.assertFalse(admin.has_delete_permission(None))

    def test_ingestion_source_read_only(self):
        """Test IngestionSource model is read-only in admin."""
        from django.contrib.admin.sites import AdminSite

        from .admin import IngestionSourceAdmin

        source = IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
        )
        admin = IngestionSourceAdmin(IngestionSource, AdminSite())
        self.assertFalse(admin.has_add_permission(None))
        self.assertFalse(admin.has_change_permission(None, source))
        self.assertFalse(admin.has_delete_permission(None, source))

    def test_job_read_only(self):
        """Test Job model is read-only in admin."""
        from django.contrib.admin.sites import AdminSite

        from .admin import JobAdmin

        source = IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
        )
        job = Job.objects.create(
            source=source,
            company=self.company,
            title="Software Engineer",
            description="Job description",
            application_url="https://acme.com/jobs/12345",
        )
        admin = JobAdmin(Job, AdminSite())
        self.assertFalse(admin.has_add_permission(None))
        self.assertFalse(admin.has_change_permission(None, job))
        self.assertFalse(admin.has_delete_permission(None, job))

    def test_job_skill_read_only(self):
        """Test JobSkill model is read-only in admin."""
        from django.contrib.admin.sites import AdminSite

        from .admin import JobSkillAdmin

        source = IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
        )
        job = Job.objects.create(
            source=source,
            company=self.company,
            title="Software Engineer",
            description="Job description",
            application_url="https://acme.com/jobs/12345",
        )
        skill = Skill.objects.create(name="Python", category="programming")
        job_skill = JobSkill.objects.create(job=job, skill=skill)
        admin = JobSkillAdmin(JobSkill, AdminSite())
        self.assertFalse(admin.has_add_permission(None))
        self.assertFalse(admin.has_change_permission(None, job_skill))
        self.assertFalse(admin.has_delete_permission(None, job_skill))

    def test_match_score_read_only(self):
        """Test MatchScore model is read-only in admin."""
        from django.contrib.admin.sites import AdminSite

        from .admin import MatchScoreAdmin

        user = User.objects.create_user(
            email="candidate@example.com", password="testpass123"
        )
        profile = CandidateProfile.objects.create(user=user)
        source = IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
        )
        job = Job.objects.create(
            source=source,
            company=self.company,
            title="Software Engineer",
            description="Job description",
            application_url="https://acme.com/jobs/12345",
        )
        score = MatchScore.objects.create(
            candidate=profile, job=job, base_score=0.75, final_score=0.80
        )
        admin = MatchScoreAdmin(MatchScore, AdminSite())
        self.assertFalse(admin.has_add_permission(None))
        self.assertFalse(admin.has_change_permission(None, score))
        self.assertFalse(admin.has_delete_permission(None, score))

    def test_application_click_read_only(self):
        """Test ApplicationClick model is read-only in admin."""
        from django.contrib.admin.sites import AdminSite

        from .admin import ApplicationClickAdmin

        user = User.objects.create_user(
            email="candidate@example.com", password="testpass123"
        )
        profile = CandidateProfile.objects.create(user=user)
        source = IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
        )
        job = Job.objects.create(
            source=source,
            company=self.company,
            title="Software Engineer",
            description="Job description",
            application_url="https://acme.com/jobs/12345",
        )
        click = ApplicationClick.objects.create(candidate=profile, job=job)
        admin = ApplicationClickAdmin(ApplicationClick, AdminSite())
        self.assertFalse(admin.has_add_permission(None))
        self.assertFalse(admin.has_change_permission(None, click))
        self.assertFalse(admin.has_delete_permission(None, click))
