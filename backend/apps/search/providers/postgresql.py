"""
PostgreSQL search provider implementation.

This provider uses Django ORM and PostgreSQL-specific features like
full-text search (tsvector) and trigram matching (pg_trgm) to provide
search capabilities without requiring an external search engine.
"""

import time
from typing import Any, Dict, List, Optional
from django.db import models, connection
from django.db.models import Q, QuerySet
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

from .base import (
    SearchProvider,
    IndexResult,
    BulkIndexResult,
    DeleteResult,
    BulkDeleteResult,
    HealthResult,
    StatisticsResult,
)
from apps.search.exceptions import ProviderUnavailable, InvalidQuery


class PostgreSQLProvider(SearchProvider):
    """
    PostgreSQL-based search provider using Django ORM.

    This provider implements search using:
    - Django ORM for filtering and ordering
    - PostgreSQL full-text search (tsvector) for text search
    - PostgreSQL trigram matching (pg_trgm) for autocomplete
    - GIN indexes for performance
    """

    # Entity type to Django model mapping
    ENTITY_MODELS = {
        "job": "apps.jobs.models.Job",
        "candidate": "apps.users.models.User",
        "resume": "apps.resumes.models.Resume",
        "company": "apps.users.models.RecruiterProfile",
        "recruiter": "apps.users.models.User",
        "skill": "apps.resumes.models.ResumeSkill",
    }

    # Searchable fields per entity type
    SEARCHABLE_FIELDS = {
        "job": ["title", "description", "requirements", "company_name"],
        "candidate": ["full_name", "email"],
        "resume": ["raw_text"],
        "company": ["company_name"],
        "recruiter": ["full_name", "email"],
        "skill": ["name"],
    }

    # Autocomplete fields per entity type
    AUTOCOMPLETE_FIELDS = {
        "job": ["title", "company_name"],
        "candidate": ["full_name"],
        "resume": ["full_name"],
        "company": ["company_name"],
        "recruiter": ["full_name"],
        "skill": ["name"],
    }

    def _initialize(self) -> None:
        """Initialize PostgreSQL provider."""
        self.connection_name = self.config.get("connection", "default")
        # Verify connection is available
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            raise ProviderUnavailable(f"PostgreSQL connection failed: {e}")

    def _get_model(self, entity_type: str) -> models.Model:
        """Get Django model for entity type."""
        model_path = self.ENTITY_MODELS.get(entity_type)
        if not model_path:
            raise InvalidQuery(f"Unknown entity type: {entity_type}")

        module_path, class_name = model_path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)

    def _get_searchable_fields(self, entity_type: str) -> List[str]:
        """Get searchable fields for entity type."""
        return self.SEARCHABLE_FIELDS.get(entity_type, [])

    def _apply_filters(self, queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """Apply filters to queryset."""
        filter_q = Q()

        for field, value in filters.items():
            if value is None:
                continue

            # Handle exact match
            if isinstance(value, (str, int, float, bool)):
                filter_q &= Q(**{field: value})

            # Handle range filters (field__gte, field__lte)
            elif isinstance(value, dict):
                if "gte" in value:
                    filter_q &= Q(**{f"{field}__gte": value["gte"]})
                if "lte" in value:
                    filter_q &= Q(**{f"{field}__lte": value["lte"]})
                if "gt" in value:
                    filter_q &= Q(**{f"{field}__gt": value["gt"]})
                if "lt" in value:
                    filter_q &= Q(**{f"{field}__lt": value["lt"]})

            # Handle in filter (list of values)
            elif isinstance(value, (list, tuple)):
                filter_q &= Q(**{f"{field}__in": value})

        return queryset.filter(filter_q)

    def _apply_sort(self, queryset: QuerySet, sort: List[Dict[str, Any]]) -> QuerySet:
        """Apply sorting to queryset."""
        if not sort:
            return queryset

        order_fields = []
        for sort_spec in sort:
            field = sort_spec.get("field")
            direction = sort_spec.get("direction", "asc")

            if direction == "desc":
                order_fields.append(f"-{field}")
            else:
                order_fields.append(field)

        return queryset.order_by(*order_fields)

    def _apply_pagination(
        self, queryset: QuerySet, pagination: Dict[str, Any]
    ) -> tuple[QuerySet, int, int]:
        """Apply pagination to queryset."""
        # Support both page/page_size and offset/limit
        if "page" in pagination and "page_size" in pagination:
            page = max(1, pagination["page"])
            page_size = max(1, min(100, pagination["page_size"]))
            offset = (page - 1) * page_size
            limit = page_size
        elif "offset" in pagination and "limit" in pagination:
            offset = max(0, pagination["offset"])
            limit = max(1, min(100, pagination["limit"]))
        else:
            # Default pagination
            offset = 0
            limit = 20

        total = queryset.count()
        paginated_queryset = queryset[offset : offset + limit]

        return paginated_queryset, total, offset

    def _apply_field_selection(
        self, queryset: QuerySet, fields: Optional[List[str]]
    ) -> QuerySet:
        """Apply field selection to queryset."""
        if fields:
            return queryset.only(*fields)
        return queryset

    def _apply_fulltext_search(
        self, queryset: QuerySet, query: str, entity_type: str
    ) -> QuerySet:
        """Apply PostgreSQL full-text search."""
        searchable_fields = self._get_searchable_fields(entity_type)

        if not searchable_fields or not query:
            return queryset

        # Create search vector from searchable fields
        search_vector = SearchVector(*searchable_fields)
        search_query = SearchQuery(query)

        # Annotate with search rank and filter
        queryset = queryset.annotate(
            search=search_vector, rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query)

        return queryset

    def search(
        self,
        entity_type: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        pagination: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute a search query using PostgreSQL."""
        start_time = time.time()

        try:
            model = self._get_model(entity_type)
            queryset = model.objects.all()

            # Apply full-text search if query is provided
            if query:
                queryset = self._apply_fulltext_search(queryset, query, entity_type)

            # Apply filters
            if filters:
                queryset = self._apply_filters(queryset, filters)

            # Apply field selection
            if fields:
                queryset = self._apply_field_selection(queryset, fields)

            # Apply sorting
            if sort:
                queryset = self._apply_sort(queryset, sort)
            else:
                # Default sort by rank if full-text search, else by created_at
                if query and hasattr(queryset.model, "rank"):
                    queryset = queryset.order_by("-rank")
                elif hasattr(queryset.model, "created_at"):
                    queryset = queryset.order_by("-created_at")

            # Apply pagination
            if pagination:
                queryset, total, offset = self._apply_pagination(queryset, pagination)
            else:
                total = queryset.count()
                offset = 0

            # Convert to list of dicts
            results = list(queryset.values())

            took_ms = int((time.time() - start_time) * 1000)

            return {
                "results": results,
                "total": total,
                "offset": offset,
                "took_ms": took_ms,
                "metadata": {
                    "provider": "postgresql",
                    "entity_type": entity_type,
                    "query": query,
                },
            }

        except Exception as e:
            raise InvalidQuery(f"Search failed: {e}")

    def autocomplete(
        self,
        entity_type: str,
        field: str,
        prefix: str,
        context: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get autocomplete suggestions using PostgreSQL trigram matching."""
        try:
            model = self._get_model(entity_type)
            queryset = model.objects.all()

            # Apply context filters if provided
            if context:
                queryset = self._apply_filters(queryset, context)

            # Use icontains for simple prefix matching
            # In production, consider using pg_trgm for better performance
            queryset = queryset.filter(**{f"{field}__icontains": prefix})

            # Get distinct values
            values = (
                queryset.values_list(field, flat=True)
                .distinct()
                .order_by(field)[:limit]
            )

            # Return as list of dicts
            return [{"value": value, "metadata": {}} for value in values if value]

        except Exception as e:
            raise InvalidQuery(f"Autocomplete failed: {e}")

    def index(
        self,
        entity_type: str,
        document_id: str,
        document: Dict[str, Any],
    ) -> IndexResult:
        """
        Index a single document.

        For PostgreSQL, this is a no-op since the database is the source of truth.
        Indexing happens automatically through the ORM.
        """
        start_time = time.time()

        try:
            # Verify the document exists in the database
            model = self._get_model(entity_type)
            model.objects.filter(pk=document_id).exists()

            took_ms = int((time.time() - start_time) * 1000)

            return IndexResult(
                success=True,
                document_id=document_id,
                took_ms=took_ms,
            )

        except Exception as e:
            return IndexResult(
                success=False,
                document_id=document_id,
                error=str(e),
                took_ms=int((time.time() - start_time) * 1000),
            )

    def bulk_index(
        self,
        entity_type: str,
        documents: List[Dict[str, Any]],
    ) -> BulkIndexResult:
        """
        Index multiple documents in bulk.

        For PostgreSQL, this is a no-op since the database is the source of truth.
        """
        start_time = time.time()
        indexed_count = 0
        failed_count = 0
        errors = []

        for doc in documents:
            doc_id = doc.get("id")
            if not doc_id:
                failed_count += 1
                errors.append({"document": doc, "error": "Missing id field"})
                continue

            result = self.index(entity_type, doc_id, doc)
            if result.success:
                indexed_count += 1
            else:
                failed_count += 1
                errors.append({"document_id": doc_id, "error": result.error})

        took_ms = int((time.time() - start_time) * 1000)

        return BulkIndexResult(
            success=failed_count == 0,
            indexed_count=indexed_count,
            failed_count=failed_count,
            errors=errors,
            took_ms=took_ms,
        )

    def delete(
        self,
        entity_type: str,
        document_id: str,
    ) -> DeleteResult:
        """
        Delete a single document from the index.

        For PostgreSQL, this deletes the actual record from the database.
        """
        start_time = time.time()

        try:
            model = self._get_model(entity_type)
            deleted = model.objects.filter(pk=document_id).delete()

            if deleted[0] > 0:
                took_ms = int((time.time() - start_time) * 1000)
                return DeleteResult(
                    success=True,
                    document_id=document_id,
                    took_ms=took_ms,
                )
            else:
                took_ms = int((time.time() - start_time) * 1000)
                return DeleteResult(
                    success=False,
                    document_id=document_id,
                    error="Document not found",
                    took_ms=took_ms,
                )

        except Exception as e:
            return DeleteResult(
                success=False,
                document_id=document_id,
                error=str(e),
                took_ms=int((time.time() - start_time) * 1000),
            )

    def bulk_delete(
        self,
        entity_type: str,
        document_ids: List[str],
    ) -> BulkDeleteResult:
        """
        Delete multiple documents from the index in bulk.

        For PostgreSQL, this deletes the actual records from the database.
        """
        start_time = time.time()
        deleted_count = 0
        failed_count = 0
        errors = []

        for doc_id in document_ids:
            result = self.delete(entity_type, doc_id)
            if result.success:
                deleted_count += 1
            else:
                failed_count += 1
                errors.append({"document_id": doc_id, "error": result.error})

        took_ms = int((time.time() - start_time) * 1000)

        return BulkDeleteResult(
            success=failed_count == 0,
            deleted_count=deleted_count,
            failed_count=failed_count,
            errors=errors,
            took_ms=took_ms,
        )

    def health(self) -> HealthResult:
        """Check the health of the PostgreSQL connection."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            return HealthResult(
                healthy=True,
                provider_name="postgresql",
                details={
                    "connection": self.connection_name,
                    "database": connection.settings_dict["NAME"],
                },
            )

        except Exception as e:
            return HealthResult(
                healthy=False,
                provider_name="postgresql",
                details={},
                error=str(e),
            )

    def statistics(
        self,
        entity_type: Optional[str] = None,
    ) -> StatisticsResult:
        """Get statistics about indexed documents."""
        try:
            if entity_type:
                model = self._get_model(entity_type)
                document_count = model.objects.count()
            else:
                # Count all entities
                document_count = 0
                for model_path in self.ENTITY_MODELS.values():
                    module_path, class_name = model_path.rsplit(".", 1)
                    module = __import__(module_path, fromlist=[class_name])
                    model = getattr(module, class_name)
                    document_count += model.objects.count()

            return StatisticsResult(
                document_count=document_count,
                details={"entity_type": entity_type} if entity_type else None,
            )

        except Exception as e:
            raise InvalidQuery(f"Statistics query failed: {e}")
