"""Job hash computation for content change detection."""

import hashlib

from .record import JobRecord


def compute_job_hash(record: JobRecord) -> str:
    """Compute SHA-256 hash of normalized job content.

    Hash is computed from:
    - title
    - description
    - location
    - skills (sorted, joined with comma)
    - required_yoe

    This hash is used for content change detection, NOT as primary identity.
    The specification (Decision 5) defines this as the job_hash field.

    Args:
        record: The normalized JobRecord to hash

    Returns:
        Hexadecimal SHA-256 hash string (64 characters)
    """
    # Build hash string from specified fields
    hash_parts = [
        record.title.lower(),
        record.description.lower(),
        (record.location or "").lower(),
        ",".join(sorted([s.lower() for s in record.skills])),
        str(record.required_yoe) if record.required_yoe is not None else "",
    ]

    hash_string = "|".join(hash_parts)

    # Compute SHA-256
    hash_bytes = hashlib.sha256(hash_string.encode("utf-8")).hexdigest()

    return hash_bytes


def hash_matches(record1: JobRecord, record2: JobRecord) -> bool:
    """Check if two JobRecords have the same content hash.

    Args:
        record1: First JobRecord
        record2: Second JobRecord

    Returns:
        True if hashes match, False otherwise
    """
    return compute_job_hash(record1) == compute_job_hash(record2)
