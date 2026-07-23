"""
Search signals.

This module defines Django signals for automatic document indexing
when models are created, updated, or deleted.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.search.config import SearchConfig
from apps.search.registry import get_registry
from apps.search.exceptions import SearchError


def should_index_model(instance) -> bool:
    """
    Check if a model should be indexed.

    Args:
        instance: Model instance

    Returns:
        True if model should be indexed
    """
    # Check if search is enabled for this entity type
    if not SearchConfig.is_feature_enabled("full_text_search"):
        return False

    # Add entity-specific logic here
    return True


@receiver(post_save)
def index_document_on_save(sender, instance, **kwargs):
    """
    Index a document when a model is saved.

    This signal handler automatically indexes documents when
    they are created or updated. For PostgreSQL provider,
    this is a no-op since the database is the source of truth.
    """
    if not should_index_model(instance):
        return

    try:
        registry = get_registry()
        provider_name = registry.get_current_provider()

        if provider_name == "postgresql":
            # PostgreSQL provider doesn't need explicit indexing
            return

        # For future providers (Elasticsearch, etc.), implement indexing here
        # This will be implemented in Phase 5.2

    except SearchError:
        # Log error but don't fail the save operation
        pass


@receiver(post_delete)
def delete_document_on_delete(sender, instance, **kwargs):
    """
    Delete a document from the index when a model is deleted.

    This signal handler automatically removes documents from
    the search index when they are deleted from the database.
    """
    if not should_index_model(instance):
        return

    try:
        registry = get_registry()
        provider_name = registry.get_current_provider()

        if provider_name == "postgresql":
            # PostgreSQL provider doesn't need explicit deletion
            return

        # For future providers (Elasticsearch, etc.), implement deletion here
        # This will be implemented in Phase 5.2

    except SearchError:
        # Log error but don't fail the delete operation
        pass
