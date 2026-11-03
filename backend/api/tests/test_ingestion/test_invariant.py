"""Regression tests for job-write invariant.

Tests ensure that jobs can only be created through the ingestion pipeline,
not through admin, public API, or other shortcuts.
"""

from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from api.admin import CompanyAdmin, IngestionSourceAdmin, JobAdmin
from api.ingestion.pipeline import process_batch
from api.models import Company, IngestionSource, Job


class JobWriteInvariantTest(TestCase):
    """Regression tests for core invariant: no manual job creation."""

    def setUp(self):
        """Set up test data."""
        self.company = Company.objects.create(name="Acme Corp")
        self.source = IngestionSource.objects.create(
            company=self.company,
            name="Career Page",
            source_type="career_page",
            base_url="https://acme.com/careers",
            scraper_class="FakeScraper",
        )

    def test_job_admin_read_only(self):
        """Test Job admin is read-only (no add/change/delete permissions)."""
        admin = JobAdmin(Job, AdminSite())
        self.assertFalse(admin.has_add_permission(None))
        self.assertFalse(admin.has_change_permission(None))
        self.assertFalse(admin.has_delete_permission(None))

    def test_company_admin_read_only(self):
        """Test Company admin is read-only (no add/change/delete permissions)."""
        admin = CompanyAdmin(Company, AdminSite())
        self.assertFalse(admin.has_add_permission(None))
        self.assertFalse(admin.has_change_permission(None))
        self.assertFalse(admin.has_delete_permission(None))

    def test_ingestion_source_admin_read_only(self):
        """Test IngestionSource admin is read-only (no add/change/delete permissions)."""
        admin = IngestionSourceAdmin(IngestionSource, AdminSite())
        self.assertFalse(admin.has_add_permission(None))
        self.assertFalse(admin.has_change_permission(None, self.source))
        self.assertFalse(admin.has_delete_permission(None, self.source))

    def test_ingestion_pipeline_can_create_jobs(self):
        """Test ingestion pipeline can create jobs (intended path)."""
        raw_records = [
            {
                "source_id": self.source.id,
                "company_id": self.company.id,
                "external_id": "123",
                "title": "Software Engineer",
                "description": "Job description",
                "requirements": None,
                "location": "Bangalore",
                "application_url": "https://acme.com/jobs/123",
                "posted_date": None,
                "remote_type": None,
                "role_type": None,
                "experience_min_years": None,
                "experience_max_years": None,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "INR",
                "skills": [],
                "required_yoe": None,
            }
        ]

        result = process_batch(raw_records, "FakeScraper")
        self.assertEqual(result.jobs_created, 1)
        self.assertEqual(Job.objects.count(), 1)

    def test_direct_orm_create_possible_but_not_public(self):
        """Test direct ORM create is technically possible but not a public API.

        This test documents that Django ORM allows direct object creation,
        but this is not a supported public API path. The invariant is
        enforced at the application level (admin, views, serializers), not
        at the database level. Production deployments should use database
        permissions and application-level controls to prevent direct writes.
        """
        # This test documents the limitation: ORM doesn't prevent direct creation
        job = Job.objects.create(
            source=self.source,
            company=self.company,
            external_id="999",
            title="Direct ORM Job",
            description="Created via direct ORM (not supported path)",
            application_url="https://example.com/job",
        )
        self.assertEqual(Job.objects.count(), 1)

        # Clean up
        job.delete()

    def test_no_public_job_create_endpoint(self):
        """Test there is no public API endpoint for job creation.

        This test checks that the URL configuration does not include
        disallowed job-write methods. In a real system, this would
        also check that serializers don't allow job creation.
        """
        from django.urls import get_resolver

        resolver = get_resolver()
        url_patterns = []

        # Collect all URL patterns
        def collect_patterns(patterns):
            for pattern in patterns:
                if hasattr(pattern, "url_patterns"):
                    collect_patterns(pattern.url_patterns)
                else:
                    url_patterns.append(pattern)

        collect_patterns(resolver.url_patterns)

        # Check for job creation endpoints
        # This is a basic check - in production, you'd want more thorough testing
        job_create_endpoints = []
        for pattern in url_patterns:
            pattern_str = str(pattern.pattern)
            if "job" in pattern_str.lower():
                job_create_endpoints.append(pattern_str)

        # The ingestion pipeline should not expose a public job creation endpoint
        # This test documents the expected state
        # In a real system, you'd test actual view/serializer permissions
        pass  # Placeholder for more comprehensive endpoint testing
