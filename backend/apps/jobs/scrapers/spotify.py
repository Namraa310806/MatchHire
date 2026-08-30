"""
Spotify scraper for Lever ATS.

Spotify uses Lever ATS for their job postings.
API: https://api.lever.co/v0/postings/spotify?mode=json
No authentication required.
"""

import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from decimal import Decimal

from .base import BaseJobScraper, NormalizedJob, ScrapingError


class SpotifyScraper(BaseJobScraper):
    """
    Scraper for Spotify jobs via Lever ATS.
    
    Spotify's Lever API returns job postings with the following structure:
    - id: UUID string (external job ID)
    - text: Job title
    - descriptionPlain: Plain text description
    - description: HTML description
    - hostedUrl: Job detail URL
    - applyUrl: Application URL
    - categories: {location, department, team, commitment, allLocations}
    - createdAt: Timestamp in milliseconds
    - workplaceType: remote, hybrid, or on-site
    - country: Country code
    """
    
    LEVER_API_BASE = "https://api.lever.co/v0/postings"
    LEVER_SITE_SLUG = "spotify"
    
    def __init__(self, company_slug: str, config: Dict[str, Any]):
        super().__init__(company_slug, config)
        self.api_url = f"{self.LEVER_API_BASE}/{self.LEVER_SITE_SLUG}"
    
    def get_source_identifier(self) -> str:
        """Return the source identifier for Spotify."""
        return "spotify"
    
    def fetch(self) -> Dict[str, Any]:
        """
        Fetch job postings from Spotify's Lever API.
        
        Returns:
            Raw JSON response from the API.
            
        Raises:
            ScrapingError: If the fetch fails.
        """
        try:
            params = {
                'mode': 'json',
                'limit': 100  # Lever API default limit
            }
            
            response = requests.get(
                self.api_url,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not isinstance(data, list):
                raise ScrapingError(
                    f"Expected list of jobs from Spotify API, got {type(data).__name__}"
                )
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise ScrapingError(f"Failed to fetch Spotify jobs: {str(e)}")
        except ValueError as e:
            raise ScrapingError(f"Failed to parse Spotify API response: {str(e)}")
    
    def extract(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract job postings from raw API response.
        
        Args:
            raw_data: Raw JSON response from Lever API (list of job objects).
            
        Returns:
            List of job dictionaries.
            
        Raises:
            ScrapingError: If extraction fails.
        """
        if not isinstance(raw_data, list):
            raise ScrapingError(
                f"Expected list of jobs, got {type(raw_data).__name__}"
            )
        
        return raw_data
    
    def normalize(self, job_data: Dict[str, Any]) -> NormalizedJob:
        """
        Normalize a single job posting to NormalizedJob format.
        
        Args:
            job_data: Raw job data from Lever API.
            
        Returns:
            NormalizedJob instance.
            
        Raises:
            ScrapingError: If normalization fails or required fields are missing.
        """
        # Extract required fields
        external_id = job_data.get('id')
        title = job_data.get('text')
        
        # Description: prefer plain text, fall back to HTML
        description = job_data.get('descriptionPlain') or job_data.get('description')
        
        # Application URL
        application_url = job_data.get('applyUrl') or job_data.get('hostedUrl')
        
        # Validate required fields
        if not external_id:
            raise ScrapingError("Missing required field: id")
        if not title:
            raise ScrapingError("Missing required field: text (title)")
        if not description:
            raise ScrapingError("Missing required field: descriptionPlain or description")
        if not application_url:
            raise ScrapingError("Missing required field: applyUrl or hostedUrl")
        
        # Extract categories
        categories = job_data.get('categories', {})
        
        # Location
        location = categories.get('location') or job_data.get('location')
        
        # Employment type from commitment
        commitment = categories.get('commitment', '')
        employment_type = self._normalize_employment_type(commitment)
        
        # Department and team for keywords
        department = categories.get('department', '')
        team = categories.get('team', '')
        all_locations = categories.get('allLocations', [])
        
        # Build keywords from department, team, and locations
        keywords = []
        if department:
            keywords.append(department.lower())
        if team:
            keywords.append(team.lower())
        for loc in all_locations:
            if loc:
                keywords.append(loc.lower())
        
        # Extract skills from description (simple keyword extraction)
        skills = self._extract_skills_from_description(description)
        
        # Convert HTML to plain text if description is HTML
        if description and '<' in description:
            description = self._html_to_text(description)
        
        # Create NormalizedJob
        return NormalizedJob(
            source=self.get_source_identifier(),
            external_id=str(external_id),
            title=title,
            description=description,
            location=location,
            employment_type=employment_type,
            skills=skills,
            keywords=list(set(keywords)),  # Deduplicate
            application_url=application_url,
            source_url=job_data.get('hostedUrl'),
            raw_data=job_data
        )
    
    def _normalize_employment_type(self, commitment: str) -> Optional[str]:
        """
        Normalize employment type from Lever commitment field.
        
        Args:
            commitment: Raw commitment string from Lever API.
            
        Returns:
            Normalized employment type or None.
        """
        if not commitment:
            return None
        
        commitment_lower = commitment.lower()
        
        # Map Lever commitment types to normalized values
        type_mapping = {
            'permanent': 'FULL_TIME',
            'full-time': 'FULL_TIME',
            'fulltime': 'FULL_TIME',
            'contract': 'CONTRACT',
            'contractor': 'CONTRACT',
            'intern': 'INTERNSHIP',
            'internship': 'INTERNSHIP',
            'part-time': 'PART_TIME',
            'parttime': 'PART_TIME',
        }
        
        return type_mapping.get(commitment_lower)
    
    def _extract_skills_from_description(self, description: str) -> List[str]:
        """
        Extract skills from job description using simple keyword matching.
        
        This is a basic implementation that looks for common tech keywords.
        A more sophisticated implementation could use NLP or a skills taxonomy.
        
        Args:
            description: Job description text.
            
        Returns:
            List of extracted skills (lowercase).
        """
        if not description:
            return []
        
        # Common tech skills to look for
        skill_keywords = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'node', 'django', 'flask', 'spring', 'rails', 'go', 'rust', 'swift',
            'kotlin', 'android', 'ios', 'sql', 'nosql', 'mongodb', 'postgresql',
            'mysql', 'redis', 'elasticsearch', 'docker', 'kubernetes', 'aws', 'gcp',
            'azure', 'git', 'ci/cd', 'agile', 'scrum', 'machine learning', 'ai',
            'data science', 'devops', 'linux', 'unix', 'html', 'css', 'sass',
            'graphql', 'rest', 'api', 'microservices', 'testing', 'tdd', 'bdd'
        ]
        
        description_lower = description.lower()
        found_skills = []
        
        for skill in skill_keywords:
            if skill in description_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _html_to_text(self, html_content: str) -> str:
        """
        Convert HTML content to plain text.
        
        Args:
            html_content: HTML string.
            
        Returns:
            Plain text string.
        """
        if not html_content:
            return ""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception:
            # If BeautifulSoup fails, return original content
            return html_content
