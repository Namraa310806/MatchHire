"""Pipeline orchestration for job ingestion."""

from typing import Any

from .experience_extraction import extract_required_yoe
from .normalization import normalize_job_record
from .persistence import IngestionResult, bulk_upsert_jobs
from .record import JobRecord
from .scraper_registry import load_scraper
from .skill_extraction import extract_skills
from .validation import ValidationError, validate_job_record


def process_batch(
    raw_records: list[dict[str, Any]],
    scraper_class: str,
    dry_run: bool = False,
) -> IngestionResult:
    """Process a batch of raw job records through the ingestion pipeline.

    Pipeline stages:
    1. Parse raw records into JobRecord (using scraper)
    2. Normalize records (HTML, whitespace, etc.)
    3. Extract skills from descriptions
    4. Extract required years of experience
    5. Validate records
    6. Persist records with idempotent upsert (skipped if dry_run=True)

    Args:
        raw_records: List of raw job data dictionaries (source-specific format)
        scraper_class: Name of the scraper class to use for parsing
        dry_run: If True, skip persistence stage and return summary only

    Returns:
        IngestionResult with counts and validation errors
    """
    # Load scraper
    scraper = load_scraper(scraper_class)

    # Track all errors across stages
    all_errors: list[ValidationError] = []

    # Stage 1: Parse raw records (scraper takes entire list and isolates failures)
    parsed_records = scraper.parse(raw_records)

    # Collect any parsing errors from the scraper (base class contract)
    for raw_record, error_msg in scraper.parse_errors:
        all_errors.append(
            ValidationError(
                record=None,
                raw_record=raw_record,
                reason=f"Parsing failed: {error_msg}",
                error_type="parsing_error",
            )
        )

    if not parsed_records and not all_errors:
        # No records and no errors (empty input)
        return IngestionResult(
            jobs_processed=len(raw_records),
            jobs_created=0,
            jobs_updated=0,
            jobs_skipped=len(raw_records),
            validation_errors=[],
            skill_associations_created=0,
        )

    # Stage 2: Normalize
    normalized_records: list[JobRecord] = []
    for record in parsed_records:
        try:
            normalized = normalize_job_record(record)
            normalized_records.append(normalized)
        except Exception as e:
            # Record normalization error with attribution to parsed record
            all_errors.append(
                ValidationError(
                    record=record,
                    raw_record=None,
                    reason=f"Normalization failed: {str(e)}",
                    error_type="normalization_error",
                )
            )

    if not normalized_records:
        # All records failed normalization
        return IngestionResult(
            jobs_processed=len(raw_records),
            jobs_created=0,
            jobs_updated=0,
            jobs_skipped=len(raw_records),
            validation_errors=all_errors,
            skill_associations_created=0,
        )

    # Stage 3: Extract skills
    for record in normalized_records:
        record.skills = extract_skills(record.description)

    # Stage 4: Extract experience
    for record in normalized_records:
        record.required_yoe = extract_required_yoe(record.description)

    # Stage 5: Validate
    valid_records: list[JobRecord] = []
    validation_errors = []

    for record in normalized_records:
        error = validate_job_record(record)
        if error:
            validation_errors.append(error)
        else:
            valid_records.append(record)

    # Stage 6: Persist (skip if dry_run)
    if dry_run:
        # Read-only comparison to calculate create/update/skip counts
        from api.models import Job

        from .hashing import compute_job_hash

        jobs_created = 0
        jobs_updated = 0
        jobs_skipped = 0

        for record in valid_records:
            # Try to find existing job by identity
            existing_job = None
            if record.external_id:
                existing_job = Job.objects.filter(
                    source_id=record.source_id,
                    external_id=record.external_id
                ).first()
            else:
                existing_job = Job.objects.filter(
                    source_id=record.source_id,
                    application_url=record.application_url
                ).first()

            if existing_job:
                # Check if content changed
                new_hash = compute_job_hash(record)
                if existing_job.job_hash != new_hash:
                    jobs_updated += 1
                else:
                    jobs_skipped += 1
            else:
                jobs_created += 1

        result = IngestionResult(
            jobs_processed=len(raw_records),
            jobs_created=jobs_created,
            jobs_updated=jobs_updated,
            jobs_skipped=jobs_skipped + len(raw_records) - len(valid_records),
            validation_errors=[],
            skill_associations_created=0,
        )
    else:
        result = bulk_upsert_jobs(valid_records)

    result.validation_errors.extend(all_errors)
    result.validation_errors.extend(validation_errors)

    return result
