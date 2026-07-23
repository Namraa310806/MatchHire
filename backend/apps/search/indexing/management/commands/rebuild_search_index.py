"""
Management command to rebuild search index.

This command rebuilds the search index for specified entity types.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from typing import Optional

from apps.search.registry import get_registry
from apps.search.indexing.index_manager import IndexManager
from apps.search.indexing.bulk_indexer import BulkIndexer
from apps.search.indexing.sync_service import SyncService
from apps.search.indexing.bulk_indexer import BulkIndexStatus
from apps.search.indexing.documents import EntityType
from apps.search.exceptions import SearchError


class Command(BaseCommand):
    help = "Rebuild search index for specified entity types"

    def add_arguments(self, parser):
        parser.add_argument(
            "--entity-type",
            type=str,
            help="Entity type to rebuild (candidate, recruiter, job, resume, application)",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Rebuild all entity types",
        )
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=100,
            help="Number of documents to process per chunk (default: 100)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform a dry run without actually rebuilding",
        )
        parser.add_argument(
            "--progress",
            action="store_true",
            help="Show progress during rebuild",
        )

    def handle(self, *args, **options):
        entity_type = options.get("entity_type")
        rebuild_all = options.get("all")
        chunk_size = options.get("chunk_size")
        dry_run = options.get("dry_run")
        show_progress = options.get("progress")

        # Validate arguments
        if not entity_type and not rebuild_all:
            raise CommandError("Either --entity-type or --all must be specified")

        if entity_type and rebuild_all:
            raise CommandError("Cannot specify both --entity-type and --all")

        # Determine entity types to rebuild
        if rebuild_all:
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

        # Initialize services
        sync_service = SyncService(provider)
        index_manager = IndexManager(provider)
        bulk_indexer = BulkIndexer(sync_service, chunk_size=chunk_size)

        self.stdout.write(self.style.WARNING(f"Starting rebuild at {timezone.now()}"))

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        # Rebuild each entity type
        for entity_type in entity_types:
            self.stdout.write(f"\nRebuilding {entity_type.value} index...")

            if dry_run:
                # Just show what would be done
                from apps.search.indexing.bulk_indexer import BulkIndexer
                temp_indexer = BulkIndexer(sync_service, chunk_size=chunk_size)
                count = temp_indexer._count_documents(entity_type)
                self.stdout.write(f"  Would rebuild {count} documents")
                continue

            try:
                # Rebuild index
                index_manager.rebuild_index(entity_type)

                # Create and execute bulk job
                job = bulk_indexer.create_job(entity_type)

                if show_progress:
                    def progress_callback(job):
                        self.stdout.write(
                            f"  Progress: {job.progress_percentage:.1f}% "
                            f"({job.processed_count}/{job.total_count}) "
                            f"({job.documents_per_second:.1f} docs/sec)"
                        )

                    job = bulk_indexer.execute_job(job, progress_callback=progress_callback)
                else:
                    job = bulk_indexer.execute_job(job)

                # Report results
                if job.status == BulkIndexStatus.COMPLETED:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Successfully rebuilt {job.processed_count} documents "
                            f"in {job.duration:.2f} seconds "
                            f"({job.documents_per_second:.1f} docs/sec)"
                        )
                    )
                    if job.failed_count > 0:
                        self.stdout.write(
                            self.style.WARNING(f"  Failed: {job.failed_count} documents")
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  Rebuild failed: {job.error_message}"
                        )
                    )

            except SearchError as e:
                self.stdout.write(self.style.ERROR(f"  Error: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Unexpected error: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nRebuild completed at {timezone.now()}"))
