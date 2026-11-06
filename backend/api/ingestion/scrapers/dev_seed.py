"""Development seed scraper for synthetic job data.

This scraper generates deterministic, fictional job records for local development
and testing. It does not perform real network requests - it returns pre-defined
synthetic data that routes through the existing ingestion pipeline.

This preserves the job-creation invariant: all jobs still enter through the
scraper → parse → normalize → validate → persist pipeline, even if the source
is synthetic for development purposes.
"""

from datetime import date
from typing import Any

from api.ingestion.base_scraper import BaseJobScraper
from api.ingestion.record import JobRecord


class DevSeedScraper(BaseJobScraper):
    """Development seed scraper for synthetic job generation.

    This scraper is exclusively for local development and testing.
    It generates deterministic, fictional job data that routes through
    the standard ingestion pipeline to preserve the job-creation invariant.

    All generated data is clearly synthetic (example.com domains, fictional
    companies, fictional job titles). No real company data is used.
    """

    def fetch(self, url: str) -> list[dict[str, Any]]:
        """Fetch synthetic job data (no network request).

        Args:
            url: Ignored (method signature required by base class)

        Returns:
            List of synthetic job data dictionaries in a format compatible
            with the parse() method. The data includes fictional companies,
            job titles, and clearly synthetic URLs.

        Note:
            This method does not perform real network requests.
            The URL parameter is ignored but kept for interface compatibility.
        """
        # Return synthetic job data
        # All companies are fictional
        # All URLs use example.com (reserved for documentation/examples)
        return [
            {
                "source_id": 1,  # Will be mapped to actual IngestionSource by command
                "company_id": 1,  # Will be mapped to actual Company by command
                "external_id": "dev-seed-job-001",
                "title": "Junior Software Engineer",
                "description": "Join our fictional team to build innovative solutions. We are looking for a junior engineer with Python and Django experience. You will work on web applications, APIs, and backend systems.",
                "requirements": "Python, Django, PostgreSQL, Git, REST APIs",
                "location": "Bangalore, India",
                "remote_type": "hybrid",
                "role_type": "full-time",
                "experience_min_years": 0,
                "experience_max_years": 2,
                "salary_min": 600000,
                "salary_max": 900000,
                "salary_currency": "INR",
                "application_url": "https://example.invalid/apply/dev-seed-job-001",
                "posted_date": "2024-01-15",
            },
            {
                "source_id": 1,
                "company_id": 1,
                "external_id": "dev-seed-job-002",
                "title": "Frontend Developer (React)",
                "description": "We are seeking a frontend developer to build modern user interfaces. You will work with React, TypeScript, and modern CSS frameworks to create responsive web applications.",
                "requirements": "React, JavaScript, TypeScript, HTML, CSS",
                "location": "Mumbai, India",
                "remote_type": "remote",
                "role_type": "full-time",
                "experience_min_years": 1,
                "experience_max_years": 3,
                "salary_min": 700000,
                "salary_max": 1000000,
                "salary_currency": "INR",
                "application_url": "https://example.invalid/apply/dev-seed-job-002",
                "posted_date": "2024-02-01",
            },
            {
                "source_id": 2,
                "company_id": 2,
                "external_id": "dev-seed-job-003",
                "title": "Data Analyst Intern",
                "description": "Join our data team as an intern. You will work on data cleaning, analysis, and visualization projects using Python and SQL. Great opportunity for fresh graduates.",
                "requirements": "Python, SQL, Excel, Data visualization",
                "location": "Hyderabad, India",
                "remote_type": "on-site",
                "role_type": "internship",
                "experience_min_years": 0,
                "experience_max_years": 1,
                "salary_min": 15000,
                "salary_max": 25000,
                "salary_currency": "INR",
                "application_url": "https://example.invalid/apply/dev-seed-job-003",
                "posted_date": "2024-03-10",
            },
            {
                "source_id": 2,
                "company_id": 2,
                "external_id": "dev-seed-job-004",
                "title": "Backend Developer (Python)",
                "description": "We are looking for a backend developer to build scalable APIs and microservices. You will work with Python, Django, PostgreSQL, and Redis. Experience with cloud platforms is a plus.",
                "requirements": "Python, Django, PostgreSQL, Redis, REST APIs",
                "location": "Pune, India",
                "remote_type": "hybrid",
                "role_type": "full-time",
                "experience_min_years": 2,
                "experience_max_years": 4,
                "salary_min": 800000,
                "salary_max": 1200000,
                "salary_currency": "INR",
                "application_url": "https://example.invalid/apply/dev-seed-job-004",
                "posted_date": "2024-04-05",
            },
            {
                "source_id": 3,
                "company_id": 3,
                "external_id": "dev-seed-job-005",
                "title": "DevOps Engineer",
                "description": "Join our infrastructure team to build and maintain CI/CD pipelines. You will work with Docker, Kubernetes, AWS, and monitoring tools. Experience with infrastructure as code is required.",
                "requirements": "Docker, Kubernetes, AWS, CI/CD, Linux",
                "location": "Chennai, India",
                "remote_type": "remote",
                "role_type": "full-time",
                "experience_min_years": 2,
                "experience_max_years": 5,
                "salary_min": 900000,
                "salary_max": 1400000,
                "salary_currency": "INR",
                "application_url": "https://example.invalid/apply/dev-seed-job-005",
                "posted_date": "2024-05-20",
            },
            {
                "source_id": 3,
                "company_id": 3,
                "external_id": "dev-seed-job-006",
                "title": "QA Engineer",
                "description": "We are seeking a QA engineer to ensure software quality. You will design and execute test plans, automate tests, and work with the development team to identify and fix bugs.",
                "requirements": "Testing, Selenium, Python, CI/CD",
                "location": "Delhi, India",
                "remote_type": "on-site",
                "role_type": "full-time",
                "experience_min_years": 1,
                "experience_max_years": 3,
                "salary_min": 500000,
                "salary_max": 800000,
                "salary_currency": "INR",
                "application_url": "https://example.invalid/apply/dev-seed-job-006",
                "posted_date": "2024-06-15",
            },
        ]

    def parse(self, raw: list[dict[str, Any]]) -> list[JobRecord]:
        """Parse synthetic job data into JobRecord instances.

        Args:
            raw: List of synthetic job data dictionaries from fetch()

        Returns:
            List of normalized JobRecord instances

        Note:
            This method is idempotent - the same input always produces
            the same output. Errors are recorded via _record_parse_error().
        """
        self._clear_parse_errors()
        parsed_records: list[JobRecord] = []

        for raw_record in raw:
            try:
                # Convert date string to date object
                posted_date = None
                if raw_record.get("posted_date"):
                    posted_date = date.fromisoformat(raw_record["posted_date"])

                record = JobRecord(
                    source_id=raw_record["source_id"],
                    company_id=raw_record["company_id"],
                    external_id=raw_record.get("external_id"),
                    title=raw_record["title"],
                    description=raw_record["description"],
                    requirements=raw_record.get("requirements"),
                    location=raw_record.get("location"),
                    application_url=raw_record["application_url"],
                    posted_date=posted_date,
                    remote_type=raw_record.get("remote_type"),
                    role_type=raw_record.get("role_type"),
                    experience_min_years=raw_record.get("experience_min_years"),
                    experience_max_years=raw_record.get("experience_max_years"),
                    salary_min=raw_record.get("salary_min"),
                    salary_max=raw_record.get("salary_max"),
                    salary_currency=raw_record.get("salary_currency", "INR"),
                    skills=[],  # Will be extracted by pipeline
                    required_yoe=None,  # Will be extracted by pipeline
                )
                parsed_records.append(record)
            except Exception as e:
                self._record_parse_error(raw_record, str(e))

        return parsed_records

    def validate(self, job: JobRecord) -> bool:
        """Validate a parsed JobRecord.

        Args:
            job: The JobRecord to validate

        Returns:
            True if valid, False otherwise

        Note:
            This performs basic validation. The ingestion pipeline
            will perform additional validation.
        """
        # Basic validation - the pipeline will perform more thorough checks
        if not job.title or not job.description or not job.application_url:
            return False
        if job.source_id <= 0 or job.company_id <= 0:
            return False
        return True
