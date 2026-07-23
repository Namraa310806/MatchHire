"""
Tests for Elasticsearch mappings.
"""

import pytest

from apps.search.providers.elasticsearch.mappings import Mappings


class TestMappings:
    """Test Mappings class."""

    def test_get_job_mapping(self):
        """Test getting job mapping."""
        mapping = Mappings.get_job_mapping()

        assert "properties" in mapping
        assert "id" in mapping["properties"]
        assert "title" in mapping["properties"]
        assert "company_name" in mapping["properties"]
        assert mapping["properties"]["id"]["type"] == "keyword"
        assert mapping["properties"]["title"]["type"] == "text"
        assert "keyword" in mapping["properties"]["title"]["fields"]
        assert "edge_ngram" in mapping["properties"]["title"]["fields"]

    def test_get_candidate_mapping(self):
        """Test getting candidate mapping."""
        mapping = Mappings.get_candidate_mapping()

        assert "properties" in mapping
        assert "id" in mapping["properties"]
        assert "full_name" in mapping["properties"]
        assert "email" in mapping["properties"]
        assert mapping["properties"]["email"]["type"] == "keyword"

    def test_get_company_mapping(self):
        """Test getting company mapping."""
        mapping = Mappings.get_company_mapping()

        assert "properties" in mapping
        assert "company_id" in mapping["properties"]
        assert "name" in mapping["properties"]
        assert "industry" in mapping["properties"]

    def test_get_recruiter_mapping(self):
        """Test getting recruiter mapping."""
        mapping = Mappings.get_recruiter_mapping()

        assert "properties" in mapping
        assert "user_id" in mapping["properties"]
        assert "company_name" in mapping["properties"]
        assert "job_title" in mapping["properties"]

    def test_get_skill_mapping(self):
        """Test getting skill mapping."""
        mapping = Mappings.get_skill_mapping()

        assert "properties" in mapping
        assert "skill_id" in mapping["properties"]
        assert "name" in mapping["properties"]
        assert "category" in mapping["properties"]
        assert "synonyms" in mapping["properties"]

    def test_get_application_mapping(self):
        """Test getting application mapping."""
        mapping = Mappings.get_application_mapping()

        assert "properties" in mapping
        assert "application_id" in mapping["properties"]
        assert "job_id" in mapping["properties"]
        assert "candidate_id" in mapping["properties"]
        assert "status" in mapping["properties"]

    def test_get_interview_mapping(self):
        """Test getting interview mapping."""
        mapping = Mappings.get_interview_mapping()

        assert "properties" in mapping
        assert "interview_id" in mapping["properties"]
        assert "application_id" in mapping["properties"]
        assert "scheduled_at" in mapping["properties"]
        assert mapping["properties"]["scheduled_at"]["type"] == "date"

    def test_get_resume_mapping(self):
        """Test getting resume mapping."""
        mapping = Mappings.get_resume_mapping()

        assert "properties" in mapping
        assert "resume_id" in mapping["properties"]
        assert "skills" in mapping["properties"]
        assert "education" in mapping["properties"]
        assert "experience" in mapping["properties"]
        assert mapping["properties"]["education"]["type"] == "nested"
        assert mapping["properties"]["experience"]["type"] == "nested"

    def test_get_mapping_job(self):
        """Test get_mapping with job entity type."""
        mapping = Mappings.get_mapping("job")

        assert "properties" in mapping
        assert "title" in mapping["properties"]

    def test_get_mapping_candidate(self):
        """Test get_mapping with candidate entity type."""
        mapping = Mappings.get_mapping("candidate")

        assert "properties" in mapping
        assert "full_name" in mapping["properties"]

    def test_get_mapping_invalid(self):
        """Test get_mapping with invalid entity type."""
        with pytest.raises(ValueError):
            Mappings.get_mapping("invalid_entity")

    def test_get_all_mappings(self):
        """Test getting all mappings."""
        all_mappings = Mappings.get_all_mappings()

        assert "job" in all_mappings
        assert "candidate" in all_mappings
        assert "company" in all_mappings
        assert "recruiter" in all_mappings
        assert "skill" in all_mappings
        assert "application" in all_mappings
        assert "interview" in all_mappings
        assert "resume" in all_mappings

    def test_base_settings(self):
        """Test base settings."""
        settings = Mappings.BASE_SETTINGS

        assert "number_of_shards" in settings
        assert "number_of_replicas" in settings
        assert "refresh_interval" in settings

    def test_vector_embedding_placeholder(self):
        """Test vector embedding placeholder in mappings."""
        job_mapping = Mappings.get_job_mapping()
        candidate_mapping = Mappings.get_candidate_mapping()

        assert "vector_embedding" in job_mapping["properties"]
        assert job_mapping["properties"]["vector_embedding"]["type"] == "dense_vector"
        assert "vector_embedding" in candidate_mapping["properties"]

    def test_geo_placeholder(self):
        """Test geo point placeholder in mappings."""
        job_mapping = Mappings.get_job_mapping()
        candidate_mapping = Mappings.get_candidate_mapping()

        assert "location_geo" in job_mapping["properties"]
        assert job_mapping["properties"]["location_geo"]["type"] == "geo_point"
        assert "location_geo" in candidate_mapping["properties"]

    def test_resume_nested_objects(self):
        """Test resume nested objects structure."""
        mapping = Mappings.get_resume_mapping()

        education = mapping["properties"]["education"]
        assert education["type"] == "nested"
        assert "properties" in education
        assert "institution" in education["properties"]
        assert "degree" in education["properties"]

        experience = mapping["properties"]["experience"]
        assert experience["type"] == "nested"
        assert "properties" in experience
        assert "company" in experience["properties"]
        assert "job_title" in experience["properties"]

        projects = mapping["properties"]["projects"]
        assert projects["type"] == "nested"
        assert "properties" in projects
        assert "title" in projects["properties"]

        certifications = mapping["properties"]["certifications"]
        assert certifications["type"] == "nested"
        assert "properties" in certifications
        assert "name" in certifications["properties"]

    def test_edge_ngram_fields(self):
        """Test edge n-gram fields for autocomplete."""
        job_mapping = Mappings.get_job_mapping()
        candidate_mapping = Mappings.get_candidate_mapping()

        assert "edge_ngram" in job_mapping["properties"]["title"]["fields"]
        assert "edge_ngram" in job_mapping["properties"]["company_name"]["fields"]
        assert "edge_ngram" in candidate_mapping["properties"]["full_name"]["fields"]

    def test_keyword_fields(self):
        """Test keyword fields for exact matching."""
        job_mapping = Mappings.get_job_mapping()

        assert "keyword" in job_mapping["properties"]["title"]["fields"]
        assert "keyword" in job_mapping["properties"]["company_name"]["fields"]
        assert job_mapping["properties"]["id"]["type"] == "keyword"
        assert job_mapping["properties"]["status"]["type"] == "keyword"

    def test_date_fields(self):
        """Test date fields."""
        job_mapping = Mappings.get_job_mapping()
        interview_mapping = Mappings.get_interview_mapping()

        assert job_mapping["properties"]["created_at"]["type"] == "date"
        assert job_mapping["properties"]["updated_at"]["type"] == "date"
        assert job_mapping["properties"]["closed_at"]["type"] == "date"
        assert interview_mapping["properties"]["scheduled_at"]["type"] == "date"

    def test_numeric_fields(self):
        """Test numeric fields."""
        job_mapping = Mappings.get_job_mapping()
        candidate_mapping = Mappings.get_candidate_mapping()

        assert job_mapping["properties"]["salary_min"]["type"] == "float"
        assert job_mapping["properties"]["salary_max"]["type"] == "float"
        assert candidate_mapping["properties"]["years_of_experience"]["type"] == "integer"

    def test_boolean_fields(self):
        """Test boolean fields."""
        job_mapping = Mappings.get_job_mapping()
        candidate_mapping = Mappings.get_candidate_mapping()

        assert job_mapping["properties"]["is_remote"]["type"] == "boolean"
        assert candidate_mapping["properties"]["is_active"]["type"] == "boolean"
        assert candidate_mapping["properties"]["is_verified"]["type"] == "boolean"

    def test_metadata_field(self):
        """Test metadata field is dynamic."""
        job_mapping = Mappings.get_job_mapping()

        assert "metadata" in job_mapping["properties"]
        assert job_mapping["properties"]["metadata"]["type"] == "object"
        assert job_mapping["properties"]["metadata"]["dynamic"] is True
