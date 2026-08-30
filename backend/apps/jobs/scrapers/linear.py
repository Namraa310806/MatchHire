"""
Linear scraper for Ashby ATS.

Linear uses Ashby ATS for their job postings.
API: https://api.ashbyhq.com/posting-api/job-board/linear
No authentication required.
"""

import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from decimal import Decimal

from .base import BaseJobScraper, NormalizedJob, ScrapingError


class LinearScraper(BaseJobScraper):
    """
    Scraper for Linear jobs via Ashby ATS.
    
    Linear's Ashby API returns job postings with the following structure:
    - id: UUID string (external job ID)
    - title: Job title
    - descriptionPlain: Plain text description
    - descriptionHtml: HTML description
    - jobUrl: Job detail URL
    - applyUrl: Application URL
    - location: Location string
    - department: Department name
    - team: Team name
    - employmentType: FullTime, PartTime, Intern, Contract, Temporary
    - workplaceType: Remote, OnSite, Hybrid
    - isRemote: Boolean
    - isListed: Boolean (filter out if false)
    - publishedAt: ISO datetime string
    """
    
    ASHBY_API_BASE = "https://api.ashbyhq.com/posting-api/job-board"
    ASHBY_JOB_BOARD_NAME = "linear"
    
    def __init__(self, company_slug: str, config: Dict[str, Any]):
        super().__init__(company_slug, config)
        self.api_url = f"{self.ASHBY_API_BASE}/{self.ASHBY_JOB_BOARD_NAME}"
    
    def get_source_identifier(self) -> str:
        """Return the source identifier for Linear."""
        return "linear"
    
    def fetch(self) -> Dict[str, Any]:
        """
        Fetch job postings from Linear's Ashby API.
        
        Returns:
            Raw JSON response from the API.
            
        Raises:
            ScrapingError: If the fetch fails.
        """
        try:
            params = {
                'includeCompensation': 'false'  # Don't include compensation data
            }
            
            response = requests.get(
                self.api_url,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Ashby returns {apiVersion: "1", jobs: [...]}
            if not isinstance(data, dict) or 'jobs' not in data:
                raise ScrapingError(
                    f"Expected Ashby API response with 'jobs' key, got {type(data).__name__}"
                )
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise ScrapingError(f"Failed to fetch Linear jobs: {str(e)}")
        except ValueError as e:
            raise ScrapingError(f"Failed to parse Linear API response: {str(e)}")
    
    def extract(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract job postings from raw API response.
        
        Args:
            raw_data: Raw JSON response from Ashby API (dict with 'jobs' key).
            
        Returns:
            List of job dictionaries.
            
        Raises:
            ScrapingError: If extraction fails.
        """
        if not isinstance(raw_data, dict):
            raise ScrapingError(
                f"Expected dict with 'jobs' key, got {type(raw_data).__name__}"
            )
        
        jobs = raw_data.get('jobs', [])
        
        if not isinstance(jobs, list):
            raise ScrapingError(
                f"Expected 'jobs' to be a list, got {type(jobs).__name__}"
            )
        
        # Filter out unlisted jobs (should not be displayed publicly)
        listed_jobs = [job for job in jobs if job.get('isListed', True)]
        
        return listed_jobs
    
    def normalize(self, job_data: Dict[str, Any]) -> NormalizedJob:
        """
        Normalize a single job posting to NormalizedJob format.
        
        Args:
            job_data: Raw job data from Ashby API.
            
        Returns:
            NormalizedJob instance.
            
        Raises:
            ScrapingError: If normalization fails or required fields are missing.
        """
        # Extract required fields
        external_id = job_data.get('id')
        title = job_data.get('title')
        
        # Description: prefer plain text, fall back to HTML
        description = job_data.get('descriptionPlain') or job_data.get('descriptionHtml')
        
        # Application URL
        application_url = job_data.get('applyUrl') or job_data.get('jobUrl')
        
        # Validate required fields
        if not external_id:
            raise ScrapingError("Missing required field: id")
        if not title:
            raise ScrapingError("Missing required field: title")
        if not description:
            raise ScrapingError("Missing required field: descriptionPlain or descriptionHtml")
        if not application_url:
            raise ScrapingError("Missing required field: applyUrl or jobUrl")
        
        # Location
        location = job_data.get('location')
        
        # Employment type
        employment_type_raw = job_data.get('employmentType', '')
        employment_type = self._normalize_employment_type(employment_type_raw)
        
        # Department and team for keywords
        department = job_data.get('department', '')
        team = job_data.get('team', '')
        
        # Build keywords from department and team
        keywords = []
        if department:
            keywords.append(department.lower())
        if team:
            keywords.append(team.lower())
        
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
            source_url=job_data.get('jobUrl'),
            raw_data=job_data
        )
    
    def _normalize_employment_type(self, employment_type: str) -> Optional[str]:
        """
        Normalize employment type from Ashby employmentType field.
        
        Args:
            employment_type: Raw employment type string from Ashby API.
            
        Returns:
            Normalized employment type or None.
        """
        if not employment_type:
            return None
        
        type_mapping = {
            'FullTime': 'FULL_TIME',
            'PartTime': 'PART_TIME',
            'Intern': 'INTERNSHIP',
            'Contract': 'CONTRACT',
            'Temporary': 'CONTRACT',  # Map Temporary to Contract
        }
        
        return type_mapping.get(employment_type)
    
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
            'graphql', 'rest', 'api', 'microservices', 'testing', 'tdd', 'bdd',
            'temporal', 'mobx', 'styled-components', 'dbt', 'snowflake', 'metabase',
            'hex', 'oauth2', 'github', 'linear', 'jira'
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
