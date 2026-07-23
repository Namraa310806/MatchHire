"""
Tests for document serializers.
"""

from datetime import datetime
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.users.models import CandidateProfile, RecruiterProfile
from apps.jobs.models import Job
from apps.resumes.models import Resume, ResumeVersion, StructuredResume, ResumeSkill
from apps.applications.models import Application

from apps.search.indexing.serializers import (
    CandidateSerializer,
    RecruiterSerializer,
    JobSerializer,
    ResumeSerializer,
    ApplicationSerializer,
    SkillSerializer,
)
from apps.search.indexing.documents import EntityType

User = get_user_model()


class TestCandidateSerializer(TestCase):
    """Test CandidateSerializer class."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="candidate@example.com",
            password="password123",
            role=User.Roles.CANDIDATE,
            full_name="John Doe",
        )
        self.profile = CandidateProfile.objects.create(
            user=self.user,
            headline="Software Engineer",
            bio="Experienced developer",
            skills_text="Python Django",
        )
    
    def test_serialize_candidate(self):
        """Test serializing a candidate."""
        document = CandidateSerializer.serialize(self.user, self.profile)
        
        self.assertEqual(document.id, str(self.user.id))
        self.assertEqual(document.entity_type, EntityType.CANDIDATE)
        self.assertEqual(document.email, self.user.email)
        self.assertEqual(document.full_name, self.user.full_name)
        self.assertEqual(document.headline, self.profile.headline)
    
    def test_serialize_from_user(self):
        """Test serializing from user instance."""
        document = CandidateSerializer.serialize_from_user(self.user)
        
        self.assertEqual(document.id, str(self.user.id))
        self.assertEqual(document.email, self.user.email)
    
    def test_serialize_non_candidate_raises_error(self):
        """Test that serializing non-candidate raises error."""
        recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="password123",
            role=User.Roles.RECRUITER,
        )
        
        with self.assertRaises(ValueError):
            CandidateSerializer.serialize_from_user(recruiter)


class TestRecruiterSerializer(TestCase):
    """Test RecruiterSerializer class."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="recruiter@example.com",
            password="password123",
            role=User.Roles.RECRUITER,
            full_name="Jane Smith",
        )
        self.profile = RecruiterProfile.objects.create(
            user=self.user,
            company_name="Tech Corp",
            job_title="HR Manager",
        )
    
    def test_serialize_recruiter(self):
        """Test serializing a recruiter."""
        document = RecruiterSerializer.serialize(self.user, self.profile)
        
        self.assertEqual(document.id, str(self.user.id))
        self.assertEqual(document.entity_type, EntityType.RECRUITER)
        self.assertEqual(document.email, self.user.email)
        self.assertEqual(document.company_name, self.profile.company_name)
    
    def test_serialize_from_user(self):
        """Test serializing from user instance."""
        document = RecruiterSerializer.serialize_from_user(self.user)
        
        self.assertEqual(document.id, str(self.user.id))
        self.assertEqual(document.email, self.user.email)


class TestJobSerializer(TestCase):
    """Test JobSerializer class."""
    
    def setUp(self):
        """Set up test data."""
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="password123",
            role=User.Roles.RECRUITER,
        )
        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Software Engineer",
            company_name="Tech Corp",
            location="San Francisco",
            description="Build amazing software",
            salary_min=Decimal("50000.00"),
            salary_max=Decimal("100000.00"),
        )
    
    def test_serialize_job(self):
        """Test serializing a job."""
        document = JobSerializer.serialize(self.job)
        
        self.assertEqual(document.id, str(self.job.id))
        self.assertEqual(document.entity_type, EntityType.JOB)
        self.assertEqual(document.title, self.job.title)
        self.assertEqual(document.company_name, self.job.company_name)
        self.assertEqual(document.salary_min, 50000.0)
        self.assertEqual(document.salary_max, 100000.0)


class TestResumeSerializer(TestCase):
    """Test ResumeSerializer class."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="candidate@example.com",
            password="password123",
            role=User.Roles.CANDIDATE,
        )
        self.resume = Resume.objects.create(user=self.user)
        self.version = ResumeVersion.objects.create(
            resume=self.resume,
            original_filename="resume.pdf",
            stored_filename="resume_123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
    
    def test_serialize_resume_version(self):
        """Test serializing a resume version."""
        document = ResumeSerializer.serialize(self.version)
        
        self.assertEqual(document.id, str(self.version.id))
        self.assertEqual(document.entity_type, EntityType.RESUME)
        self.assertEqual(document.resume_id, str(self.resume.id))
        self.assertEqual(document.user_id, str(self.user.id))
        self.assertEqual(document.version_number, 1)
    
    def test_serialize_resume_with_structured_data(self):
        """Test serializing resume with structured data."""
        structured = StructuredResume.objects.create(
            resume_version=self.version,
            full_name="John Doe",
            summary="Software Engineer",
        )
        ResumeSkill.objects.create(
            structured_resume=structured,
            name="Python",
        )
        
        document = ResumeSerializer.serialize(self.version)
        
        self.assertEqual(document.full_name, "John Doe")
        self.assertEqual(document.summary, "Software Engineer")
        self.assertIn("Python", document.skills)


class TestApplicationSerializer(TestCase):
    """Test ApplicationSerializer class."""
    
    def setUp(self):
        """Set up test data."""
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="password123",
            role=User.Roles.RECRUITER,
        )
        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            password="password123",
            role=User.Roles.CANDIDATE,
        )
        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Software Engineer",
            company_name="Tech Corp",
        )
        self.resume = Resume.objects.create(user=self.candidate)
        self.version = ResumeVersion.objects.create(
            resume=self.resume,
            original_filename="resume.pdf",
            stored_filename="resume_123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            version_number=1,
            is_current=True,
        )
        self.application = Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            resume_version=self.version,
        )
    
    def test_serialize_application(self):
        """Test serializing an application."""
        document = ApplicationSerializer.serialize(self.application)
        
        self.assertEqual(document.id, str(self.application.id))
        self.assertEqual(document.entity_type, EntityType.APPLICATION)
        self.assertEqual(document.job_id, str(self.job.id))
        self.assertEqual(document.candidate_id, str(self.candidate.id))


class TestSkillSerializer(TestCase):
    """Test SkillSerializer class."""
    
    def test_serialize_skill(self):
        """Test serializing a skill."""
        document = SkillSerializer.serialize("Python", usage_count=100)
        
        self.assertEqual(document.name, "Python")
        self.assertEqual(document.usage_count, 100)
        self.assertEqual(document.entity_type, EntityType.SKILL)
