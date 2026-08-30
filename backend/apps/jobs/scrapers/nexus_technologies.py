"""
Nexus Technologies job scraper.

This scraper extracts jobs from the Nexus Technologies official careers API.
Source: https://careers.nexustech.example.test/api/jobs (fictional endpoint)

Source format: Structured JSON API with the following structure:
{
    "jobs": [
        {
            "id": "NX-1001",
            "title": "Senior Backend Engineer",
            "description": "...",
            "location": "San Francisco, CA",
            "employment_type": "Full-time",
            "experience_required": "5-7 years",
            "skills": ["Python", "Django", "PostgreSQL"],
            "keywords": ["backend", "api"],
            "application_url": "https://careers.nexustech.example.test/jobs/NX-1001"
        }
    ]
}
"""

import logging
import requests
from typing import List, Dict, Any
from decimal import Decimal
import re

from .base import BaseJobScraper, NormalizedJob, ScrapingError
from apps.jobs.models import Job


logger = logging.getLogger(__name__)


class NexusTechnologiesScraper(BaseJobScraper):
    """
    Scraper for Nexus Technologies official careers API.
    
    This scraper handles the specific JSON format returned by the
    Nexus Technologies careers API and normalizes it to the
    common NormalizedJob representation.
    """
    
    # Employment type mapping from source to Job model choices
    EMPLOYMENT_TYPE_MAP = {
        'full-time': Job.EmploymentType.FULL_TIME,
        'full time': Job.EmploymentType.FULL_TIME,
        'part-time': Job.EmploymentType.PART_TIME,
        'part time': Job.EmploymentType.PART_TIME,
        'contract': Job.EmploymentType.CONTRACT,
        'contractor': Job.EmploymentType.CONTRACT,
        'internship': Job.EmploymentType.INTERNSHIP,
        'remote': Job.EmploymentType.REMOTE,
    }
    
    # Default API endpoint (can be overridden in config)
    DEFAULT_API_URL = 'https://careers.nexustech.example.test/api/jobs'
    
    def get_source_identifier(self) -> str:
        """Return the unique source identifier for Nexus Technologies."""
        return 'nexus_technologies'
    
    def fetch(self) -> Dict[str, Any]:
        """
        Fetch raw job data from the Nexus Technologies careers API.
        
        Returns:
            Raw JSON response as a dictionary
        
        Raises:
            ScrapingError: If HTTP request fails or response is invalid
        """
        api_url = self.config.get('api_url', self.DEFAULT_API_URL)
        timeout = self.config.get('timeout', 30)
        
        logger.info(f"Fetching from {api_url}")
        
        try:
            response = requests.get(
                api_url,
                timeout=timeout,
                headers={
                    'User-Agent': 'MatchHire-Job-Ingestor/1.0'
                }
            )
            response.raise_for_status()
            
            raw_data = response.json()
            
            if not raw_data:
                raise ScrapingError("Empty response from API")
            
            return raw_data
            
        except requests.exceptions.Timeout:
            raise ScrapingError(f"Request timed out after {timeout}s")
        except requests.exceptions.HTTPError as e:
            raise ScrapingError(f"HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            raise ScrapingError(f"Request failed: {e}")
        except ValueError as e:
            raise ScrapingError(f"Invalid JSON response: {e}")
    
    def extract(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract structured job records from the raw API response.
        
        Args:
            raw_data: Raw JSON response from the API
        
        Returns:
            List of structured job records
        
        Raises:
            ScrapingError: If extraction fails or format is invalid
        """
        if 'jobs' not in raw_data:
            raise ScrapingError("Missing 'jobs' key in API response")
        
        jobs = raw_data['jobs']
        
        if not isinstance(jobs, list):
            raise ScrapingError("'jobs' must be a list")
        
        if not jobs:
            logger.warning("No jobs found in API response")
            return []
        
        logger.info(f"Extracted {len(jobs)} job records")
        return jobs
    
    def normalize(self, extracted_job: Dict[str, Any]) -> NormalizedJob:
        """
        Normalize a single extracted job to the common representation.
        
        This method handles:
        - Field mapping from source format to NormalizedJob
        - Employment type normalization
        - Experience parsing (e.g., "5-7 years" -> min=5.0, max=7.0)
        - Skill/keyword list normalization (lowercase, strip whitespace)
        - URL validation
        
        Args:
            extracted_job: Single job record from extract()
        
        Returns:
            NormalizedJob object
        
        Raises:
            ScrapingError: If normalization fails
        """
        try:
            # Extract required fields
            external_id = extracted_job.get('id')
            title = extracted_job.get('title')
            description = extracted_job.get('description')
            application_url = extracted_job.get('application_url')
            
            if not external_id:
                raise ScrapingError("Missing required field: id")
            if not title:
                raise ScrapingError("Missing required field: title")
            if not description:
                raise ScrapingError("Missing required field: description")
            if not application_url:
                raise ScrapingError("Missing required field: application_url")
            
            # Extract optional fields
            location = extracted_job.get('location')
            employment_type_str = extracted_job.get('employment_type')
            experience_required_str = extracted_job.get('experience_required')
            skills_list = extracted_job.get('skills', [])
            keywords_list = extracted_job.get('keywords', [])
            source_url = extracted_job.get('source_url')
            
            # Normalize employment type
            employment_type = self._normalize_employment_type(employment_type_str)
            
            # Parse experience requirements
            min_exp, max_exp = self._parse_experience(experience_required_str)
            
            # Normalize skills and keywords
            normalized_skills = self._normalize_skill_list(skills_list)
            normalized_keywords = self._normalize_keyword_list(keywords_list)
            
            # Build normalized job
            normalized_job = NormalizedJob(
                source=self.source_identifier,
                external_id=str(external_id),
                title=title.strip(),
                description=description.strip(),
                location=location.strip() if location else None,
                employment_type=employment_type,
                experience_required=experience_required_str.strip() if experience_required_str else None,
                minimum_experience_years=min_exp,
                maximum_experience_years=max_exp,
                skills=normalized_skills,
                keywords=normalized_keywords,
                application_url=application_url.strip(),
                source_url=source_url.strip() if source_url else None,
                raw_data=extracted_job
            )
            
            return normalized_job
            
        except ScrapingError:
            raise
        except Exception as e:
            raise ScrapingError(f"Normalization failed: {e}") from e
    
    def _normalize_employment_type(self, employment_type_str: str) -> str:
        """
        Normalize employment type to Job model choices.
        
        Args:
            employment_type_str: Raw employment type string from source
        
        Returns:
            Normalized employment type matching Job.EmploymentType choices
        """
        if not employment_type_str:
            return None
        
        normalized = employment_type_str.lower().strip()
        return self.EMPLOYMENT_TYPE_MAP.get(normalized)
    
    def _parse_experience(self, experience_str: str) -> tuple:
        """
        Parse experience string into numeric min/max values.
        
        Supports formats:
        - "X-Y years" or "X-Y" -> (5.0, 7.0)
        - "X+ years" or "X+" -> (5.0, None)
        - "X years" or just "X" -> (3.0, 3.0)
        - "Senior" -> (None, None)
        
        Args:
            experience_str: Experience requirement string
        
        Returns:
            Tuple of (minimum_experience_years, maximum_experience_years) as Decimal or None
        """
        if not experience_str:
            return None, None
        
        try:
            # Pattern for "X-Y years" or "X-Y" (must check this before single number)
            range_match = re.search(r'(\d+)\s*[-–to]\s*(\d+)', experience_str, re.IGNORECASE)
            if range_match:
                min_val = Decimal(range_match.group(1))
                max_val = Decimal(range_match.group(2))
                return min_val, max_val
            
            # Pattern for "X+ years" or "X+"
            plus_match = re.search(r'(\d+)\s*\+', experience_str, re.IGNORECASE)
            if plus_match:
                min_val = Decimal(plus_match.group(1))
                return min_val, None
            
            # Pattern for "X years" or just "X" (only if not part of a range)
            single_match = re.search(r'^(\d+)\s*(?:years?)?', experience_str, re.IGNORECASE)
            if single_match:
                val = Decimal(single_match.group(1))
                return val, val
            
            # No numeric pattern found
            return None, None
            
        except (ValueError, AttributeError):
            return None, None
    
    def _normalize_skill_list(self, skills: List[str]) -> List[str]:
        """
        Normalize skill list to lowercase, stripped strings.
        
        Args:
            skills: Raw skill list from source
        
        Returns:
            Normalized skill list
        """
        if not skills:
            return []
        
        normalized = []
        for skill in skills:
            if skill:
                normalized.append(skill.lower().strip())
        
        return normalized
    
    def _normalize_keyword_list(self, keywords: List[str]) -> List[str]:
        """
        Normalize keyword list to lowercase, stripped strings.
        
        Args:
            keywords: Raw keyword list from source
        
        Returns:
            Normalized keyword list
        """
        if not keywords:
            return []
        
        normalized = []
        for keyword in keywords:
            if keyword:
                normalized.append(keyword.lower().strip())
        
        return normalized
