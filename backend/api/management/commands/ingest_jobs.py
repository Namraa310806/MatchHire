"""Django management command for job ingestion with dry-run support."""

from django.core.management.base import BaseCommand

from api.ingestion.pipeline import process_batch
from api.ingestion.scraper_registry import load_scraper
from api.models import IngestionSource, Job


class Command(BaseCommand):
    """Management command to ingest jobs from a source.

    Usage:
        python manage.py ingest_jobs --source <source-name> [--dry-run]

    Options:
        --source: Name of the IngestionSource to ingest from
        --dry-run: Preview ingestion without writing to database
    """

    help = "Ingest jobs from a configured source (with optional dry-run)"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--source",
            type=str,
            required=True,
            help="Name of the IngestionSource to ingest from",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview ingestion without writing to database",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        source_name = options["source"]
        dry_run = options["dry_run"]

        self.stdout.write(f"Loading source: {source_name}")

        # Load the IngestionSource
        try:
            source = IngestionSource.objects.get(name=source_name, is_active=True)
        except IngestionSource.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Source '{source_name}' not found or inactive"))
            return

        self.stdout.write(f"Source found: {source.company.name} - {source.name}")
        self.stdout.write(f"Scraper class: {source.scraper_class}")
        self.stdout.write(f"Base URL: {source.base_url}")

        if not source.scraper_class:
            self.stderr.write(self.style.ERROR("Source has no scraper_class configured"))
            return

        # Load the scraper
        try:
            scraper = load_scraper(source.scraper_class)
        except ValueError as e:
            self.stderr.write(self.style.ERROR(f"Failed to load scraper: {e}"))
            return

        self.stdout.write("Scraper loaded successfully")

        # Fetch jobs from the source
        self.stdout.write("Fetching jobs from source...")
        try:
            raw_records = scraper.fetch(source.base_url)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Fetch failed: {e}"))
            return

        self.stdout.write(f"Fetched: {len(raw_records)} jobs")

        if not raw_records:
            self.stdout.write(self.style.WARNING("No jobs found"))
            return

        # Count database state before processing (for dry-run verification)
        if dry_run:
            job_count_before = Job.objects.filter(source=source).count()
            self.stdout.write(f"Existing jobs in database: {job_count_before}")

        # Parse records with source_id and company_id
        for raw_record in raw_records:
            raw_record["_source_id"] = source.id
            raw_record["_company_id"] = source.company_id

        # Process through pipeline
        self.stdout.write("Processing jobs through pipeline...")
        try:
            result = process_batch(raw_records, source.scraper_class, dry_run=dry_run)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Pipeline processing failed: {e}"))
            return

        # Display results
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("INGESTION SUMMARY")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Source: {source.company.name} - {source.name}")
        self.stdout.write(f"Fetched: {len(raw_records)}")
        self.stdout.write(f"Parsed: {result.jobs_processed}")
        self.stdout.write(f"Invalid: {len(result.validation_errors)}")
        self.stdout.write(f"Would create: {result.jobs_created}")
        self.stdout.write(f"Would update: {result.jobs_updated}")
        self.stdout.write(f"Would skip: {result.jobs_skipped}")
        self.stdout.write(f"Skill associations: {result.skill_associations_created}")

        if result.validation_errors:
            self.stdout.write("\nValidation errors:")
            for error in result.validation_errors[:10]:  # Show first 10 errors
                self.stdout.write(f"  - {error.error_type}: {error.reason}")
            if len(result.validation_errors) > 10:
                self.stdout.write(f"  ... and {len(result.validation_errors) - 10} more")

        # Dry-run verification
        if dry_run:
            job_count_after = Job.objects.filter(source=source).count()
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write("DRY-RUN VERIFICATION")
            self.stdout.write("=" * 50)
            self.stdout.write(f"Jobs before: {job_count_before}")
            self.stdout.write(f"Jobs after: {job_count_after}")
            self.stdout.write(f"Jobs added: {job_count_after - job_count_before}")

            if job_count_after == job_count_before:
                self.stdout.write(self.style.SUCCESS("✓ No database writes occurred (dry-run successful)"))
            else:
                self.stderr.write(self.style.ERROR("✗ Database writes occurred (dry-run failed!)"))
        else:
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write("REAL INGESTION")
            self.stdout.write("=" * 50)
            self.stdout.write(self.style.SUCCESS("Jobs written to database"))
