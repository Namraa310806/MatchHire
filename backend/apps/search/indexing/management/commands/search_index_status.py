"""
Management command to show search index status.

This command displays the current status of search indices including
document counts, health status, and synchronization information.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from typing import Optional

from apps.search.registry import get_registry
from apps.search.indexing.index_manager import IndexManager
from apps.search.indexing.sync_service import SyncService
from apps.search.indexing.bulk_indexer import BulkIndexer
from apps.search.indexing.metrics import get_metrics
from apps.search.indexing.documents import EntityType
from apps.search.exceptions import SearchError


class Command(BaseCommand):
    help = "Show search index status"

    def add_arguments(self, parser):
        parser.add_argument(
            "--entity-type",
            type=str,
            help="Entity type to show status for (candidate, recruiter, job, resume, application)",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Show status for all entity types",
        )
        parser.add_argument(
            "--metrics",
            action="store_true",
            help="Show detailed metrics",
        )
        parser.add_argument(
            "--jobs",
            action="store_true",
            help="Show bulk indexing job status",
        )

    def handle(self, *args, **options):
        entity_type = options.get("entity_type")
        show_all = options.get("all")
        show_metrics = options.get("metrics")
        show_jobs = options.get("jobs")

        # Validate arguments
        if not entity_type and not show_all:
            raise CommandError("Either --entity-type or --all must be specified")

        if entity_type and show_all:
            raise CommandError("Cannot specify both --entity-type and --all")

        # Determine entity types to show
        if show_all:
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
            provider_name = registry.get_current_provider()
        except Exception as e:
            raise CommandError(f"Failed to get search provider: {e}")

        # Initialize services
        index_manager = IndexManager(provider)
        sync_service = SyncService(provider)
        bulk_indexer = BulkIndexer(sync_service)
        metrics = get_metrics()

        # Show provider information
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Search Index Status"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"Provider: {provider_name}")
        self.stdout.write(f"Timestamp: {timezone.now()}")
        self.stdout.write("")

        # Show entity type status
        for entity_type in entity_types:
            self.stdout.write(self.style.WARNING(f"\n{entity_type.value.upper()}"))
            self.stdout.write("-" * 40)

            try:
                # Get document counts
                db_count = bulk_indexer._count_documents(entity_type)
                self.stdout.write(f"Database documents: {db_count}")

                # Get index statistics
                stats = index_manager.get_statistics(entity_type)
                self.stdout.write(f"Index documents: {stats.get('document_count', 'N/A')}")

                # Get health status
                health = index_manager.health_check(entity_type)
                self.stdout.write(f"Health status: {health.get('status', 'unknown')}")

                # Get sync metrics
                doc_metrics = metrics.get_document_metrics(entity_type.value)
                if doc_metrics:
                    self.stdout.write(f"Indexed: {doc_metrics.get('indexed', 0)}")
                    self.stdout.write(f"Synced: {doc_metrics.get('synced', 0)}")
                    self.stdout.write(f"Failed syncs: {doc_metrics.get('failed_syncs', 0)}")
                    self.stdout.write(f"Sync success rate: {doc_metrics.get('sync_success_rate', 0):.2%}")

            except SearchError as e:
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Unexpected error: {e}"))

        # Show detailed metrics if requested
        if show_metrics:
            self.stdout.write(self.style.WARNING(f"\n{'='*60}"))
            self.stdout.write(self.style.WARNING("DETAILED METRICS"))
            self.stdout.write(self.style.WARNING("=" * 60))

            # Show operation metrics
            op_metrics = metrics.get_operation_metrics()
            if op_metrics:
                self.stdout.write("\nOperation Metrics:")
                for op, entity_metrics in op_metrics.items():
                    self.stdout.write(f"  {op}:")
                    for entity_type, metrics_data in entity_metrics.items():
                        self.stdout.write(f"    {entity_type}:")
                        self.stdout.write(f"      Count: {metrics_data.get('count', 0)}")
                        self.stdout.write(f"      Failures: {metrics_data.get('failures', 0)}")
                        self.stdout.write(f"      Avg duration: {metrics_data.get('avg_duration', 0):.3f}s")
                        self.stdout.write(f"      Success rate: {metrics_data.get('success_rate', 0):.2%}")

            # Show queue metrics
            queue_metrics = metrics.get_queue_metrics()
            if queue_metrics:
                self.stdout.write("\nQueue Metrics:")
                for queue_name, queue_data in queue_metrics.items():
                    self.stdout.write(f"  {queue_name}:")
                    self.stdout.write(f"    Current size: {queue_data.get('current_size', 0)}")
                    self.stdout.write(f"    Total processed: {queue_data.get('total_processed', 0)}")

            # Show provider metrics
            provider_metrics = metrics.get_provider_metrics()
            if provider_metrics:
                self.stdout.write("\nProvider Metrics:")
                for provider_name, provider_data in provider_metrics.items():
                    self.stdout.write(f"  {provider_name}:")
                    self.stdout.write(f"    Avg latency: {provider_data.get('avg_latency', 0):.3f}s")
                    self.stdout.write(f"    Min latency: {provider_data.get('min_latency', 0):.3f}s")
                    self.stdout.write(f"    Max latency: {provider_data.get('max_latency', 0):.3f}s")
                    self.stdout.write(f"    Request count: {provider_data.get('request_count', 0)}")

            # Show summary metrics
            summary = metrics.get_summary()
            self.stdout.write("\nSummary:")
            self.stdout.write(f"  Uptime: {summary.get('uptime_seconds', 0):.2f}s")
            self.stdout.write(f"  Total documents indexed: {summary.get('total_documents_indexed', 0)}")
            self.stdout.write(f"  Total documents synced: {summary.get('total_documents_synced', 0)}")
            self.stdout.write(f"  Total sync failures: {summary.get('total_sync_failures', 0)}")
            self.stdout.write(f"  Overall sync success rate: {summary.get('overall_sync_success_rate', 0):.2%}")
            self.stdout.write(f"  Documents per second: {summary.get('documents_per_second', 0):.2f}")

        # Show bulk indexing jobs if requested
        if show_jobs:
            self.stdout.write(self.style.WARNING(f"\n{'='*60}"))
            self.stdout.write(self.style.WARNING("BULK INDEXING JOBS"))
            self.stdout.write(self.style.WARNING("=" * 60))

            jobs = bulk_indexer.list_jobs()
            if jobs:
                for job in jobs:
                    self.stdout.write(f"\nJob ID: {job.job_id}")
                    self.stdout.write(f"  Entity type: {job.entity_type.value}")
                    self.stdout.write(f"  Status: {job.status.value}")
                    self.stdout.write(f"  Progress: {job.progress_percentage:.1f}%")
                    self.stdout.write(f"  Processed: {job.processed_count}/{job.total_count}")
                    self.stdout.write(f"  Failed: {job.failed_count}")
                    self.stdout.write(f"  Duration: {job.duration:.2f}s")
                    self.stdout.write(f"  Docs/sec: {job.documents_per_second:.1f}")
                    if job.start_time:
                        self.stdout.write(f"  Started: {job.start_time}")
                    if job.end_time:
                        self.stdout.write(f"  Ended: {job.end_time}")
                    if job.error_message:
                        self.stdout.write(self.style.ERROR(f"  Error: {job.error_message}"))
            else:
                self.stdout.write("No bulk indexing jobs found")

            # Show dead letter queue
            dead_letter = sync_service.get_dead_letter_queue()
            if dead_letter:
                self.stdout.write(self.style.WARNING(f"\nDead Letter Queue: {len(dead_letter)} items"))
                for item in dead_letter[:5]:
                    self.stdout.write(f"  {item.entity_type}:{item.document_id} - {item.status.value}")
                if len(dead_letter) > 5:
                    self.stdout.write(f"  ... and {len(dead_letter) - 5} more")
            else:
                self.stdout.write("\nDead letter queue is empty")

        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
