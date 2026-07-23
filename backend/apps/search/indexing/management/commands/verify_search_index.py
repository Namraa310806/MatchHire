"""
Management command to verify search index integrity.

This command checks for missing documents, extra documents, version mismatches,
orphaned documents, relationship consistency, and synchronization status.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.search.registry import get_registry
from apps.search.indexing.index_manager import IndexManager
from apps.search.indexing.sync_service import SyncService
from apps.search.indexing.verification import IndexVerifier
from apps.search.indexing.documents import EntityType
from apps.search.exceptions import SearchError


class Command(BaseCommand):
    help = "Verify search index integrity"

    def add_arguments(self, parser):
        parser.add_argument(
            "--entity-type",
            type=str,
            help="Entity type to verify (candidate, recruiter, job, resume, application)",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Verify all entity types",
        )
        parser.add_argument(
            "--detailed",
            action="store_true",
            help="Show detailed verification results",
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Attempt to fix issues found (experimental)",
        )

    def handle(self, *args, **options):
        entity_type = options.get("entity_type")
        verify_all = options.get("all")
        detailed = options.get("detailed")
        fix_issues = options.get("fix")

        if not entity_type and not verify_all:
            raise CommandError("Either --entity-type or --all must be specified")

        if entity_type and verify_all:
            raise CommandError("Cannot specify both --entity-type and --all")

        if verify_all:
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

        try:
            registry = get_registry()
            provider = registry.get_provider()
        except Exception as e:
            raise CommandError(f"Failed to get search provider: {e}")

        index_manager = IndexManager(provider)
        verifier = IndexVerifier(index_manager)

        self.stdout.write(self.style.WARNING(f"Starting verification at {timezone.now()}"))

        reports = []
        for target in entity_types:
            self.stdout.write(f"\nVerifying {target.value}...")

            try:
                report = verifier.verify_entity_type(target, detailed=detailed)
                reports.append(report)

                if report.is_healthy:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Healthy ({report.total_db_documents} docs in DB, "
                            f"{report.total_index_documents} docs in index)"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  Issues found: {report.issue_count} "
                            f"(critical={report.critical_count}, warning={report.warning_count}, info={report.info_count})"
                        )
                    )

                    if detailed:
                        for issue in report.issues[:25]:
                            self.stdout.write(
                                f"    - [{issue.severity}] {issue.issue_type} "
                                f"{issue.document_id}: {issue.description}"
                            )
                        remaining = report.issue_count - min(report.issue_count, 25)
                        if remaining > 0:
                            self.stdout.write(f"    ... and {remaining} more")

                    if fix_issues:
                        self._fix_entity_type(target, report, index_manager)

            except SearchError as e:
                self.stdout.write(self.style.ERROR(f"  Error: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Unexpected error: {e}"))

        summary = verifier.get_summary(reports)

        self.stdout.write("\n" + "=" * 60)
        if summary["overall_healthy"]:
            self.stdout.write(
                self.style.SUCCESS(
                    f"All {summary['total_entity_types']} entity types healthy"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Healthy entity types: {summary['healthy_entity_types']}/{summary['total_entity_types']}"
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    f"Issues: total={summary['total_issues']}, "
                    f"critical={summary['critical_issues']}, warning={summary['warning_issues']}"
                )
            )

        self.stdout.write(self.style.SUCCESS(f"\nVerification completed at {timezone.now()}"))

    def _fix_entity_type(self, entity_type: EntityType, report, index_manager: IndexManager) -> None:
        """Best-effort fix strategy for non-healthy entity types."""
        if report.is_healthy:
            return

        self.stdout.write("  Applying best-effort fix via full entity rebuild sync...")

        sync_service = SyncService(index_manager.provider)
        progress = sync_service.sync_full_rebuild(entity_type)

        self.stdout.write(
            self.style.SUCCESS(
                f"  Fix sync complete: {progress.completed}/{progress.total} processed, {progress.failed} failed"
            )
        )
