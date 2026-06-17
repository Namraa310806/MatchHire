import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from django.db import transaction
from django.utils import timezone

from ..models import (
    StructuredResume,
    ResumeSkill,
    ResumeEducation,
    ResumeExperience,
    ResumeProject,
    ResumeCertification,
    ParsedResume,
)


class ResumeExtractionService:
    """
    Service for extracting structured resume data from raw parsed resume text.
    Uses deterministic parsing only: regex, section detection, heuristics, rule-based extraction.
    NO AI, NO OpenAI, NO external APIs, NO embeddings.
    """

    # Common section headings
    SECTION_PATTERNS = {
        'skills': r'(?i)^(skills|technical\s+skills|technologies|tech\s+stack|competencies|programming\s+languages)(:|\s*$)',
        'experience': r'(?i)^(experience|work\s+experience|professional\s+experience|employment\s+history|work\s+history)(:|\s*$)',
        'education': r'(?i)^(education|academic\s+background|educational\s+background|qualifications)(:|\s*$)',
        'projects': r'(?i)^(projects|personal\s+projects|side\s+projects|portfolio)(:|\s*$)',
        'certifications': r'(?i)^(certifications|certificates|credentials|licenses)(:|\s*$)',
        'summary': r'(?i)^(summary|profile|about\s+me|objective|professional\s+summary)(:|\s*$)',
    }

    # Email patterns
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    # Phone patterns (international and US formats)
    PHONE_PATTERNS = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # International/US
        r'\+?\d{1,3}[-.\s]?\d{10}',  # Simple international
        r'\(\d{3}\)\s*\d{3}-\d{4}',  # (xxx) xxx-xxxx
        r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',  # xxx-xxx-xxxx
    ]

    # URL patterns
    LINKEDIN_PATTERN = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+/?'
    GITHUB_PATTERN = r'(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9-]+/?'
    PORTFOLIO_PATTERN = r'(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.(?:com|io|net|org|dev|co|me)(?:/.*)?'

    # Date patterns for experience/education
    DATE_PATTERNS = [
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',  # Month Year
        r'\d{1,2}/\d{4}',  # MM/YYYY
        r'\d{4}',  # Year only
        r'(Spring|Summer|Fall|Winter)\s+\d{4}',  # Season Year
    ]

    @classmethod
    def extract(cls, parsed_resume: ParsedResume) -> StructuredResume:
        """
        Main extraction method. Extracts all structured data from parsed resume.
        Replaces old extracted records idempotently.
        """
        if not parsed_resume.raw_text:
            raise ValueError("Parsed resume has no raw text to extract from")

        raw_text = parsed_resume.raw_text

        # Delete existing structured resume if it exists
        StructuredResume.objects.filter(resume_version=parsed_resume.resume_version).delete()

        # Extract all data
        contact_info = cls.extract_contact_info(raw_text)
        links = cls.extract_links(raw_text)
        sections = cls.detect_sections(raw_text)
        
        summary = cls.extract_summary(raw_text, sections)
        skills = cls.extract_skills(raw_text, sections)
        education = cls.extract_education(raw_text, sections)
        experience = cls.extract_experience(raw_text, sections)
        projects = cls.extract_projects(raw_text, sections)
        certifications = cls.extract_certifications(raw_text, sections)

        # Create structured resume
        structured_resume = StructuredResume.objects.create(
            resume_version=parsed_resume.resume_version,
            full_name=contact_info.get('full_name', ''),
            email=contact_info.get('email', ''),
            phone=contact_info.get('phone', ''),
            location=contact_info.get('location', ''),
            summary=summary,
            linkedin_url=links.get('linkedin', ''),
            github_url=links.get('github', ''),
            portfolio_url=links.get('portfolio', ''),
        )

        # Create related records
        cls._create_skills(structured_resume, skills)
        cls._create_education(structured_resume, education)
        cls._create_experience(structured_resume, experience)
        cls._create_projects(structured_resume, projects)
        cls._create_certifications(structured_resume, certifications)

        return structured_resume

    @classmethod
    def extract_contact_info(cls, raw_text: str) -> Dict[str, str]:
        """
        Extract contact information: full_name, email, phone, location.
        """
        contact_info = {
            'full_name': '',
            'email': '',
            'phone': '',
            'location': '',
        }

        # Extract email
        email_match = re.search(cls.EMAIL_PATTERN, raw_text)
        if email_match:
            contact_info['email'] = email_match.group()

        # Extract phone
        for pattern in cls.PHONE_PATTERNS:
            phone_match = re.search(pattern, raw_text)
            if phone_match:
                contact_info['phone'] = phone_match.group().strip()
                break

        # Extract location (common patterns)
        location_patterns = [
            r'(?:Location|City|Address|Based in)[:\s]+([A-Za-z\s,]+(?:State|Province|Country)?)',
            r'([A-Za-z\s]+,\s*[A-Z]{2})',  # City, State
            r'([A-Za-z\s]+,\s*[A-Za-z\s]+)',  # City, Country
        ]
        for pattern in location_patterns:
            location_match = re.search(pattern, raw_text, re.IGNORECASE)
            if location_match:
                location = location_match.group(1).strip()
                if len(location) > 3 and len(location) < 100:
                    contact_info['location'] = location
                    break

        # Extract full name (typically first line or before email)
        lines = raw_text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and len(line.split()) >= 2 and len(line) < 60:
                # Check if it looks like a name (no numbers, no special chars except hyphens)
                if re.match(r'^[A-Za-z\s\-\.]+$', line):
                    contact_info['full_name'] = line
                    break

        return contact_info

    @classmethod
    def extract_links(cls, raw_text: str) -> Dict[str, str]:
        """
        Extract LinkedIn, GitHub, and portfolio URLs.
        """
        links = {
            'linkedin': '',
            'github': '',
            'portfolio': '',
        }

        # Extract LinkedIn
        linkedin_match = re.search(cls.LINKEDIN_PATTERN, raw_text)
        if linkedin_match:
            url = linkedin_match.group()
            if not url.startswith('http'):
                url = 'https://' + url
            links['linkedin'] = url

        # Extract GitHub
        github_match = re.search(cls.GITHUB_PATTERN, raw_text)
        if github_match:
            url = github_match.group()
            if not url.startswith('http'):
                url = 'https://' + url
            links['github'] = url

        # Extract portfolio (heuristic: URLs that aren't LinkedIn or GitHub)
        all_urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', raw_text)
        for url in all_urls:
            url = url.rstrip('.,;:')
            if 'linkedin' not in url.lower() and 'github' not in url.lower():
                if not links['portfolio']:
                    links['portfolio'] = url

        return links

    @classmethod
    def detect_sections(cls, raw_text: str) -> Dict[str, Tuple[int, int]]:
        """
        Detect section boundaries in the resume text.
        Returns dict mapping section name to (start_line, end_line).
        """
        sections = {}
        lines = raw_text.split('\n')
        section_starts = {}
        
        # Find section start lines
        for i, line in enumerate(lines):
            line = line.strip()
            for section_name, pattern in cls.SECTION_PATTERNS.items():
                if re.match(pattern, line):
                    section_starts[section_name] = i
                    break

        # Determine section end lines
        sorted_starts = sorted(section_starts.items(), key=lambda x: x[1])
        for i, (section_name, start_line) in enumerate(sorted_starts):
            if i + 1 < len(sorted_starts):
                next_section_line = sorted_starts[i + 1][1]
                sections[section_name] = (start_line, next_section_line)
            else:
                sections[section_name] = (start_line, len(lines))

        return sections

    @classmethod
    def extract_summary(cls, raw_text: str, sections: Dict[str, Tuple[int, int]]) -> str:
        """
        Extract summary/profile section.
        """
        if 'summary' in sections:
            start, end = sections['summary']
            lines = raw_text.split('\n')[start:end]
            # Skip the heading line
            summary_lines = [line.strip() for line in lines[1:] if line.strip()]
            return '\n'.join(summary_lines[:5])  # Limit to first 5 lines
        
        # Fallback: look for summary-like text at the beginning
        lines = raw_text.split('\n')[:10]
        for line in lines:
            line = line.strip()
            if len(line) > 50 and len(line) < 500:
                # Check if it's not a heading
                if not re.match(r'^[A-Z][A-Za-z\s]+$', line):
                    return line
        
        return ''

    @classmethod
    def extract_skills(cls, raw_text: str, sections: Dict[str, Tuple[int, int]]) -> List[str]:
        """
        Extract skills from the skills section.
        """
        skills = []
        
        if 'skills' in sections:
            start, end = sections['skills']
            section_text = '\n'.join(raw_text.split('\n')[start:end])
            
            # Remove the heading line (first line)
            lines = section_text.split('\n')
            if lines:
                section_text = '\n'.join(lines[1:])
            
            # Extract skills using various delimiters
            # Try comma-separated
            if ',' in section_text:
                skills = [s.strip() for s in section_text.split(',') if s.strip()]
            # Try bullet points
            elif '•' in section_text or '-' in section_text:
                skills = [s.strip('•-').strip() for s in section_text.split('\n') if s.strip() and (s.strip().startswith('•') or s.strip().startswith('-'))]
            # Try newlines
            else:
                skills = [s.strip() for s in section_text.split('\n') if s.strip() and len(s.strip()) > 2]
            
            # Clean up skills
            skills = [s for s in skills if len(s) > 1 and len(s) < 100]
        
        return skills[:50]  # Limit to 50 skills

    @classmethod
    def extract_education(cls, raw_text: str, sections: Dict[str, Tuple[int, int]]) -> List[Dict]:
        """
        Extract education entries.
        """
        education_entries = []
        
        if 'education' in sections:
            start, end = sections['education']
            section_text = '\n'.join(raw_text.split('\n')[start:end])
            
            # Remove the heading line (first line)
            lines = section_text.split('\n')
            if lines:
                section_text = '\n'.join(lines[1:])
            
            # Split by common delimiters (double newlines usually separate entries)
            entries = re.split(r'\n\s*\n', section_text.strip())
            
            for entry in entries:
                entry = entry.strip()
                if len(entry) < 10:
                    continue
                
                edu_data = {
                    'institution': '',
                    'degree': '',
                    'field_of_study': '',
                    'start_year': None,
                    'end_year': None,
                    'description': '',
                }
                
                lines = entry.split('\n')
                
                # First line usually contains institution
                if lines:
                    edu_data['institution'] = lines[0].strip()
                
                # Look for degree and field of study
                degree_keywords = ['Bachelor', 'Master', 'PhD', 'Doctor', 'MBA', 'B.S.', 'M.S.', 'B.A.', 'M.A.']
                for line in lines:
                    for keyword in degree_keywords:
                        if keyword in line:
                            edu_data['degree'] = line.strip()
                            break
                
                # Extract years
                year_matches = re.findall(r'\b(19|20)\d{2}\b', entry)
                if len(year_matches) >= 1:
                    edu_data['start_year'] = int(year_matches[0])
                if len(year_matches) >= 2:
                    edu_data['end_year'] = int(year_matches[-1])
                
                # Description (remaining lines)
                if len(lines) > 2:
                    edu_data['description'] = '\n'.join(lines[2:]).strip()
                
                if edu_data['institution']:
                    education_entries.append(edu_data)
        
        return education_entries[:10]  # Limit to 10 entries

    @classmethod
    def extract_experience(cls, raw_text: str, sections: Dict[str, Tuple[int, int]]) -> List[Dict]:
        """
        Extract work experience entries.
        """
        experience_entries = []
        
        if 'experience' in sections:
            start, end = sections['experience']
            section_text = '\n'.join(raw_text.split('\n')[start:end])
            
            # Remove the heading line (first line)
            lines = section_text.split('\n')
            if lines:
                section_text = '\n'.join(lines[1:])
            
            # Split by common delimiters
            entries = re.split(r'\n\s*\n', section_text.strip())
            
            for entry in entries:
                entry = entry.strip()
                if len(entry) < 20:
                    continue
                
                exp_data = {
                    'company': '',
                    'job_title': '',
                    'start_date': None,
                    'end_date': None,
                    'description': '',
                }
                
                lines = entry.split('\n')
                
                # First line usually contains job title and company
                if lines:
                    first_line = lines[0].strip()
                    # Try to separate title and company
                    if ' at ' in first_line.lower():
                        parts = first_line.split(' at ', 1)
                        exp_data['job_title'] = parts[0].strip()
                        exp_data['company'] = parts[1].strip()
                    elif '|' in first_line:
                        parts = first_line.split('|', 1)
                        exp_data['job_title'] = parts[0].strip()
                        exp_data['company'] = parts[1].strip()
                    elif '-' in first_line:
                        parts = first_line.split('-', 1)
                        exp_data['job_title'] = parts[0].strip()
                        exp_data['company'] = parts[1].strip()
                    else:
                        exp_data['job_title'] = first_line
                
                # Look for company in second line if not found
                if not exp_data['company'] and len(lines) > 1:
                    exp_data['company'] = lines[1].strip()
                
                # Extract dates
                for line in lines:
                    date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*(?:–|-|to)?\s*(?:(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|Present)?', line, re.IGNORECASE)
                    if date_match:
                        date_str = date_match.group()
                        exp_data['start_date'] = cls._parse_date(date_str.split('–')[0].split('-')[0].split('to')[0].strip())
                        if '–' in date_str or '-' in date_str or 'to' in date_str.lower():
                            end_part = date_str.split('–')[-1].split('-')[-1].split('to')[-1].strip()
                            if 'present' not in end_part.lower():
                                exp_data['end_date'] = cls._parse_date(end_part)
                        break
                
                # Description (remaining lines)
                if len(lines) > 2:
                    exp_data['description'] = '\n'.join(lines[2:]).strip()
                
                if exp_data['job_title'] or exp_data['company']:
                    experience_entries.append(exp_data)
        
        return experience_entries[:15]  # Limit to 15 entries

    @classmethod
    def extract_projects(cls, raw_text: str, sections: Dict[str, Tuple[int, int]]) -> List[Dict]:
        """
        Extract project entries.
        """
        project_entries = []
        
        if 'projects' in sections:
            start, end = sections['projects']
            section_text = '\n'.join(raw_text.split('\n')[start:end])
            
            # Remove the heading line (first line)
            lines = section_text.split('\n')
            if lines:
                section_text = '\n'.join(lines[1:])
            
            # Split by common delimiters
            entries = re.split(r'\n\s*\n', section_text.strip())
            
            for entry in entries:
                entry = entry.strip()
                if len(entry) < 10:
                    continue
                
                project_data = {
                    'title': '',
                    'description': '',
                    'github_url': '',
                    'project_url': '',
                }
                
                lines = entry.split('\n')
                
                # First line usually contains project title
                if lines:
                    project_data['title'] = lines[0].strip()
                
                # Extract URLs
                github_match = re.search(cls.GITHUB_PATTERN, entry)
                if github_match:
                    url = github_match.group()
                    if not url.startswith('http'):
                        url = 'https://' + url
                    project_data['github_url'] = url
                
                # Extract other project URLs
                all_urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', entry)
                for url in all_urls:
                    url = url.rstrip('.,;:')
                    if 'github' not in url.lower():
                        project_data['project_url'] = url
                        break
                
                # Description
                if len(lines) > 1:
                    project_data['description'] = '\n'.join(lines[1:]).strip()
                
                if project_data['title']:
                    project_entries.append(project_data)
        
        return project_entries[:20]  # Limit to 20 entries

    @classmethod
    def extract_certifications(cls, raw_text: str, sections: Dict[str, Tuple[int, int]]) -> List[Dict]:
        """
        Extract certification entries.
        """
        certification_entries = []
        
        if 'certifications' in sections:
            start, end = sections['certifications']
            section_text = '\n'.join(raw_text.split('\n')[start:end])
            
            # Remove the heading line (first line)
            lines = section_text.split('\n')
            if lines:
                section_text = '\n'.join(lines[1:])
            
            # Split by common delimiters
            entries = re.split(r'\n\s*\n', section_text.strip())
            
            for entry in entries:
                entry = entry.strip()
                if len(entry) < 5:
                    continue
                
                cert_data = {
                    'name': '',
                    'issuer': '',
                    'issue_date': None,
                }
                
                lines = entry.split('\n')
                
                # First line usually contains certification name
                if lines:
                    cert_data['name'] = lines[0].strip()
                
                # Look for issuer (common patterns)
                issuer_keywords = ['by', 'from', 'issued by', 'certified by']
                for line in lines:
                    for keyword in issuer_keywords:
                        if keyword in line.lower():
                            issuer = line.lower().split(keyword)[-1].strip()
                            cert_data['issuer'] = issuer
                            break
                
                # Extract date
                for line in lines:
                    date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}', line, re.IGNORECASE)
                    if date_match:
                        cert_data['issue_date'] = cls._parse_date(date_match.group())
                        break
                
                if cert_data['name']:
                    certification_entries.append(cert_data)
        
        return certification_entries[:20]  # Limit to 20 entries

    @classmethod
    def _parse_date(cls, date_str: str) -> Optional[datetime]:
        """
        Parse date string into datetime object.
        """
        if not date_str:
            return None
        
        date_str = date_str.strip()
        
        # Try various formats
        formats = [
            '%B %Y',  # January 2020
            '%b %Y',  # Jan 2020
            '%m/%Y',  # 01/2020
            '%Y',     # 2020
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None

    @classmethod
    def _create_skills(cls, structured_resume: StructuredResume, skills: List[str]) -> None:
        """Create skill records."""
        for skill_name in skills:
            ResumeSkill.objects.create(
                structured_resume=structured_resume,
                name=skill_name,
            )

    @classmethod
    def _create_education(cls, structured_resume: StructuredResume, education_list: List[Dict]) -> None:
        """Create education records."""
        for edu_data in education_list:
            ResumeEducation.objects.create(
                structured_resume=structured_resume,
                institution=edu_data.get('institution', ''),
                degree=edu_data.get('degree', ''),
                field_of_study=edu_data.get('field_of_study', ''),
                start_year=edu_data.get('start_year'),
                end_year=edu_data.get('end_year'),
                description=edu_data.get('description', ''),
            )

    @classmethod
    def _create_experience(cls, structured_resume: StructuredResume, experience_list: List[Dict]) -> None:
        """Create experience records."""
        for exp_data in experience_list:
            ResumeExperience.objects.create(
                structured_resume=structured_resume,
                company=exp_data.get('company', ''),
                job_title=exp_data.get('job_title', ''),
                start_date=exp_data.get('start_date'),
                end_date=exp_data.get('end_date'),
                description=exp_data.get('description', ''),
            )

    @classmethod
    def _create_projects(cls, structured_resume: StructuredResume, project_list: List[Dict]) -> None:
        """Create project records."""
        for project_data in project_list:
            ResumeProject.objects.create(
                structured_resume=structured_resume,
                title=project_data.get('title', ''),
                description=project_data.get('description', ''),
                github_url=project_data.get('github_url', ''),
                project_url=project_data.get('project_url', ''),
            )

    @classmethod
    def _create_certifications(cls, structured_resume: StructuredResume, certification_list: List[Dict]) -> None:
        """Create certification records."""
        for cert_data in certification_list:
            ResumeCertification.objects.create(
                structured_resume=structured_resume,
                name=cert_data.get('name', ''),
                issuer=cert_data.get('issuer', ''),
                issue_date=cert_data.get('issue_date'),
            )
