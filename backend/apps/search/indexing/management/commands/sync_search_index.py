"""
Management command to sync search index.

This command synchronizes the search index with database changes.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta
from typing import Optional

from apps.search.registry import get_registry
from apps.search.indexing.sync_service import SyncService
from apps.search.indexing.documents import EntityType
from apps.search.exceptions import SearchError


class Command(BaseCommand):
    help = "Synchronize search index with database changes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--entity-type",
            type=str,
            help="Entity type to sync (candidate, recruiter, job, resume, application)",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Sync all entity types",
        )
        parser.add_argument(
            "--since",
            type=str,
            help="Sync changes since this timestamp (ISO format or '1h', '1d', etc.)",
        )
        parser.add_argument(
            "--full",
            action="store_true",
            help="Perform a full sync (all documents)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform a dry run without actually syncing",
        )
        parser.add_argument(
            "--progress",
            action="store_true",
            help="Show progress during sync",
        )
        parser.add_argument(
            "--retry-dead-letter",
            action="store_true",
            help="Retry failed dead-letter items after sync",
        )

    def handle(self, *args, **options):
        entity_type = options.get("entity_type")
        sync_all = options.get("all")
        since_str = options.get("since")
        full_sync = options.get("full")
        dry_run = options.get("dry_run")
        show_progress = options.get("progress")
        retry_dead_letter = options.get("retry_dead_letter")

        # Validate arguments
        if not entity_type and not sync_all:
            raise CommandError("Either --entity-type or --all must be specified")

        if entity_type and sync_all:
            raise CommandError("Cannot specify both --entity-type and --all")

        if since_str and full_sync:
            raise CommandError("Cannot specify both --since and --full")

        # Parse since timestamp
        since = None
        if since_str:
            since = self._parse_since(since_str)

        # Determine entity types to sync
        if sync_all:
            entity_types = [
                EntityType.CANDIDATE,
                EntityType.RECRUITER,
                EntityType.JOB,
                EntityType.RESUME,
                EntityType.APPLICATION,
            ]
        else:
            try:
                entity_types = [EntityType(entity_type.lower())]
            except ValueError:
                valid_types = [e.value for e in EntityType]
                raise CommandError(
                    f"Invalid entity type '{entity_type}'. "
                    f"Valid types: {', '.join(valid_types)}"
                )

        # Get provider
        try:
            registry = get_registry()
            provider = registry.get_provider()
        except Exception as e:
            raise CommandError(f"Failed to get search provider: {e}")

        # Initialize sync service
        sync_service = SyncService(provider)

        self.stdout.write(self.style.WARNING(f"Starting sync at {timezone.now()}"))

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        if full_sync:
            self.stdout.write("Performing full sync (all documents)")
        elif since:
            self.stdout.write(f"Syncing changes since {since}")
        else:
            self.stdout.write("Syncing recent changes (default: last 1 hour)")

        # Sync each entity type
        for entity_type in entity_types:
            self.stdout.write(f"\nSyncing {entity_type.value}...")

            if dry_run:
                # Just show what would be done
                if full_sync:
                    from apps.search.indexing.bulk_indexer import BulkIndexer
                    temp_indexer = BulkIndexer(sync_service)
                    count = temp_indexer._count_documents(entity_type)
                    self.stdout.write(f"  Would sync {count} documents")
                else:
                    if since is None:
                        since = timezone.now() - timedelta(hours=1)
                    documents = sync_service._get_documents_since(entity_type, since)
                    self.stdout.write(f"  Would sync {len(documents)} documents")
                continue

            try:
                if full_sync:
                    # Perform full sync
                    progress = sync_service.sync_full_rebuild(entity_type)
                else:
                    # Perform incremental sync
                    if since is None:
                        since = timezone.now() - timedelta(hours=1)
                    progress = sync_service.sync_incremental(entity_type, since)

                # Report results
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Synced {progress.completed} documents "
                        f"in {progress.duration:.2f} seconds "
                        f"({progress.documents_per_second:.1f} docs/sec)"
                    )
                )
                if progress.failed > 0:
                    self.stdout.write(
                        self.style.WARNING(f"  Failed: {progress.failed} documents")
                    )

            except SearchError as e:
                self.stdout.write(self.style.ERROR(f"  Error: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Unexpected error: {e}"))

        # Check dead letter queue
        dead_letter = sync_service.get_dead_letter_queue()
        if dead_letter:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDead letter queue contains {len(dead_letter)} failed items"
                )
            )

            if retry_dead_letter and not dry_run:
                retried = sync_service.retry_dead_letter_queue()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Retried {len(retried)} dead-letter items"
                    )
                )
            elif retry_dead_letter and dry_run:
                self.stdout.write("Dry run: skipping dead-letter retry")
            else:
                self.stdout.write("Run with --retry-dead-letter to retry failed items")

        self.stdout.write(self.style.SUCCESS(f"\nSync completed at {timezone.now()}"))

    def _parse_since(self, since_str: str) -> datetime:
        """
        Parse a timestamp string into a datetime object.
        
        Args:
            since_str: Timestamp string (ISO format or relative like '1h', '1d')
            
        Returns:
            Datetime object
        """
        # Try ISO format first
        try:
            return datetime.fromisoformat(since_str)
        except ValueError:
            pass

        # Try relative format
        if since_str.endswith("h"):
            hours = int(since_str[:-1])
            return timezone.now() - timedelta(hours=hours)
        elif since_str.endswith("d"):
            days = int(since_str[:-1])
            return timezone.now() - timedelta(days=days)
        elif since_str.endswith("m"):
            minutes = int(since_str[:-1])
            return timezone.now() - timedelta(minutes=minutes)

        raise CommandError(
            f"Invalid timestamp format '{since_str}'. "
            "Use ISO format (e.g., '2024-01-01T00:00:00') or relative (e.g., '1h', '1d')"
        )
