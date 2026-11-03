"""Job ingestion pipeline for MatchHire."""

from .pipeline import process_batch
from .record import JobRecord

__all__ = ["JobRecord", "process_batch"]
