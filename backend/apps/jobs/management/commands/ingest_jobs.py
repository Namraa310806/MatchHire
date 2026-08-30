"""
Management command to manually run job ingestion for a specific source.

Usage:
    python manage.py ingest_jobs --source nexus_technologies
    python manage.py ingest_jobs --source nexus_technologies --dry-run
    python manage.py ingest_jobs --source stripe --async

This command is for manual testing and debugging of the ingestion pipeline.
By default, it runs synchronously without Celery.
Use --async to queue the task for asynchronous execution via Celery.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import logging

from apps.companies.models import Company
from apps.jobs.scrapers.nexus_technologies import NexusTechnologiesScraper
from apps.jobs.scrapers.stripe import StripeScraper
from apps.jobs.services.ingestion import JobIngestionService
from apps.jobs.tasks import ingest_jobs_task


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manually run job ingestion for a specific source'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            required=True,
            help='Source identifier (e.g., nexus_technologies, stripe)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run scraper without persisting to database'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Queue the task for asynchronous execution via Celery'
        )

    def handle(self, *args, **options):
        source = options['source']
        dry_run = options['dry_run']
        async_mode = options['async']

        self.stdout.write(f"Starting job ingestion for source: {source}")

        # If async mode, queue the Celery task and return
        if async_mode:
            if dry_run:
                raise CommandError("--dry-run and --async are mutually exclusive")
            
            self.stdout.write("Queueing Celery task for asynchronous execution...")
            try:
                result = ingest_jobs_task.delay(source)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Task queued successfully. Task ID: {result.id}"
                    )
                )
                self.stdout.write(
                    "Monitor task execution with Celery worker logs or Flower."
                )
                return
            except Exception as e:
                logger.error(f"Failed to queue Celery task: {e}", exc_info=True)
                raise CommandError(f"Failed to queue Celery task: {e}")

        # Synchronous execution (existing behavior)
        self.stdout.write("Running synchronous ingestion...")

        # Map source to scraper
        scraper_map = {
            'nexus_technologies': NexusTechnologiesScraper,
            'stripe': StripeScraper,
        }

        if source not in scraper_map:
            raise CommandError(
                f"Unknown source: {source}. "
                f"Available sources: {', '.join(scraper_map.keys())}"
            )

        scraper_class = scraper_map[source]

        try:
            # Resolve company
            # For nexus_technologies: nexus_technologies -> nexus-technologies
            # For stripe: stripe -> stripe (no change)
            if source == 'nexus_technologies':
                company_slug = 'nexus-technologies'
            else:
                company_slug = source
            
            try:
                company = Company.objects.get(slug=company_slug)
                if not company.is_active:
                    raise CommandError(f"Company {company_slug} is not active")
                self.stdout.write(f"Company resolved: {company.name}")
            except Company.DoesNotExist:
                raise CommandError(f"Company not found: {company_slug}")

            # Initialize scraper
            scraper = scraper_class(
                company_slug=company_slug,
                config=company.scraper_config
            )

            # Run scraper
            self.stdout.write("Fetching jobs from source...")
            normalized_jobs = scraper.scrape()

            if not normalized_jobs:
                self.stdout.write(self.style.WARNING("No jobs found"))
                return

            self.stdout.write(f"Normalized {len(normalized_jobs)} jobs")

            # Dry run: just report what would be ingested
            if dry_run:
                self.stdout.write(self.style.WARNING("DRY RUN - No database changes"))
                for job in normalized_jobs:
                    self.stdout.write(
                        f"  - {job.external_id}: {job.title} "
                        f"({job.location or 'N/A'}, {job.employment_type or 'N/A'})"
                    )
                return

            # Ingest to database
            self.stdout.write("Ingesting jobs to database...")
            ingestion_service = JobIngestionService()
            result = ingestion_service.ingest_jobs(normalized_jobs, company_slug)

            # Report results
            self.stdout.write(self.style.SUCCESS("\nIngestion complete"))
            self.stdout.write(f"  Fetched: {result.fetched}")
            self.stdout.write(f"  Normalized: {result.normalized}")
            self.stdout.write(f"  Created: {result.created}")
            self.stdout.write(f"  Updated: {result.updated}")
            self.stdout.write(f"  Skipped: {result.skipped}")
            self.stdout.write(f"  Failed: {result.failed}")

            if result.errors:
                self.stdout.write(self.style.ERROR("\nErrors:"))
                for error in result.errors:
                    self.stdout.write(f"  - {error}")

        except Exception as e:
            logger.error(f"Ingestion command failed: {e}", exc_info=True)
            raise CommandError(f"Ingestion failed: {e}")
