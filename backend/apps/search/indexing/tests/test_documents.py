"""
Tests for search documents.
"""

from datetime import datetime
from decimal import Decimal

from django.test import TestCase

from apps.search.indexing.documents import (
    BaseDocument,
    CandidateDocument,
    ResumeDocument,
    JobDocument,
    CompanyDocument,
    RecruiterDocument,
    SkillDocument,
    ApplicationDocument,
    InterviewDocument,
    EntityType,
)


class TestBaseDocument(TestCase):
    """Test BaseDocument class."""
    
    def test_base_document_creation(self):
        """Test creating a base document."""
        doc = BaseDocument(
            id="test-123",
            entity_type=EntityType.CANDIDATE,
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        self.assertEqual(doc.id, "test-123")
        self.assertEqual(doc.entity_type, EntityType.CANDIDATE)
        self.assertEqual(doc.version, 1)
        self.assertIsNone(doc.vector_embedding)
    
    def test_base_document_to_dict(self):
        """Test converting base document to dictionary."""
        now = datetime.utcnow()
        doc = BaseDocument(
            id="test-123",
            entity_type=EntityType.CANDIDATE,
            version=1,
            created_at=now,
            updated_at=now,
            metadata={"key": "value"},
        )
        
        result = doc.to_dict()
        
        self.assertEqual(result["id"], "test-123")
        self.assertEqual(result["entity_type"], "candidate")
        self.assertEqual(result["version"], 1)
        self.assertEqual(result["metadata"], {"key": "value"})


class TestCandidateDocument(TestCase):
    """Test CandidateDocument class."""
    
    def test_candidate_document_creation(self):
        """Test creating a candidate document."""
        doc = CandidateDocument(
            id="user-123",
            user_id="user-123",
            email="test@example.com",
            full_name="John Doe",
        )
        
        self.assertEqual(doc.id, "user-123")
        self.assertEqual(doc.entity_type, EntityType.CANDIDATE)
        self.assertEqual(doc.email, "test@example.com")
        self.assertEqual(doc.full_name, "John Doe")
    
    def test_candidate_document_searchable_text(self):
        """Test searchable text generation."""
        doc = CandidateDocument(
            id="user-123",
            user_id="user-123",
            email="test@example.com",
            full_name="John Doe",
            headline="Software Engineer",
            bio="Experienced developer",
            skills_text="Python Django",
        )
        
        self.assertIn("John Doe", doc.searchable_text)
        self.assertIn("Software Engineer", doc.searchable_text)
        self.assertIn("Python Django", doc.searchable_text)


class TestJobDocument(TestCase):
    """Test JobDocument class."""
    
    def test_job_document_creation(self):
        """Test creating a job document."""
        doc = JobDocument(
            id="job-123",
            job_id="job-123",
            recruiter_id="recruiter-123",
            title="Software Engineer",
            company_name="Tech Corp",
        )
        
        self.assertEqual(doc.id, "job-123")
        self.assertEqual(doc.entity_type, EntityType.JOB)
        self.assertEqual(doc.title, "Software Engineer")
        self.assertEqual(doc.company_name, "Tech Corp")
    
    def test_job_document_searchable_text(self):
        """Test searchable text generation."""
        doc = JobDocument(
            id="job-123",
            job_id="job-123",
            recruiter_id="recruiter-123",
            title="Software Engineer",
            company_name="Tech Corp",
            description="Build amazing software",
            requirements="Python experience",
        )
        
        self.assertIn("Software Engineer", doc.searchable_text)
        self.assertIn("Tech Corp", doc.searchable_text)
        self.assertIn("Build amazing software", doc.searchable_text)
    
    def test_job_document_salary_fields(self):
        """Test salary field handling."""
        doc = JobDocument(
            id="job-123",
            job_id="job-123",
            recruiter_id="recruiter-123",
            title="Software Engineer",
            company_name="Tech Corp",
            salary_min=50000.0,
            salary_max=100000.0,
            currency="USD",
        )
        
        self.assertEqual(doc.salary_min, 50000.0)
        self.assertEqual(doc.salary_max, 100000.0)
        self.assertEqual(doc.currency, "USD")


class TestResumeDocument(TestCase):
    """Test ResumeDocument class."""
    
    def test_resume_document_creation(self):
        """Test creating a resume document."""
        doc = ResumeDocument(
            id="resume-123",
            resume_id="resume-123",
            user_id="user-123",
            version_number=1,
        )
        
        self.assertEqual(doc.id, "resume-123")
        self.assertEqual(doc.entity_type, EntityType.RESUME)
        self.assertEqual(doc.version_number, 1)
    
    def test_resume_document_with_skills(self):
        """Test resume document with skills."""
        doc = ResumeDocument(
            id="resume-123",
            resume_id="resume-123",
            user_id="user-123",
            version_number=1,
            skills=["Python", "Django", "PostgreSQL"],
        )
        
        self.assertEqual(len(doc.skills), 3)
        self.assertIn("Python", doc.skills)
    
    def test_resume_document_searchable_text(self):
        """Test searchable text generation."""
        doc = ResumeDocument(
            id="resume-123",
            resume_id="resume-123",
            user_id="user-123",
            version_number=1,
            full_name="John Doe",
            summary="Software Engineer",
            skills=["Python", "Django"],
        )
        
        self.assertIn("John Doe", doc.searchable_text)
        self.assertIn("Software Engineer", doc.searchable_text)
        self.assertIn("Python", doc.searchable_text)


class TestApplicationDocument(TestCase):
    """Test ApplicationDocument class."""
    
    def test_application_document_creation(self):
        """Test creating an application document."""
        doc = ApplicationDocument(
            id="app-123",
            application_id="app-123",
            job_id="job-123",
            candidate_id="user-123",
            resume_version_id="resume-123",
            status="submitted",
        )
        
        self.assertEqual(doc.id, "app-123")
        self.assertEqual(doc.entity_type, EntityType.APPLICATION)
        self.assertEqual(doc.status, "submitted")


class TestSkillDocument(TestCase):
    """Test SkillDocument class."""
    
    def test_skill_document_creation(self):
        """Test creating a skill document."""
        doc = SkillDocument(
            id="skill-123",
            skill_id="skill-123",
            name="Python",
            usage_count=100,
        )
        
        self.assertEqual(doc.id, "skill-123")
        self.assertEqual(doc.entity_type, EntityType.SKILL)
        self.assertEqual(doc.name, "Python")
        self.assertEqual(doc.usage_count, 100)


class TestRecruiterDocument(TestCase):
    """Test RecruiterDocument class."""
    
    def test_recruiter_document_creation(self):
        """Test creating a recruiter document."""
        doc = RecruiterDocument(
            id="recruiter-123",
            user_id="recruiter-123",
            email="recruiter@example.com",
            full_name="Jane Smith",
            company_name="Tech Corp",
        )
        
        self.assertEqual(doc.id, "recruiter-123")
        self.assertEqual(doc.entity_type, EntityType.RECRUITER)
        self.assertEqual(doc.company_name, "Tech Corp")


class TestCompanyDocument(TestCase):
    """Test CompanyDocument class."""
    
    def test_company_document_creation(self):
        """Test creating a company document."""
        doc = CompanyDocument(
            id="company-123",
            company_id="company-123",
            name="Tech Corp",
            website="https://techcorp.com",
        )
        
        self.assertEqual(doc.id, "company-123")
        self.assertEqual(doc.entity_type, EntityType.COMPANY)
        self.assertEqual(doc.name, "Tech Corp")


class TestInterviewDocument(TestCase):
    """Test InterviewDocument class."""
    
    def test_interview_document_creation(self):
        """Test creating an interview document."""
        doc = InterviewDocument(
            id="interview-123",
            interview_id="interview-123",
            application_id="app-123",
            job_id="job-123",
            candidate_id="user-123",
            interview_type="technical",
            status="scheduled",
        )
        
        self.assertEqual(doc.id, "interview-123")
        self.assertEqual(doc.entity_type, EntityType.INTERVIEW)
        self.assertEqual(doc.interview_type, "technical")
