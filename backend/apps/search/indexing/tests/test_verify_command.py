"""
Tests for verify_search_index management command.
"""

from datetime import datetime
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase

from apps.search.indexing.documents import EntityType
from apps.search.indexing.verification import VerificationIssue, VerificationReport


class TestVerifySearchIndexCommand(TestCase):
    """Test verify_search_index command behavior."""

    @patch("apps.search.indexing.management.commands.verify_search_index.get_registry")
    @patch("apps.search.indexing.management.commands.verify_search_index.IndexVerifier")
    def test_verify_all_runs_and_reports_summary(self, verifier_cls, registry_fn):
        provider = Mock()
        registry = Mock()
        registry.get_provider.return_value = provider
        registry_fn.return_value = registry

        verifier = Mock()
        verifier_cls.return_value = verifier

        report = VerificationReport(
            entity_type=EntityType.CANDIDATE.value,
            total_db_documents=10,
            total_index_documents=10,
            issues=[],
            verified_at=datetime.utcnow(),
        )
        verifier.verify_entity_type.return_value = report
        verifier.get_summary.return_value = {
            "total_entity_types": 5,
            "healthy_entity_types": 5,
            "overall_healthy": True,
            "total_issues": 0,
            "critical_issues": 0,
            "warning_issues": 0,
        }

        call_command("verify_search_index", "--all")

        self.assertTrue(verifier.verify_entity_type.called)
        self.assertTrue(verifier.get_summary.called)

    @patch("apps.search.indexing.management.commands.verify_search_index.get_registry")
    @patch("apps.search.indexing.management.commands.verify_search_index.IndexVerifier")
    def test_verify_with_fix_triggers_rebuild_sync(self, verifier_cls, registry_fn):
        provider = Mock()
        registry = Mock()
        registry.get_provider.return_value = provider
        registry_fn.return_value = registry

        verifier = Mock()
        verifier_cls.return_value = verifier

        issue = VerificationIssue(
            issue_type="missing_document",
            entity_type=EntityType.CANDIDATE.value,
            document_id="user-1",
            description="Missing",
            severity="critical",
            metadata={},
        )

        unhealthy_report = VerificationReport(
            entity_type=EntityType.CANDIDATE.value,
            total_db_documents=10,
            total_index_documents=9,
            issues=[issue],
            verified_at=datetime.utcnow(),
        )

        verifier.verify_entity_type.return_value = unhealthy_report
        verifier.get_summary.return_value = {
            "total_entity_types": 1,
            "healthy_entity_types": 0,
            "overall_healthy": False,
            "total_issues": 1,
            "critical_issues": 1,
            "warning_issues": 0,
        }

        with patch(
            "apps.search.indexing.management.commands.verify_search_index.SyncService"
        ) as sync_cls:
            sync = Mock()
            sync.sync_full_rebuild.return_value = Mock(total=10, completed=10, failed=0)
            sync_cls.return_value = sync

            call_command("verify_search_index", "--entity-type", "candidate", "--fix")

            sync.sync_full_rebuild.assert_called_once_with(EntityType.CANDIDATE)
