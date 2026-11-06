"""Management command to seed development data.

This command creates a deterministic, fictional dataset for local development,
demonstration, and testing. All data is synthetic and clearly marked as such.

The command:
- Creates 3 fictional companies with ingestion sources
- Creates 2-4 fictional jobs per company via the ingestion pipeline
- Creates 1-2 fictional candidate users with profiles
- Creates skills, work experience, match scores, and application clicks
- Is idempotent (repeated runs do not create duplicates)
- Uses database transactions for safety
- Refuses to run in production environments

IMPORTANT: This command is exclusively for development environments.
It will refuse to run if DEBUG=False (production check).
"""

from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from api.ingestion.pipeline import process_batch
from api.models import (
    ApplicationClick,
    CandidateProfile,
    CandidateSkill,
    Company,
    IngestionSource,
    Job,
    MatchScore,
    Skill,
    WorkExperience,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seed development data (companies, jobs, candidates, profiles, skills)"

    def handle(self, *args, **options):
        """Execute the seed command."""
        # Production safety check
        if not settings.DEBUG:
            raise CommandError(
                "seed_dev_data cannot run in production. "
                "This command is exclusively for development environments."
            )

        self.stdout.write(self.style.WARNING("Seeding development data..."))
        self.stdout.write(
            self.style.WARNING("All data is fictional and for development/testing only.")
        )

        try:
            with transaction.atomic():
                # Seed in stages
                self._seed_skills()
                companies = self._seed_companies()
                self._seed_candidates()
                self._seed_jobs_via_pipeline(companies)
                self._seed_match_scores_and_clicks()

            self.stdout.write(self.style.SUCCESS("Development data seeded successfully."))
            self._print_summary()

        except Exception as e:
            raise CommandError(f"Failed to seed development data: {e}") from e

    def _seed_skills(self) -> None:
        """Seed the skills vocabulary."""
        self.stdout.write("Seeding skills...")

        # Skills used in synthetic jobs and candidate profiles
        skill_names = [
            "Python",
            "Django",
            "JavaScript",
            "React",
            "TypeScript",
            "HTML",
            "CSS",
            "SQL",
            "PostgreSQL",
            "Git",
            "REST APIs",
            "Docker",
            "Kubernetes",
            "AWS",
            "Linux",
            "Testing",
            "Selenium",
            "CI/CD",
            "Excel",
            "Data visualization",
        ]

        created_count = 0
        for skill_name in skill_names:
            skill, created = Skill.objects.get_or_create(
                name=skill_name,
                defaults={"category": "development"},
            )
            if created:
                created_count += 1

        self.stdout.write(f"  Created {created_count} skills.")

    def _seed_companies(self) -> dict[str, tuple[Company, IngestionSource]]:
        """Seed fictional companies and ingestion sources.

        Returns:
            Dictionary mapping company names to (Company, IngestionSource) tuples
        """
        self.stdout.write("Seeding companies and ingestion sources...")

        companies_data = [
            {
                "name": "TechNova Solutions",
                "website": "https://technova.example.invalid",
                "description": "A fictional technology company specializing in web development and cloud solutions.",
            },
            {
                "name": "DataFlow Analytics",
                "website": "https://dataflow.example.invalid",
                "description": "A fictional data analytics company providing insights and visualization services.",
            },
            {
                "name": "CloudScale Systems",
                "website": "https://cloudscale.example.invalid",
                "description": "A fictional cloud infrastructure company offering DevOps and platform services.",
            },
        ]

        result: dict[str, tuple[Company, IngestionSource]] = {}

        for _idx, company_data in enumerate(companies_data, start=1):
            company, created = Company.objects.get_or_create(
                name=company_data["name"],
                defaults={
                    "website": company_data["website"],
                    "description": company_data["description"],
                    "is_active": True,
                },
            )

            source, source_created = IngestionSource.objects.get_or_create(
                company=company,
                base_url=f"https://{company_data['name'].lower().replace(' ', '-')}.example.invalid/jobs",
                defaults={
                    "name": f"{company_data['name']} Career Page",
                    "source_type": "career_page",
                    "scraper_class": "DevSeedScraper",
                    "fetch_interval_hours": 24,
                    "stale_threshold": 3,
                    "is_active": True,
                },
            )

            result[company.name] = (company, source)

            action = "Created" if created else "Reused"
            source_action = "Created" if source_created else "Reused"
            self.stdout.write(
                f"  {action} company: {company.name} ({source_action} source)"
            )

        return result

    def _seed_candidates(self) -> None:
        """Seed fictional candidate users and profiles."""
        self.stdout.write("Seeding candidate users and profiles...")

        candidates_data: list[dict[str, str | Decimal | list[str] | list[dict[str, str]]]] = [
            {
                "email": "candidate1@example.invalid",
                "password": "dev_password_123",  # Insecure by design - development only
                "first_name": "Priya",
                "last_name": "Sharma",
                "location": "Bangalore, India",
                "remote_preference": "hybrid",
                "role_type_preference": "full-time",
                "total_experience_years": Decimal("1.5"),
                "bio": "Fresher with 1.5 years of internship experience in Python and Django development.",
                "skills": ["Python", "Django", "JavaScript", "HTML", "CSS", "Git"],
                "work_experience": [
                    {
                        "company_name": "Internship Company",
                        "role": "Python Developer Intern",
                        "description": "Developed REST APIs using Django REST Framework.",
                        "start_date": "2023-06-01",
                        "end_date": "2023-12-31",
                        "location": "Bangalore, India",
                    }
                ],
            },
            {
                "email": "candidate2@example.invalid",
                "password": "dev_password_456",  # Insecure by design - development only
                "first_name": "Rahul",
                "last_name": "Verma",
                "location": "Mumbai, India",
                "remote_preference": "remote",
                "role_type_preference": "full-time",
                "total_experience_years": Decimal("0.0"),
                "bio": "Fresh graduate with strong fundamentals in data analysis and SQL.",
                "skills": ["Python", "SQL", "Excel", "Data visualization"],
                "work_experience": [],
            },
        ]

        for candidate_data in candidates_data:
            # Create or get user
            user, user_created = User.objects.get_or_create(
                email=candidate_data["email"],
                defaults={
                    "first_name": candidate_data["first_name"],
                    "last_name": candidate_data["last_name"],
                    "is_active": True,
                },
            )

            if user_created:
                user.set_password(candidate_data["password"])
                user.save()

            # Create or get profile
            profile, profile_created = CandidateProfile.objects.get_or_create(
                user=user,
                defaults={
                    "location": candidate_data["location"],
                    "remote_preference": candidate_data["remote_preference"],
                    "role_type_preference": candidate_data["role_type_preference"],
                    "total_experience_years": candidate_data["total_experience_years"],
                    "bio": candidate_data["bio"],
                },
            )

            action = "Created" if user_created else "Reused"
            profile_action = "Created" if profile_created else "Reused"
            self.stdout.write(
                f"  {action} user: {user.email} ({profile_action} profile)"
            )

            # Add skills
            skills = candidate_data.get("skills", [])
            if isinstance(skills, list):
                for skill_name in skills:
                    if isinstance(skill_name, str):
                        try:
                            skill = Skill.objects.get(name=skill_name)
                            CandidateSkill.objects.get_or_create(
                                candidate=profile,
                                skill=skill,
                                defaults={"proficiency": "intermediate"},
                            )
                        except Skill.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(f"    Skill not found: {skill_name}")
                            )

            # Add work experience
            work_experience = candidate_data.get("work_experience", [])
            if isinstance(work_experience, list):
                for work_data in work_experience:
                    if isinstance(work_data, dict):
                        WorkExperience.objects.get_or_create(
                            candidate=profile,
                            company_name=work_data.get("company_name", ""),
                            role=work_data.get("role", ""),
                            defaults={
                                "description": work_data.get("description", ""),
                                "start_date": work_data.get("start_date"),
                                "end_date": work_data.get("end_date"),
                                "location": work_data.get("location", ""),
                            },
                        )

    def _seed_jobs_via_pipeline(self, companies: dict[str, tuple[Company, IngestionSource]]) -> None:
        """Seed jobs through the ingestion pipeline to preserve the job-creation invariant.

        This method uses the DevSeedScraper to generate synthetic job data,
        then routes it through the standard ingestion pipeline. This ensures
        that all jobs enter the system through the approved pathway, even if
        the source is synthetic for development purposes.

        Args:
            companies: Dictionary of company names to (Company, IngestionSource) tuples
        """
        self.stdout.write("Seeding jobs via ingestion pipeline...")

        # Load the DevSeedScraper
        from api.ingestion.scraper_registry import load_scraper

        scraper = load_scraper("DevSeedScraper")

        # Fetch synthetic job data
        raw_jobs = scraper.fetch("ignored")

        # Map source_id and company_id to actual database IDs
        # The scraper uses sequential IDs (1, 2, 3) which we map to actual sources
        source_map = {
            1: companies["TechNova Solutions"][1].id,
            2: companies["DataFlow Analytics"][1].id,
            3: companies["CloudScale Systems"][1].id,
        }

        company_map = {
            1: companies["TechNova Solutions"][0].id,
            2: companies["DataFlow Analytics"][0].id,
            3: companies["CloudScale Systems"][0].id,
        }

        # Update raw job data with actual IDs
        for raw_job in raw_jobs:
            raw_job["source_id"] = source_map[raw_job["source_id"]]
            raw_job["company_id"] = company_map[raw_job["company_id"]]

        # Process through the pipeline (not dry_run - actually persist)
        result = process_batch(raw_jobs, "DevSeedScraper", dry_run=False)

        self.stdout.write(
            f"  Jobs processed: {result.jobs_processed}, "
            f"Created: {result.jobs_created}, "
            f"Updated: {result.jobs_updated}, "
            f"Skipped: {result.jobs_skipped}"
        )

        if result.validation_errors:
            self.stdout.write(
                self.style.WARNING(f"  Validation errors: {len(result.validation_errors)}")
            )

    def _seed_match_scores_and_clicks(self) -> None:
        """Seed match scores and application clicks for synthetic candidates and jobs."""
        self.stdout.write("Seeding match scores and application clicks...")

        # Get all candidates and jobs
        candidates = CandidateProfile.objects.all()
        jobs = Job.objects.all()

        match_count = 0
        click_count = 0

        for candidate in candidates:
            for job in jobs:
                # Create deterministic match score based on candidate email and job title
                # This ensures idempotency - same candidates and jobs get same scores
                base_score = self._compute_deterministic_score(candidate, job)
                final_score = min(base_score + Decimal("0.05"), Decimal("1.0"))  # Small boost

                MatchScore.objects.get_or_create(
                    candidate=candidate,
                    job=job,
                    defaults={
                        "base_score": base_score,
                        "final_score": final_score,
                        "skill_similarity": base_score * Decimal("0.5"),
                        "experience_match": base_score * Decimal("0.3"),
                        "keyword_overlap": base_score * Decimal("0.2"),
                    },
                )
                match_count += 1

                # Create application click for high-scoring matches only
                if final_score >= Decimal("0.7"):
                    ApplicationClick.objects.get_or_create(
                        candidate=candidate,
                        job=job,
                        defaults={
                            "ip_address": "127.0.0.1",
                            "user_agent": "DevSeed/1.0",
                        },
                    )
                    click_count += 1

        self.stdout.write(f"  Created {match_count} match scores.")
        self.stdout.write(f"  Created {click_count} application clicks.")

    def _compute_deterministic_score(self, candidate: CandidateProfile, job: Job) -> Decimal:
        """Compute a deterministic match score for testing.

        This uses a simple hash-based approach to ensure that the same
        candidate-job pair always gets the same score. This is for
        development data only - real matching uses TF-IDF.

        Args:
            candidate: The candidate profile
            job: The job

        Returns:
            A deterministic score between 0.0 and 1.0
        """
        # Simple hash-based score for determinism
        hash_input = f"{candidate.user.email}:{job.title}"
        hash_value = hash(hash_input) % 100
        return Decimal(str(hash_value / 100.0))

    def _print_summary(self) -> None:
        """Print a summary of seeded data."""
        self.stdout.write("\n" + self.style.SUCCESS("=== Seed Data Summary ==="))
        self.stdout.write(f"Companies: {Company.objects.count()}")
        self.stdout.write(f"Ingestion Sources: {IngestionSource.objects.count()}")
        self.stdout.write(f"Jobs: {Job.objects.count()}")
        self.stdout.write(f"Users: {User.objects.count()}")
        self.stdout.write(f"Candidate Profiles: {CandidateProfile.objects.count()}")
        self.stdout.write(f"Skills: {Skill.objects.count()}")
        self.stdout.write(f"Candidate Skills: {CandidateSkill.objects.count()}")
        self.stdout.write(f"Work Experience: {WorkExperience.objects.count()}")
        self.stdout.write(f"Match Scores: {MatchScore.objects.count()}")
        self.stdout.write(f"Application Clicks: {ApplicationClick.objects.count()}")
        self.stdout.write(self.style.SUCCESS("========================"))
