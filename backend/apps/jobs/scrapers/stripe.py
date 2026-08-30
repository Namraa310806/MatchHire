"""
Stripe job scraper.

This scraper extracts jobs from Stripe's official Greenhouse ATS API.
Source: https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true

Stripe uses Greenhouse as their official ATS. The Greenhouse Job Board API is a public,
documented API that requires no authentication and is designed for third-party integrations.

Source format: Structured JSON API with the following structure:
{
    "jobs": [
        {
            "id": 7532733,
            "title": "Account Executive, AI Sales",
            "location": {"name": "San Francisco, CA"},
            "content": "<html>...</html>",
            "absolute_url": "https://stripe.com/jobs/search?gh_jid=7532733",
            "first_published": "2026-02-03T15:19:01-05:00",
            "updated_at": "2026-08-25T17:40:40-04:00",
            "departments": [...],
            "offices": [...]
        }
    ]
}
"""

import logging
import requests
from typing import List, Dict, Any
from decimal import Decimal
import re
from html import unescape

from .base import BaseJobScraper, NormalizedJob, ScrapingError
from apps.jobs.models import Job


logger = logging.getLogger(__name__)


class StripeScraper(BaseJobScraper):
    """
    Scraper for Stripe's official Greenhouse ATS API.
    
    This scraper handles the JSON format returned by the Greenhouse Job Board API
    and normalizes it to the common NormalizedJob representation.
    
    Greenhouse API documentation: https://docs.greenhouse.io/job-board.html
    """
    
    # Default API endpoint
    DEFAULT_API_URL = 'https://boards-api.greenhouse.io/v1/boards/stripe/jobs'
    
    def get_source_identifier(self) -> str:
        """Return the unique source identifier for Stripe."""
        return 'stripe'
    
    def fetch(self) -> Dict[str, Any]:
        """
        Fetch raw job data from Stripe's Greenhouse API.
        
        Returns:
            Raw JSON response as a dictionary
        
        Raises:
            ScrapingError: If HTTP request fails or response is invalid
        """
        api_url = self.config.get('api_url', self.DEFAULT_API_URL)
        timeout = self.config.get('timeout', 30)
        
        # Add content=true to get full job descriptions
        if 'content=true' not in api_url:
            api_url = f"{api_url}?content=true"
        
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
        - Field mapping from Greenhouse format to NormalizedJob
        - HTML content to plain text conversion
        - Location extraction
        - Department/office metadata extraction
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
            content = extracted_job.get('content')
            application_url = extracted_job.get('absolute_url')
            
            if not external_id:
                raise ScrapingError("Missing required field: id")
            if not title:
                raise ScrapingError("Missing required field: title")
            if not content:
                raise ScrapingError("Missing required field: content")
            if not application_url:
                raise ScrapingError("Missing required field: absolute_url")
            
            # Convert HTML content to plain text for description
            description = self._html_to_text(content)
            
            # Extract location
            location_obj = extracted_job.get('location', {})
            location = location_obj.get('name') if location_obj else None
            
            # Extract department for keywords
            departments = extracted_job.get('departments', [])
            department_names = [dept.get('name', '') for dept in departments if dept.get('name')]
            
            # Extract office for location context
            offices = extracted_job.get('offices', [])
            office_names = [office.get('name', '') for office in offices if office.get('name')]
            
            # Build keywords from department and office
            keywords = []
            keywords.extend(department_names)
            keywords.extend(office_names)
            
            # Normalize keywords
            keywords = self._normalize_keyword_list(keywords)
            
            # Build normalized job
            normalized_job = NormalizedJob(
                source=self.source_identifier,
                external_id=str(external_id),
                title=title.strip(),
                description=description.strip(),
                location=location.strip() if location else None,
                employment_type=None,  # Not provided by Greenhouse API
                experience_required=None,  # Not explicitly structured
                minimum_experience_years=None,
                maximum_experience_years=None,
                skills=[],  # Not explicitly structured in Greenhouse
                keywords=keywords,
                application_url=application_url.strip(),
                source_url=application_url.strip(),  # Same as application_url for Greenhouse
                raw_data=extracted_job
            )
            
            return normalized_job
            
        except ScrapingError:
            raise
        except Exception as e:
            raise ScrapingError(f"Normalization failed: {e}") from e
    
    def _html_to_text(self, html_content: str) -> str:
        """
        Convert HTML content to plain text.
        
        This is a simple conversion that removes HTML tags and unescapes entities.
        For production use, consider using a proper HTML parsing library like BeautifulSoup.
        
        Args:
            html_content: HTML string
        
        Returns:
            Plain text string
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html_content)
        # Unescape HTML entities
        text = unescape(text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
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
        seen = set()
        for keyword in keywords:
            if keyword:
                normalized_keyword = keyword.lower().strip()
                if normalized_keyword and normalized_keyword not in seen:
                    normalized.append(normalized_keyword)
                    seen.add(normalized_keyword)
        
        return normalized
