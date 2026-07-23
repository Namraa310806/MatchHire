"""
Event handlers for search indexing.

This module implements Django signal handlers for automatic document indexing
when models are created, updated, or deleted. It uses lightweight signals as
triggers and keeps business logic independent.
"""

from typing import Optional
import logging

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Model

from apps.search.config import SearchConfig
from apps.search.registry import get_registry
from apps.search.indexing.serializers import (
    CandidateSerializer,
    RecruiterSerializer,
    JobSerializer,
    ResumeSerializer,
    ApplicationSerializer,
)
from apps.search.indexing.sync_service import SyncService
from apps.search.exceptions import SearchError

logger = logging.getLogger(__name__)


# Global sync service instance (initialized on first use)
_sync_service: Optional[SyncService] = None


def get_sync_service() -> SyncService:
    """
    Get or create the sync service instance.
    
    Returns:
        SyncService instance
    """
    global _sync_service
    
    if _sync_service is None:
        try:
            registry = get_registry()
            provider = registry.get_provider()
            _sync_service = SyncService(provider)
        except Exception as e:
            logger.error(f"Failed to initialize sync service: {e}")
            raise
    
    return _sync_service


def should_index_model(instance: Model) -> bool:
    """
    Check if a model should be indexed.
    
    Args:
        instance: Model instance
        
    Returns:
        True if model should be indexed
    """
    # Check if search is enabled
    if not SearchConfig.is_feature_enabled("full_text_search"):
        return False
    
    # Check if auto-indexing is enabled
    if not SearchConfig.is_feature_enabled("auto_indexing"):
        return False
    
    # Check if the model is indexable
    model_class = instance.__class__.__name__
    indexable_models = {
        "User",
        "CandidateProfile",
        "RecruiterProfile",
        "Job",
        "ResumeVersion",
        "Application",
    }
    
    return model_class in indexable_models


@receiver(post_save)
def handle_post_save(sender, instance, created, **kwargs):
    """
    Handle post_save signal for document indexing.
    
    This signal handler automatically indexes documents when
    they are created or updated.
    
    Args:
        sender: Model class
        instance: Model instance
        created: Whether this was a create operation
    """
    if not should_index_model(instance):
        return
    
    try:
        sync_service = get_sync_service()
        
        # Route to appropriate serializer based on model type
        from apps.users.models import User, CandidateProfile, RecruiterProfile
        from apps.jobs.models import Job
        from apps.resumes.models import ResumeVersion
        from apps.applications.models import Application
        
        if isinstance(instance, User):
            if instance.role == User.Roles.CANDIDATE:
                document = CandidateSerializer.serialize_from_user(instance)
                sync_service.sync_single_document(document)
            elif instance.role == User.Roles.RECRUITER:
                document = RecruiterSerializer.serialize_from_user(instance)
                sync_service.sync_single_document(document)
        
        elif isinstance(instance, CandidateProfile):
            # Index the associated user
            document = CandidateSerializer.serialize(instance.user, instance)
            sync_service.sync_single_document(document)
        
        elif isinstance(instance, RecruiterProfile):
            # Index the associated user
            document = RecruiterSerializer.serialize(instance.user, instance)
            sync_service.sync_single_document(document)
        
        elif isinstance(instance, Job):
            document = JobSerializer.serialize(instance)
            sync_service.sync_single_document(document)
        
        elif isinstance(instance, ResumeVersion):
            # Only index current versions
            if instance.is_current:
                document = ResumeSerializer.serialize(instance)
                sync_service.sync_single_document(document)
        
        elif isinstance(instance, Application):
            document = ApplicationSerializer.serialize(instance)
            sync_service.sync_single_document(document)
        
    except SearchError as e:
        # Log error but don't fail the save operation
        logger.error(f"Failed to index document on save: {e}")
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error during indexing on save: {e}")


@receiver(post_delete)
def handle_post_delete(sender, instance, **kwargs):
    """
    Handle post_delete signal for document deletion.
    
    This signal handler automatically removes documents from
    the search index when they are deleted from the database.
    
    Args:
        sender: Model class
        instance: Model instance
    """
    if not should_index_model(instance):
        return
    
    try:
        sync_service = get_sync_service()
        
        # Route to appropriate entity type based on model type
        from apps.users.models import User, CandidateProfile, RecruiterProfile
        from apps.jobs.models import Job
        from apps.resumes.models import ResumeVersion
        from apps.applications.models import Application
        from apps.search.indexing.documents import EntityType
        
        entity_type = None
        document_id = None
        
        if isinstance(instance, User):
            if instance.role == User.Roles.CANDIDATE:
                entity_type = EntityType.CANDIDATE
            elif instance.role == User.Roles.RECRUITER:
                entity_type = EntityType.RECRUITER
            document_id = str(instance.id)
        
        elif isinstance(instance, CandidateProfile):
            entity_type = EntityType.CANDIDATE
            document_id = str(instance.user_id)
        
        elif isinstance(instance, RecruiterProfile):
            entity_type = EntityType.RECRUITER
            document_id = str(instance.user_id)
        
        elif isinstance(instance, Job):
            entity_type = EntityType.JOB
            document_id = str(instance.id)
        
        elif isinstance(instance, ResumeVersion):
            entity_type = EntityType.RESUME
            document_id = str(instance.id)
        
        elif isinstance(instance, Application):
            entity_type = EntityType.APPLICATION
            document_id = str(instance.id)
        
        if entity_type and document_id:
            sync_service.delete_document(document_id, entity_type)
        
    except SearchError as e:
        # Log error but don't fail the delete operation
        logger.error(f"Failed to delete document from index: {e}")
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error during indexing on delete: {e}")


@receiver(pre_save)
def handle_pre_save(sender, instance, **kwargs):
    """
    Handle pre_save signal for tracking changes.
    
    This signal handler tracks field changes before save to determine
    if re-indexing is necessary.
    
    Args:
        sender: Model class
        instance: Model instance
    """
    if not should_index_model(instance):
        return
    
    # Store original values for change detection
    if instance.pk:
        try:
            from apps.users.models import User
            from apps.jobs.models import Job
            
            if isinstance(instance, User):
                # Store original values for User
                instance._index_original_values = {
                    field.name: getattr(instance, field.name)
                    for field in instance._meta.fields
                }
            
            elif isinstance(instance, Job):
                # Store original values for Job
                instance._index_original_values = {
                    field.name: getattr(instance, field.name)
                    for field in instance._meta.fields
                }
            
        except Exception as e:
            logger.debug(f"Could not store original values for indexing: {e}")


def register_indexing_signals() -> None:
    """
    Register all indexing signal handlers.
    
    This function should be called during application initialization
    to ensure all signal handlers are registered.
    """
    # Signal handlers are already registered via decorators
    # This function exists for explicit registration if needed
    logger.info("Indexing signal handlers registered")


def unregister_indexing_signals() -> None:
    """
    Unregister all indexing signal handlers.
    
    This function can be called to disable automatic indexing.
    """
    # Disconnect signal handlers
    from django.db.models.signals import post_save, post_delete, pre_save
    
    post_save.disconnect(handle_post_save)
    post_delete.disconnect(handle_post_delete)
    pre_save.disconnect(handle_pre_save)
    
    logger.info("Indexing signal handlers unregistered")
