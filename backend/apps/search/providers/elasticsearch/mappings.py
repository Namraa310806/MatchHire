"""
Elasticsearch index mappings for MatchHire entities.

This module defines production-ready mappings for all entity types including
Jobs, Candidates, Companies, Recruiters, Skills, Applications, Interviews,
and Resumes.
"""

from typing import Dict, Any


class Mappings:
    """
    Elasticsearch index mappings for MatchHire entities.

    Provides production-ready mappings with keyword fields, text fields,
    dates, numeric fields, nested objects, geo placeholders, and
    dense vector placeholders.
    """

    # Base settings for all indices
    BASE_SETTINGS = {
        "number_of_shards": 3,
        "number_of_replicas": 1,
        "refresh_interval": "1s",
        "index.max_result_window": 10000,
    }

    @staticmethod
    def get_job_mapping() -> Dict[str, Any]:
        """
        Get mapping for job documents.

        Returns:
            Job index mapping
        """
        return {
            "properties": {
                "id": {"type": "keyword"},
                "job_id": {"type": "keyword"},
                "recruiter_id": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "edge_ngram": {
                            "type": "text",
                            "analyzer": "edge_ngram_analyzer",
                            "search_analyzer": "standard",
                        },
                    },
                },
                "company_name": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "edge_ngram": {
                            "type": "text",
                            "analyzer": "edge_ngram_analyzer",
                            "search_analyzer": "standard",
                        },
                    },
                },
                "location": {"type": "keyword"},
                "employment_type": {"type": "keyword"},
                "experience_level": {"type": "keyword"},
                "description": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "requirements": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "responsibilities": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "salary_min": {"type": "float"},
                "salary_max": {"type": "float"},
                "currency": {"type": "keyword"},
                "is_remote": {"type": "boolean"},
                "status": {"type": "keyword"},
                "closed_at": {"type": "date"},
                "searchable_text": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "version": {"type": "integer"},
                "metadata": {"type": "object", "dynamic": True},
                # Placeholder for future geo support
                "location_geo": {"type": "geo_point"},
                # Placeholder for future vector search
                "vector_embedding": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine",
                },
            },
        }

    @staticmethod
    def get_candidate_mapping() -> Dict[str, Any]:
        """
        Get mapping for candidate documents.

        Returns:
            Candidate index mapping
        """
        return {
            "properties": {
                "id": {"type": "keyword"},
                "user_id": {"type": "keyword"},
                "email": {"type": "keyword"},
                "full_name": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "edge_ngram": {
                            "type": "text",
                            "analyzer": "edge_ngram_analyzer",
                            "search_analyzer": "standard",
                        },
                    },
                },
                "headline": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                    },
                },
                "bio": {"type": "text", "analyzer": "standard"},
                "current_location": {"type": "keyword"},
                "years_of_experience": {"type": "integer"},
                "skills_text": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                    },
                },
                "linkedin_url": {"type": "keyword"},
                "github_url": {"type": "keyword"},
                "portfolio_url": {"type": "keyword"},
                "searchable_text": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "is_active": {"type": "boolean"},
                "is_verified": {"type": "boolean"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "version": {"type": "integer"},
                "metadata": {"type": "object", "dynamic": True},
                # Placeholder for future geo support
                "location_geo": {"type": "geo_point"},
                # Placeholder for future vector search
                "vector_embedding": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine",
                },
            },
        }

    @staticmethod
    def get_company_mapping() -> Dict[str, Any]:
        """
        Get mapping for company documents.

        Returns:
            Company index mapping
        """
        return {
            "properties": {
                "id": {"type": "keyword"},
                "company_id": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "edge_ngram": {
                            "type": "text",
                            "analyzer": "edge_ngram_analyzer",
                            "search_analyzer": "standard",
                        },
                    },
                },
                "website": {"type": "keyword"},
                "industry": {"type": "keyword"},
                "size": {"type": "keyword"},
                "description": {"type": "text", "analyzer": "standard"},
                "headquarters": {"type": "keyword"},
                "locations": {"type": "keyword"},
                "searchable_text": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "is_verified": {"type": "boolean"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "version": {"type": "integer"},
                "metadata": {"type": "object", "dynamic": True},
                # Placeholder for future geo support
                "headquarters_geo": {"type": "geo_point"},
                # Placeholder for future vector search
                "vector_embedding": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine",
                },
            },
        }

    @staticmethod
    def get_recruiter_mapping() -> Dict[str, Any]:
        """
        Get mapping for recruiter documents.

        Returns:
            Recruiter index mapping
        """
        return {
            "properties": {
                "id": {"type": "keyword"},
                "user_id": {"type": "keyword"},
                "email": {"type": "keyword"},
                "full_name": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "edge_ngram": {
                            "type": "text",
                            "analyzer": "edge_ngram_analyzer",
                            "search_analyzer": "standard",
                        },
                    },
                },
                "company_name": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                    },
                },
                "company_website": {"type": "keyword"},
                "job_title": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                    },
                },
                "searchable_text": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "is_verified": {"type": "boolean"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "version": {"type": "integer"},
                "metadata": {"type": "object", "dynamic": True},
                # Placeholder for future vector search
                "vector_embedding": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine",
                },
            },
        }

    @staticmethod
    def get_skill_mapping() -> Dict[str, Any]:
        """
        Get mapping for skill documents.

        Returns:
            Skill index mapping
        """
        return {
            "properties": {
                "id": {"type": "keyword"},
                "skill_id": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "edge_ngram": {
                            "type": "text",
                            "analyzer": "edge_ngram_analyzer",
                            "search_analyzer": "standard",
                        },
                    },
                },
                "category": {"type": "keyword"},
                "synonyms": {"type": "keyword"},
                "usage_count": {"type": "integer"},
                "searchable_text": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "version": {"type": "integer"},
                "metadata": {"type": "object", "dynamic": True},
                # Placeholder for future vector search
                "vector_embedding": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine",
                },
            },
        }

    @staticmethod
    def get_application_mapping() -> Dict[str, Any]:
        """
        Get mapping for application documents.

        Returns:
            Application index mapping
        """
        return {
            "properties": {
                "id": {"type": "keyword"},
                "application_id": {"type": "keyword"},
                "job_id": {"type": "keyword"},
                "candidate_id": {"type": "keyword"},
                "resume_version_id": {"type": "keyword"},
                "status": {"type": "keyword"},
                "searchable_text": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "version": {"type": "integer"},
                "metadata": {"type": "object", "dynamic": True},
            },
        }

    @staticmethod
    def get_interview_mapping() -> Dict[str, Any]:
        """
        Get mapping for interview documents.

        Returns:
            Interview index mapping
        """
        return {
            "properties": {
                "id": {"type": "keyword"},
                "interview_id": {"type": "keyword"},
                "application_id": {"type": "keyword"},
                "job_id": {"type": "keyword"},
                "candidate_id": {"type": "keyword"},
                "scheduled_at": {"type": "date"},
                "interview_type": {"type": "keyword"},
                "status": {"type": "keyword"},
                "searchable_text": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "version": {"type": "integer"},
                "metadata": {"type": "object", "dynamic": True},
            },
        }

    @staticmethod
    def get_resume_mapping() -> Dict[str, Any]:
        """
        Get mapping for resume documents.

        Returns:
            Resume index mapping
        """
        return {
            "properties": {
                "id": {"type": "keyword"},
                "resume_id": {"type": "keyword"},
                "user_id": {"type": "keyword"},
                "version_number": {"type": "integer"},
                "is_current": {"type": "boolean"},
                "raw_text": {"type": "text", "analyzer": "standard"},
                "summary": {"type": "text", "analyzer": "standard"},
                "full_name": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "edge_ngram": {
                            "type": "text",
                            "analyzer": "edge_ngram_analyzer",
                            "search_analyzer": "standard",
                        },
                    },
                },
                "email": {"type": "keyword"},
                "phone": {"type": "keyword"},
                "location": {"type": "keyword"},
                "skills": {"type": "keyword"},
                "education": {
                    "type": "nested",
                    "properties": {
                        "institution": {"type": "text"},
                        "degree": {"type": "text"},
                        "field": {"type": "text"},
                        "start_date": {"type": "date"},
                        "end_date": {"type": "date"},
                    },
                },
                "experience": {
                    "type": "nested",
                    "properties": {
                        "company": {"type": "text"},
                        "job_title": {"type": "text"},
                        "start_date": {"type": "date"},
                        "end_date": {"type": "date"},
                        "description": {"type": "text"},
                    },
                },
                "projects": {
                    "type": "nested",
                    "properties": {
                        "title": {"type": "text"},
                        "description": {"type": "text"},
                        "technologies": {"type": "keyword"},
                    },
                },
                "certifications": {
                    "type": "nested",
                    "properties": {
                        "name": {"type": "text"},
                        "issuer": {"type": "text"},
                        "date": {"type": "date"},
                    },
                },
                "linkedin_url": {"type": "keyword"},
                "github_url": {"type": "keyword"},
                "portfolio_url": {"type": "keyword"},
                "searchable_text": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "version": {"type": "integer"},
                "metadata": {"type": "object", "dynamic": True},
                # Placeholder for future geo support
                "location_geo": {"type": "geo_point"},
                # Placeholder for future vector search
                "vector_embedding": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine",
                },
            },
        }

    @classmethod
    def get_mapping(cls, entity_type: str) -> Dict[str, Any]:
        """
        Get mapping for a specific entity type.

        Args:
            entity_type: Entity type (job, candidate, company, recruiter, skill, application, interview, resume)

        Returns:
            Index mapping

        Raises:
            ValueError: If entity type is not supported
        """
        mapping_methods = {
            "job": cls.get_job_mapping,
            "candidate": cls.get_candidate_mapping,
            "company": cls.get_company_mapping,
            "recruiter": cls.get_recruiter_mapping,
            "skill": cls.get_skill_mapping,
            "application": cls.get_application_mapping,
            "interview": cls.get_interview_mapping,
            "resume": cls.get_resume_mapping,
        }

        method = mapping_methods.get(entity_type)
        if not method:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        return method()

    @classmethod
    def get_all_mappings(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get all entity type mappings.

        Returns:
            Dictionary mapping entity types to their mappings
        """
        return {
            "job": cls.get_job_mapping(),
            "candidate": cls.get_candidate_mapping(),
            "company": cls.get_company_mapping(),
            "recruiter": cls.get_recruiter_mapping(),
            "skill": cls.get_skill_mapping(),
            "application": cls.get_application_mapping(),
            "interview": cls.get_interview_mapping(),
            "resume": cls.get_resume_mapping(),
        }
