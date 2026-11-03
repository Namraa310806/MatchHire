"""Idempotent persistence for job records."""

from collections import defaultdict
from dataclasses import dataclass

from django.db import transaction

from api.models import IngestionSource, Job, JobSkill, Skill

from .hashing import compute_job_hash
from .record import JobRecord
from .validation import ValidationError


@dataclass
class IngestionResult:
    """Result of a batch ingestion operation."""

    jobs_processed: int
    jobs_created: int
    jobs_updated: int
    jobs_skipped: int
    validation_errors: list[ValidationError]
    skill_associations_created: int


def bulk_upsert_jobs(
    records: list[JobRecord],
) -> IngestionResult:
    """Persist job records with idempotent bulk upsert.

    Behavior:
    - Re-processing the same batch does not create duplicates
    - Existing jobs with same source + external_id are updated if content changed
    - last_seen_at is updated for all existing jobs observed again
    - Duplicate records within batch are handled deterministically (first wins)
    - Skill associations are created/updated without duplicates
    - Invalid records are rejected and counted

    Identity resolution (Decision 5):
    1. Primary: source + external_id (if external_id is not null)
    2. Fallback: application_url (if no external_id)
    3. Last resort: not implemented in Phase 2A (requires manual review)

    Args:
        records: List of normalized JobRecord instances

    Returns:
        IngestionResult with counts and errors
    """
    # Deduplicate records within batch (by source + external_id or application_url)
    deduped_records = _deduplicate_batch(records)

    # Separate valid and invalid records
    valid_records: list[JobRecord] = []
    validation_errors: list[ValidationError] = []

    for record in deduped_records:
        error = _validate_persistence(record)
        if error:
            validation_errors.append(error)
        else:
            valid_records.append(record)

    if not valid_records:
        return IngestionResult(
            jobs_processed=len(records),
            jobs_created=0,
            jobs_updated=0,
            jobs_skipped=len(records),
            validation_errors=validation_errors,
            skill_associations_created=0,
        )

    # Perform upsert in a transaction
    with transaction.atomic():
        result = _perform_upsert(valid_records)

    result.jobs_processed = len(records)
    result.validation_errors = validation_errors

    return result


def _deduplicate_batch(records: list[JobRecord]) -> list[JobRecord]:
    """Deduplicate records within a batch.

    Uses identity resolution (source + external_id or application_url).
    If multiple records have the same identity, the first one wins.

    Args:
        records: List of JobRecord instances

    Returns:
        Deduplicated list (first record per identity)
    """
    seen: dict[str, JobRecord] = {}

    for record in records:
        # Build identity key
        if record.external_id:
            key = f"{record.source_id}:{record.external_id}"
        else:
            key = f"url:{record.application_url}"

        if key not in seen:
            seen[key] = record

    return list(seen.values())


def _validate_persistence(record: JobRecord) -> ValidationError | None:
    """Validate record for persistence (DB-level checks).

    Checks:
    - Source exists
    - Company exists
    - Skills exist in database (if any)

    Args:
        record: The JobRecord to validate

    Returns:
        ValidationError if invalid, None if valid
    """
    from .validation import ValidationError

    # Check source exists
    try:
        IngestionSource.objects.get(id=record.source_id)
    except IngestionSource.DoesNotExist:
        return ValidationError(
            record=record,
            raw_record=None,
            reason=f"Source ID {record.source_id} does not exist",
            error_type="invalid_value",
        )

    # Check company exists
    try:
        # Company model is imported at module level
        from api.models import Company
        Company.objects.get(id=record.company_id)
    except Company.DoesNotExist:
        return ValidationError(
            record=record,
            raw_record=None,
            reason=f"Company ID {record.company_id} does not exist",
            error_type="invalid_value",
        )

    # Check skills exist (if any)
    if record.skills:
        existing_skills = set(
            Skill.objects.filter(name__in=record.skills).values_list("name", flat=True)
        )
        missing_skills = set(record.skills) - existing_skills
        if missing_skills:
            # Log but don't reject - skills not in vocabulary are ignored per Decision 3
            # In production, this would be logged for vocabulary review
            pass

    return None


def _perform_upsert(records: list[JobRecord]) -> IngestionResult:
    """Perform the actual upsert operation.

    Args:
        records: List of valid JobRecord instances

    Returns:
        IngestionResult with counts
    """
    jobs_created = 0
    jobs_updated = 0
    skill_associations_created = 0

    # Group records by source for efficient querying
    records_by_source: dict[int, list[JobRecord]] = defaultdict(list)
    for record in records:
        records_by_source[record.source_id].append(record)

    for source_id, source_records in records_by_source.items():
        # Fetch existing jobs for this source
        existing_jobs = Job.objects.filter(source_id=source_id).select_related("company")

        # Build lookup maps
        existing_by_external_id: dict[str, Job] = {}
        existing_by_url: dict[str, Job] = {}

        for job in existing_jobs:
            if job.external_id:
                existing_by_external_id[job.external_id] = job
            existing_by_url[job.application_url] = job

        # Process each record
        for record in source_records:
            # Find existing job by identity
            existing_job = None
            if record.external_id and record.external_id in existing_by_external_id:
                existing_job = existing_by_external_id[record.external_id]
            elif record.application_url in existing_by_url:
                existing_job = existing_by_url[record.application_url]

            # Compute content hash
            job_hash = compute_job_hash(record)

            if existing_job:
                # Check if content changed
                if existing_job.job_hash != job_hash:
                    # Update existing job
                    _update_job(existing_job, record, job_hash)
                    jobs_updated += 1
                else:
                    # No change, just update last_seen_at
                    existing_job.last_seen_at = existing_job.last_seen_at  # Trigger auto_now
                    existing_job.save(update_fields=["last_seen_at"])
            else:
                # Create new job
                new_job = _create_job(record, job_hash)
                jobs_created += 1

            # Handle skill associations
            skill_count = _upsert_skills(
                existing_job if existing_job else new_job, record.skills
            )
            skill_associations_created += skill_count

    return IngestionResult(
        jobs_processed=0,  # Set by caller
        jobs_created=jobs_created,
        jobs_updated=jobs_updated,
        jobs_skipped=0,
        validation_errors=[],
        skill_associations_created=skill_associations_created,
    )


def _create_job(record: JobRecord, job_hash: str) -> Job:
    """Create a new Job from a JobRecord.

    Args:
        record: The JobRecord
        job_hash: The computed content hash

    Returns:
        Created Job instance
    """
    # Map required_yoe to experience_min_years if experience_min_years is not set
    exp_min = record.experience_min_years
    if exp_min is None and record.required_yoe is not None:
        exp_min = record.required_yoe

    job: Job = Job.objects.create(
        source_id=record.source_id,
        company_id=record.company_id,
        external_id=record.external_id,
        title=record.title,
        description=record.description,
        requirements=record.requirements or "",
        location=record.location,
        remote_type=record.remote_type,
        role_type=record.role_type,
        experience_min_years=exp_min,
        experience_max_years=record.experience_max_years,
        salary_min=record.salary_min,
        salary_max=record.salary_max,
        salary_currency=record.salary_currency,
        application_url=record.application_url,
        posted_date=record.posted_date,
        job_hash=job_hash,
        is_active=True,
    )
    return job


def _update_job(job: Job, record: JobRecord, job_hash: str) -> None:
    """Update an existing Job from a JobRecord.

    Args:
        job: The existing Job instance
        record: The JobRecord with new data
        job_hash: The new content hash
    """
    # Map required_yoe to experience_min_years if experience_min_years is not set
    exp_min = record.experience_min_years
    if exp_min is None and record.required_yoe is not None:
        exp_min = record.required_yoe

    job.title = record.title
    job.description = record.description
    job.requirements = record.requirements or ""
    job.location = record.location
    job.remote_type = record.remote_type
    job.role_type = record.role_type
    job.experience_min_years = exp_min
    job.experience_max_years = record.experience_max_years
    job.salary_min = record.salary_min
    job.salary_max = record.salary_max
    job.salary_currency = record.salary_currency
    job.application_url = record.application_url
    job.posted_date = record.posted_date
    job.job_hash = job_hash
    # last_seen_at is updated by auto_now=True
    job.save()


def _upsert_skills(job: Job, skill_names: list[str]) -> int:
    """Create or update skill associations for a job.

    Removes old skill associations and creates new ones.
    Skills not in the vocabulary are ignored.

    Args:
        job: The Job instance
        skill_names: List of skill names

    Returns:
        Number of skill associations created
    """
    # Get existing skills for this job
    existing_skills = set(
        JobSkill.objects.filter(job=job).values_list("skill__name", flat=True)
    )

    # Get skill objects from database (only those in vocabulary)
    skills_in_db = Skill.objects.filter(name__in=skill_names)
    new_skill_names = {s.name for s in skills_in_db}

    # Remove skills that are no longer present
    skills_to_remove = existing_skills - new_skill_names
    if skills_to_remove:
        JobSkill.objects.filter(job=job, skill__name__in=skills_to_remove).delete()

    # Add new skills
    skills_to_add = new_skill_names - existing_skills
    if skills_to_add:
        skill_objects = Skill.objects.filter(name__in=skills_to_add)
        job_skills = [
            JobSkill(job=job, skill=skill, is_required=True) for skill in skill_objects
        ]
        JobSkill.objects.bulk_create(job_skills)

    return len(skills_to_add)
