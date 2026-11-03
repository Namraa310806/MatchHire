"""Validation and rejection reporting for job records."""

from dataclasses import dataclass
from typing import Literal

from .record import JobRecord


@dataclass
class ValidationError:
    """Represents a validation error for a job record."""

    record: JobRecord | None  # None for parsing/normalization errors where no JobRecord exists
    raw_record: dict[str, object] | None  # Original raw record for attribution
    reason: str
    error_type: Literal["missing_field", "invalid_value", "business_rule", "parsing_error", "normalization_error"]


def validate_job_record(record: JobRecord) -> ValidationError | None:
    """Validate a JobRecord against business rules.

    Validation checks:
    - Required fields are present and non-empty
    - Source ID and company ID are positive
    - External ID (if present) is not empty
    - Title is not empty
    - Description is not empty
    - Application URL is not empty and valid
    - Experience ranges are valid (min <= max if both present)
    - Salary ranges are valid (min <= max if both present)
    - Skills list is not None (empty list is allowed)

    Args:
        record: The JobRecord to validate

    Returns:
        ValidationError if invalid, None if valid
    """
    # Check source ID
    if record.source_id <= 0:
        return ValidationError(
            record=record,
            raw_record=None,
            reason=f"Invalid source_id: {record.source_id} (must be positive)",
            error_type="invalid_value",
        )

    # Check company ID
    if record.company_id <= 0:
        return ValidationError(
            record=record,
            raw_record=None,
            reason=f"Invalid company_id: {record.company_id} (must be positive)",
            error_type="invalid_value",
        )

    # Check external_id (if present)
    if record.external_id is not None and not record.external_id.strip():
        return ValidationError(
            record=record,
            raw_record=None,
            reason="external_id is present but empty",
            error_type="invalid_value",
        )

    # Check title
    if not record.title or not record.title.strip():
        return ValidationError(
            record=record,
            raw_record=None,
            reason="Title is empty",
            error_type="missing_field",
        )

    # Check description
    if not record.description or not record.description.strip():
        return ValidationError(
            record=record,
            raw_record=None,
            reason="Description is empty",
            error_type="missing_field",
        )

    # Check application URL
    if not record.application_url or not record.application_url.strip():
        return ValidationError(
            record=record,
            raw_record=None,
            reason="Application URL is empty",
            error_type="missing_field",
        )

    # Check experience range
    if (
        record.experience_min_years is not None
        and record.experience_max_years is not None
    ):
        if record.experience_min_years > record.experience_max_years:
            return ValidationError(
                record=record,
                raw_record=None,
                reason=f"Invalid experience range: min ({record.experience_min_years}) > max ({record.experience_max_years})",
                error_type="invalid_value",
            )

    # Check salary range
    if record.salary_min is not None and record.salary_max is not None:
        if record.salary_min > record.salary_max:
            return ValidationError(
                record=record,
                raw_record=None,
                reason=f"Invalid salary range: min ({record.salary_min}) > max ({record.salary_max})",
                error_type="invalid_value",
            )

    # Check skills is not None
    if record.skills is None:
        return ValidationError(
            record=record,
            raw_record=None,
            reason="Skills list is None (should be empty list instead)",
            error_type="invalid_value",
        )

    # Check salary currency is not empty if salary fields are present
    if (record.salary_min is not None or record.salary_max is not None) and (
        not record.salary_currency or not record.salary_currency.strip()
    ):
        return ValidationError(
            record=record,
            raw_record=None,
            reason="Salary currency is empty when salary fields are present",
            error_type="missing_field",
        )

    return None
