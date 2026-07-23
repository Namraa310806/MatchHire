"""
Django management command to populate MatchHire with comprehensive demo data.

Creates:
- 50+ companies
- 200+ jobs
- 500+ candidates
- Thousands of applications
- Interview schedules
- Recommendations
- Search history
- Saved searches
- Notifications
- Analytics metrics
- Feature flags
- Audit logs
- Security events
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from faker import Faker

from apps.jobs.models import Company, Job, JobSkill
from apps.users.models import CandidateProfile, RecruiterProfile, Skill
from apps.applications.models import Application, ApplicationStatus
from apps.interviews.models import Interview, InterviewStatus
from apps.matching.models import Recommendation
from apps.search.models import SearchHistory, SavedSearch
from apps.notifications.models import Notification
from apps.analytics.models import AnalyticsEvent, FeatureFlag
from apps.core.models import AuditLog, SecurityEvent

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Populate database with comprehensive demo data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--companies',
            type=int,
            default=50,
            help='Number of companies to create'
        )
        parser.add_argument(
            '--jobs',
            type=int,
            default=200,
            help='Number of jobs to create'
        )
        parser.add_argument(
            '--candidates',
            type=int,
            default=500,
            help='Number of candidates to create'
        )
        parser.add_argument(
            '--applications',
            type=int,
            default=2000,
            help='Number of applications to create'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing demo data before populating'
        )

    def handle(self, *args, **options):
        companies_count = options['companies']
        jobs_count = options['jobs']
        candidates_count = options['candidates']
        applications_count = options['applications']
        clear = options['clear']

        if clear:
            self.clear_demo_data()

        self.stdout.write('Starting demo data population...')
        self.stdout.write(f'Companies: {companies_count}')
        self.stdout.write(f'Jobs: {jobs_count}')
        self.stdout.write(f'Candidates: {candidates_count}')
        self.stdout.write(f'Applications: {applications_count}')

        with transaction.atomic():
            # Create skills
            skills = self.create_skills()
            self.stdout.write(f'Created {len(skills)} skills')

            # Create companies and recruiters
            companies, recruiters = self.create_companies_and_recruiters(companies_count, skills)
            self.stdout.write(f'Created {len(companies)} companies and {len(recruiters)} recruiters')

            # Create jobs
            jobs = self.create_jobs(jobs_count, companies, skills)
            self.stdout.write(f'Created {len(jobs)} jobs')

            # Create candidates
            candidates = self.create_candidates(candidates_count, skills)
            self.stdout.write(f'Created {len(candidates)} candidates')

            # Create applications
            applications = self.create_applications(applications_count, candidates, jobs)
            self.stdout.write(f'Created {len(applications)} applications')

            # Create interviews
            interviews = self.create_interviews(applications)
            self.stdout.write(f'Created {len(interviews)} interviews')

            # Create recommendations
            recommendations = self.create_recommendations(candidates, jobs)
            self.stdout.write(f'Created {len(recommendations)} recommendations')

            # Create search history
            search_history = self.create_search_history(candidates, recruiters)
            self.stdout.write(f'Created {len(search_history)} search history entries')

            # Create saved searches
            saved_searches = self.create_saved_searches(candidates, recruiters)
            self.stdout.write(f'Created {len(saved_searches)} saved searches')

            # Create notifications
            notifications = self.create_notifications(candidates, recruiters)
            self.stdout.write(f'Created {len(notifications)} notifications')

            # Create analytics events
            analytics_events = self.create_analytics_events(candidates, recruiters)
            self.stdout.write(f'Created {len(analytics_events)} analytics events')

            # Create feature flags
            feature_flags = self.create_feature_flags()
            self.stdout.write(f'Created {len(feature_flags)} feature flags')

            # Create audit logs
            audit_logs = self.create_audit_logs(recruiters, candidates)
            self.stdout.write(f'Created {len(audit_logs)} audit logs')

            # Create security events
            security_events = self.create_security_events(candidates, recruiters)
            self.stdout.write(f'Created {len(security_events)} security events')

        self.stdout.write(self.style.SUCCESS('Demo data population completed successfully!'))

    def clear_demo_data(self):
        """Clear existing demo data."""
        self.stdout.write('Clearing existing demo data...')
        SecurityEvent.objects.all().delete()
        AuditLog.objects.all().delete()
        FeatureFlag.objects.all().delete()
        AnalyticsEvent.objects.all().delete()
        Notification.objects.all().delete()
        SavedSearch.objects.all().delete()
        SearchHistory.objects.all().delete()
        Recommendation.objects.all().delete()
        Interview.objects.all().delete()
        Application.objects.all().delete()
        CandidateProfile.objects.all().delete()
        RecruiterProfile.objects.all().delete()
        Job.objects.all().delete()
        Company.objects.all().delete()
        Skill.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write('Demo data cleared.')

    def create_skills(self):
        """Create a comprehensive set of skills."""
        skill_names = [
            # Programming Languages
            'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'Go', 'Rust',
            'TypeScript', 'PHP', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB',
            
            # Web Development
            'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring Boot',
            'Express.js', 'Next.js', 'Nuxt.js', 'HTML5', 'CSS3', 'SASS', 'Webpack',
            
            # Data Science & ML
            'TensorFlow', 'PyTorch', 'scikit-learn', 'Pandas', 'NumPy', 'Keras',
            'Data Analysis', 'Machine Learning', 'Deep Learning', 'NLP',
            
            # DevOps & Cloud
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform', 'Ansible',
            'Jenkins', 'CI/CD', 'Linux', 'Git',
            
            # Databases
            'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch', 'GraphQL',
            
            # Soft Skills
            'Leadership', 'Communication', 'Problem Solving', 'Teamwork',
            'Project Management', 'Agile', 'Scrum',
        ]
        
        skills = []
        for skill_name in skill_names:
            skill, created = Skill.objects.get_or_create(
                name=skill_name,
                defaults={'description': f'{skill_name} skill'}
            )
            skills.append(skill)
        
        return skills

    def create_companies_and_recruiters(self, count, skills):
        """Create companies and associated recruiters."""
        companies = []
        recruiters = []
        
        company_industries = [
            'Technology', 'Finance', 'Healthcare', 'E-commerce', 'Education',
            'Manufacturing', 'Consulting', 'Media', 'Telecommunications', 'Energy'
        ]
        
        company_names = [
            'TechCorp', 'InnovateLabs', 'DataDriven', 'CloudNine', 'FutureTech',
            'SmartSolutions', 'DigitalFirst', 'NextGen', 'PrimeTech', 'AlphaSystems',
            'BetaCorp', 'GammaTech', 'DeltaSoft', 'OmegaDigital', 'ZetaLabs',
            'QuantumComputing', 'NeuralNetworks', 'CyberSecurity', 'BlockchainTech',
            'AIResearch', 'MachineLearning', 'DataScience', 'CloudComputing',
            'DevOpsPro', 'AgileMethod', 'ScrumMaster', 'ProjectMgmt', 'TeamLead',
        ]
        
        for i in range(count):
            company_name = f"{company_names[i % len(company_names)]}_{i}"
            company = Company.objects.create(
                name=company_name,
                description=fake.paragraph(nb_sentences=3),
                industry=random.choice(company_industries),
                website=fake.url(),
                location=fake.city(),
                size=random.choice(['1-10', '11-50', '51-200', '201-500', '500+']),
                founded_year=random.randint(2010, 2024),
            )
            companies.append(company)
            
            # Create 1-3 recruiters per company
            num_recruiters = random.randint(1, 3)
            for j in range(num_recruiters):
                username = f"recruiter_{i}_{j}"
                email = f"{username}@{company_name.lower().replace(' ', '')}.com"
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=fake.password(),
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    role='recruiter'
                )
                
                recruiter = RecruiterProfile.objects.create(
                    user=user,
                    company=company,
                    title=random.choice(['HR Manager', 'Technical Recruiter', 'Senior Recruiter', 'Talent Acquisition Lead']),
                    phone=fake.phone_number(),
                    linkedin=fake.url(),
                )
                recruiters.append(recruiter)
        
        return companies, recruiters

    def create_jobs(self, count, companies, skills):
        """Create jobs across companies."""
        jobs = []
        job_titles = [
            'Software Engineer', 'Senior Software Engineer', 'Full Stack Developer',
            'Frontend Developer', 'Backend Developer', 'DevOps Engineer',
            'Data Scientist', 'Machine Learning Engineer', 'Data Analyst',
            'Product Manager', 'Project Manager', 'Scrum Master',
            'UX Designer', 'UI Designer', 'QA Engineer',
            'System Administrator', 'Cloud Architect', 'Security Engineer',
            'Mobile Developer', 'Technical Lead', 'Engineering Manager',
        ]
        
        job_types = ['full-time', 'part-time', 'contract', 'internship']
        experience_levels = ['entry', 'mid', 'senior', 'lead', 'executive']
        remote_options = ['on-site', 'remote', 'hybrid']
        
        for i in range(count):
            company = random.choice(companies)
            job = Job.objects.create(
                company=company,
                title=random.choice(job_titles),
                description=fake.paragraph(nb_sentences=5),
                requirements=fake.paragraph(nb_sentences=4),
                responsibilities=fake.paragraph(nb_sentences=4),
                benefits=fake.paragraph(nb_sentences=3),
                location=fake.city() if random.choice([True, False]) else 'Remote',
                job_type=random.choice(job_types),
                experience_level=random.choice(experience_levels),
                salary_min=random.randint(50000, 100000),
                salary_max=random.randint(100001, 200000),
                remote=random.choice(remote_options),
                status='active',
                posted_date=fake.date_between(start_date='-90d', end_date='today'),
                expiry_date=fake.date_between(start_date='today', end_date='+90d'),
            )
            
            # Add 3-8 skills to each job
            job_skills = random.sample(skills, random.randint(3, 8))
            for skill in job_skills:
                JobSkill.objects.create(
                    job=job,
                    skill=skill,
                    required=random.choice([True, False])
                )
            
            jobs.append(job)
        
        return jobs

    def create_candidates(self, count, skills):
        """Create candidate profiles."""
        candidates = []
        
        education_levels = ['High School', 'Bachelor', 'Master', 'PhD']
        fields_of_study = [
            'Computer Science', 'Software Engineering', 'Data Science',
            'Information Technology', 'Mathematics', 'Physics',
            'Business Administration', 'MBA', 'Psychology'
        ]
        
        for i in range(count):
            username = f"candidate_{i}"
            email = f"{username}@example.com"
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=fake.password(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role='candidate'
            )
            
            candidate = CandidateProfile.objects.create(
                user=user,
                phone=fake.phone_number(),
                location=fake.city(),
                headline=fake.sentence(),
                summary=fake.paragraph(nb_sentences=4),
                experience_years=random.randint(0, 15),
                education_level=random.choice(education_levels),
                field_of_study=random.choice(fields_of_study),
                linkedin=fake.url(),
                github=fake.url(),
                portfolio=fake.url(),
                resume=f"resumes/resume_{i}.pdf",
                resume_parsed=True,
                skills_extracted=True,
                open_to_work=random.choice([True, False]),
                open_to_remote=random.choice([True, False]),
                expected_salary_min=random.randint(40000, 80000),
                expected_salary_max=random.randint(80001, 150000),
            )
            
            # Add 3-10 skills to each candidate
            candidate_skills = random.sample(skills, random.randint(3, 10))
            candidate.skills.set(candidate_skills)
            
            candidates.append(candidate)
        
        return candidates

    def create_applications(self, count, candidates, jobs):
        """Create job applications."""
        applications = []
        statuses = ['pending', 'reviewed', 'shortlisted', 'interviewing', 'offered', 'rejected', 'withdrawn']
        
        for i in range(count):
            candidate = random.choice(candidates)
            job = random.choice(jobs)
            
            # Check if application already exists
            if Application.objects.filter(candidate=candidate, job=job).exists():
                continue
            
            application = Application.objects.create(
                candidate=candidate,
                job=job,
                cover_letter=fake.paragraph(nb_sentences=3),
                status=random.choice(statuses),
                applied_date=fake.date_between(start_date='-90d', end_date='today'),
                notes=fake.paragraph(nb_sentences=2) if random.choice([True, False]) else None,
            )
            
            applications.append(application)
        
        return applications

    def create_interviews(self, applications):
        """Create interview schedules."""
        interviews = []
        statuses = ['scheduled', 'completed', 'cancelled', 'no-show']
        interview_types = ['phone', 'video', 'on-site', 'technical', 'panel']
        
        # Only create interviews for applications in certain statuses
        eligible_applications = applications.filter(
            status__in=['shortlisted', 'interviewing', 'offered']
        )
        
        for application in eligible_applications:
            if random.random() < 0.7:  # 70% chance of interview
                interview_date = fake.date_time_between(start_date='-30d', end_date='+30d')
                
                interview = Interview.objects.create(
                    application=application,
                    type=random.choice(interview_types),
                    status=random.choice(statuses),
                    scheduled_date=interview_date,
                    duration=random.randint(30, 90),
                    location=fake.url() if random.choice([True, False]) else None,
                    notes=fake.paragraph(nb_sentences=2) if random.choice([True, False]) else None,
                    interviewer_notes=fake.paragraph(nb_sentences=2) if random.choice([True, False]) else None,
                    candidate_rating=random.randint(1, 5) if random.choice([True, False]) else None,
                )
                
                interviews.append(interview)
        
        return interviews

    def create_recommendations(self, candidates, jobs):
        """Create job recommendations for candidates."""
        recommendations = []
        
        for candidate in candidates[:100]:  # Limit to first 100 candidates
            # Recommend 5-15 jobs per candidate
            recommended_jobs = random.sample(jobs, random.randint(5, 15))
            
            for job in recommended_jobs:
                score = round(random.uniform(0.5, 0.99), 2)
                
                recommendation = Recommendation.objects.create(
                    candidate=candidate,
                    job=job,
                    score=score,
                    reasons=fake.paragraph(nb_sentences=2),
                    viewed=random.choice([True, False]),
                    clicked=random.choice([True, False]) if random.random() < 0.3 else False,
                    applied=random.choice([True, False]) if random.random() < 0.1 else False,
                    created_at=fake.date_time_between(start_date='-30d', end_date='today'),
                )
                
                recommendations.append(recommendation)
        
        return recommendations

    def create_search_history(self, candidates, recruiters):
        """Create search history entries."""
        search_history = []
        
        search_queries = [
            'software engineer', 'python developer', 'react developer',
            'data scientist', 'machine learning', 'devops engineer',
            'full stack', 'frontend developer', 'backend developer',
            'senior engineer', 'tech lead', 'product manager',
        ]
        
        # Candidate search history
        for candidate in candidates[:200]:
            num_searches = random.randint(1, 10)
            for _ in range(num_searches):
                entry = SearchHistory.objects.create(
                    user=candidate.user,
                    query=random.choice(search_queries),
                    search_type='job',
                    results_count=random.randint(10, 100),
                    timestamp=fake.date_time_between(start_date='-60d', end_date='today'),
                )
                search_history.append(entry)
        
        # Recruiter search history
        for recruiter in recruiters[:30]:
            num_searches = random.randint(1, 15)
            for _ in range(num_searches):
                entry = SearchHistory.objects.create(
                    user=recruiter.user,
                    query=random.choice(search_queries),
                    search_type='candidate',
                    results_count=random.randint(5, 50),
                    timestamp=fake.date_time_between(start_date='-60d', end_date='today'),
                )
                search_history.append(entry)
        
        return search_history

    def create_saved_searches(self, candidates, recruiters):
        """Create saved searches."""
        saved_searches = []
        
        # Candidate saved searches
        for candidate in candidates[:100]:
            if random.random() < 0.5:  # 50% chance
                saved_search = SavedSearch.objects.create(
                    user=candidate.user,
                    name=f"{fake.word()} jobs",
                    query='software engineer',
                    filters={'location': 'Remote', 'job_type': 'full-time'},
                    search_type='job',
                    email_alerts=random.choice([True, False]),
                    created_at=fake.date_time_between(start_date='-30d', end_date='today'),
                )
                saved_searches.append(saved_search)
        
        # Recruiter saved searches
        for recruiter in recruiters[:20]:
            if random.random() < 0.6:  # 60% chance
                saved_search = SavedSearch.objects.create(
                    user=recruiter.user,
                    name=f"{fake.word()} candidates",
                    query='python developer',
                    filters={'experience_level': 'mid', 'skills': ['Python', 'Django']},
                    search_type='candidate',
                    email_alerts=random.choice([True, False]),
                    created_at=fake.date_time_between(start_date='-30d', end_date='today'),
                )
                saved_searches.append(saved_search)
        
        return saved_searches

    def create_notifications(self, candidates, recruiters):
        """Create notifications."""
        notifications = []
        
        notification_types = [
            'application_received', 'application_status', 'interview_scheduled',
            'job_recommendation', 'profile_view', 'message_received',
            'job_posted', 'candidate_matched', 'system_alert'
        ]
        
        # Candidate notifications
        for candidate in candidates[:150]:
            num_notifications = random.randint(1, 20)
            for _ in range(num_notifications):
                notification = Notification.objects.create(
                    user=candidate.user,
                    type=random.choice(notification_types),
                    title=fake.sentence(),
                    message=fake.paragraph(nb_sentences=2),
                    read=random.choice([True, False]),
                    created_at=fake.date_time_between(start_date='-30d', end_date='today'),
                )
                notifications.append(notification)
        
        # Recruiter notifications
        for recruiter in recruiters[:25]:
            num_notifications = random.randint(1, 25)
            for _ in range(num_notifications):
                notification = Notification.objects.create(
                    user=recruiter.user,
                    type=random.choice(notification_types),
                    title=fake.sentence(),
                    message=fake.paragraph(nb_sentences=2),
                    read=random.choice([True, False]),
                    created_at=fake.date_time_between(start_date='-30d', end_date='today'),
                )
                notifications.append(notification)
        
        return notifications

    def create_analytics_events(self, candidates, recruiters):
        """Create analytics events."""
        events = []
        
        event_types = [
            'page_view', 'search', 'application_submit', 'profile_update',
            'job_view', 'candidate_view', 'interview_schedule', 'login',
            'logout', 'notification_click', 'recommendation_click'
        ]
        
        # Candidate events
        for candidate in candidates[:200]:
            num_events = random.randint(5, 50)
            for _ in range(num_events):
                event = AnalyticsEvent.objects.create(
                    user=candidate.user,
                    event_type=random.choice(event_types),
                    page=random.choice(['/jobs', '/profile', '/applications', '/recommendations']),
                    metadata={'referrer': 'direct', 'device': 'desktop'},
                    timestamp=fake.date_time_between(start_date='-30d', end_date='today'),
                )
                events.append(event)
        
        # Recruiter events
        for recruiter in recruiters[:30]:
            num_events = random.randint(5, 60)
            for _ in range(num_events):
                event = AnalyticsEvent.objects.create(
                    user=recruiter.user,
                    event_type=random.choice(event_types),
                    page=random.choice(['/dashboard', '/candidates', '/jobs', '/analytics']),
                    metadata={'referrer': 'direct', 'device': 'desktop'},
                    timestamp=fake.date_time_between(start_date='-30d', end_date='today'),
                )
                events.append(event)
        
        return events

    def create_feature_flags(self):
        """Create feature flags."""
        feature_flags = [
            FeatureFlag.objects.create(
                name='advanced_search',
                description='Enable advanced search functionality',
                enabled=True,
                rollout_percentage=100,
            ),
            FeatureFlag.objects.create(
                name='ai_recommendations',
                description='Enable AI-powered job recommendations',
                enabled=True,
                rollout_percentage=80,
            ),
            FeatureFlag.objects.create(
                name='video_interviews',
                description='Enable video interview scheduling',
                enabled=True,
                rollout_percentage=60,
            ),
            FeatureFlag.objects.create(
                name='resume_parsing',
                description='Enable automatic resume parsing',
                enabled=True,
                rollout_percentage=100,
            ),
            FeatureFlag.objects.create(
                name='analytics_dashboard',
                description='Enable analytics dashboard for recruiters',
                enabled=True,
                rollout_percentage=100,
            ),
            FeatureFlag.objects.create(
                name='mobile_app',
                description='Enable mobile app features',
                enabled=False,
                rollout_percentage=0,
            ),
            FeatureFlag.objects.create(
                name='real_time_notifications',
                description='Enable real-time push notifications',
                enabled=True,
                rollout_percentage=50,
            ),
        ]
        
        return feature_flags

    def create_audit_logs(self, recruiters, candidates):
        """Create audit logs."""
        audit_logs = []
        
        actions = [
            'create', 'update', 'delete', 'view', 'export', 'login', 'logout',
            'password_change', 'profile_update', 'job_post', 'application_submit'
        ]
        
        entity_types = [
            'User', 'Company', 'Job', 'Application', 'Interview',
            'CandidateProfile', 'RecruiterProfile', 'Skill'
        ]
        
        # Recruiter audit logs
        for recruiter in recruiters[:25]:
            num_logs = random.randint(10, 50)
            for _ in range(num_logs):
                log = AuditLog.objects.create(
                    user=recruiter.user,
                    action=random.choice(actions),
                    entity_type=random.choice(entity_types),
                    entity_id=random.randint(1, 1000),
                    ip_address=fake.ipv4(),
                    user_agent=fake.user_agent(),
                    timestamp=fake.date_time_between(start_date='-60d', end_date='today'),
                    details={'changes': fake.sentence()},
                )
                audit_logs.append(log)
        
        # Candidate audit logs
        for candidate in candidates[:150]:
            num_logs = random.randint(5, 30)
            for _ in range(num_logs):
                log = AuditLog.objects.create(
                    user=candidate.user,
                    action=random.choice(actions),
                    entity_type=random.choice(entity_types),
                    entity_id=random.randint(1, 1000),
                    ip_address=fake.ipv4(),
                    user_agent=fake.user_agent(),
                    timestamp=fake.date_time_between(start_date='-60d', end_date='today'),
                    details={'changes': fake.sentence()},
                )
                audit_logs.append(log)
        
        return audit_logs

    def create_security_events(self, candidates, recruiters):
        """Create security events."""
        security_events = []
        
        event_types = [
            'successful_login', 'failed_login', 'password_reset',
            'suspicious_activity', 'account_locked', 'mfa_enabled',
            'mfa_disabled', 'api_key_created', 'api_key_revoked',
            'data_export', 'profile_accessed'
        ]
        
        severity_levels = ['low', 'medium', 'high', 'critical']
        
        # Candidate security events
        for candidate in candidates[:200]:
            num_events = random.randint(1, 10)
            for _ in range(num_events):
                event = SecurityEvent.objects.create(
                    user=candidate.user,
                    event_type=random.choice(event_types),
                    severity=random.choice(severity_levels),
                    ip_address=fake.ipv4(),
                    user_agent=fake.user_agent(),
                    timestamp=fake.date_time_between(start_date='-60d', end_date='today'),
                    description=fake.sentence(),
                    resolved=random.choice([True, False]),
                )
                security_events.append(event)
        
        # Recruiter security events
        for recruiter in recruiters[:30]:
            num_events = random.randint(1, 15)
            for _ in range(num_events):
                event = SecurityEvent.objects.create(
                    user=recruiter.user,
                    event_type=random.choice(event_types),
                    severity=random.choice(severity_levels),
                    ip_address=fake.ipv4(),
                    user_agent=fake.user_agent(),
                    timestamp=fake.date_time_between(start_date='-60d', end_date='today'),
                    description=fake.sentence(),
                    resolved=random.choice([True, False]),
                )
                security_events.append(event)
        
        return security_events
