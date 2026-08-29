from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.users.models import User, UserProfile
from apps.companies.models import Company
from apps.jobs.models import Job
from apps.matching.models import MatchScore
from apps.subscriptions.models import Subscription
from apps.analytics.models import ApplyClick


class Command(BaseCommand):
    help = 'Seed development data for local development and testing'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.seed_companies()
            self.seed_jobs()
            self.seed_users_and_profiles()
            self.seed_match_scores()
            self.seed_subscriptions()
            self.seed_apply_clicks()
            
            self.print_summary()

    def seed_companies(self):
        """Seed fictional development companies."""
        self.stdout.write('Seeding companies...')
        
        companies_data = [
            {
                'name': 'Nexus Technologies',
                'slug': 'nexus-technologies',
                'careers_url': 'https://careers.nexustech.example.test'
            },
            {
                'name': 'Quantum Systems',
                'slug': 'quantum-systems',
                'careers_url': 'https://careers.quantumsys.example.test'
            },
            {
                'name': 'Apex Innovations',
                'slug': 'apex-innovations',
                'careers_url': 'https://careers.apexinnov.example.test'
            },
            {
                'name': 'Stellar Dynamics',
                'slug': 'stellar-dynamics',
                'careers_url': 'https://careers.stellardyn.example.test'
            }
        ]
        
        for company_data in companies_data:
            company, created = Company.objects.get_or_create(
                slug=company_data['slug'],
                defaults={
                    'name': company_data['name'],
                    'careers_url': company_data['careers_url'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  Created company: {company.name}')
            else:
                self.stdout.write(f'  Reused company: {company.name}')

    def seed_jobs(self):
        """Seed fictional development jobs."""
        self.stdout.write('Seeding jobs...')
        
        nexus = Company.objects.get(slug='nexus-technologies')
        quantum = Company.objects.get(slug='quantum-systems')
        apex = Company.objects.get(slug='apex-innovations')
        stellar = Company.objects.get(slug='stellar-dynamics')
        
        jobs_data = [
            # Nexus Technologies jobs
            {
                'company': nexus,
                'external_job_id': 'NX-1001',
                'title': 'Senior Backend Engineer',
                'description': 'Build scalable backend systems using Python and Django. Work on distributed systems architecture and API development.',
                'location': 'San Francisco, CA',
                'employment_type': Job.EmploymentType.FULL_TIME,
                'experience_required': '5-7 years',
                'minimum_experience_years': 5.0,
                'maximum_experience_years': 7.0,
                'skills': ['python', 'django', 'postgresql', 'redis', 'docker'],
                'keywords': ['backend', 'distributed systems', 'api', 'scalability'],
                'application_url': 'https://careers.nexustech.example.test/jobs/NX-1001',
                'source_url': 'https://careers.nexustech.example.test/jobs/NX-1001',
                'deduplication_hash': 'nexus-nx-1001-hash'
            },
            {
                'company': nexus,
                'external_job_id': 'NX-1002',
                'title': 'DevOps Engineer',
                'description': 'Manage cloud infrastructure and CI/CD pipelines. Implement monitoring and automation solutions.',
                'location': 'Remote',
                'employment_type': Job.EmploymentType.REMOTE,
                'experience_required': '3-5 years',
                'minimum_experience_years': 3.0,
                'maximum_experience_years': 5.0,
                'skills': ['aws', 'kubernetes', 'docker', 'terraform', 'ansible'],
                'keywords': ['devops', 'cloud', 'infrastructure', 'automation'],
                'application_url': 'https://careers.nexustech.example.test/jobs/NX-1002',
                'source_url': 'https://careers.nexustech.example.test/jobs/NX-1002',
                'deduplication_hash': 'nexus-nx-1002-hash'
            },
            {
                'company': nexus,
                'external_job_id': 'NX-1003',
                'title': 'Full Stack Developer',
                'description': 'Develop both frontend and backend components. Work with React and Django to build complete web applications.',
                'location': 'New York, NY',
                'employment_type': Job.EmploymentType.FULL_TIME,
                'experience_required': '2-4 years',
                'minimum_experience_years': 2.0,
                'maximum_experience_years': 4.0,
                'skills': ['python', 'django', 'react', 'javascript', 'postgresql'],
                'keywords': ['full stack', 'web development', 'frontend', 'backend'],
                'application_url': 'https://careers.nexustech.example.test/jobs/NX-1003',
                'source_url': 'https://careers.nexustech.example.test/jobs/NX-1003',
                'deduplication_hash': 'nexus-nx-1003-hash'
            },
            # Quantum Systems jobs
            {
                'company': quantum,
                'external_job_id': 'QS-2001',
                'title': 'Machine Learning Engineer',
                'description': 'Develop and deploy machine learning models. Work on data pipelines and model optimization.',
                'location': 'Seattle, WA',
                'employment_type': Job.EmploymentType.FULL_TIME,
                'experience_required': '4-6 years',
                'minimum_experience_years': 4.0,
                'maximum_experience_years': 6.0,
                'skills': ['python', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas'],
                'keywords': ['machine learning', 'ai', 'data science', 'ml'],
                'application_url': 'https://careers.quantumsys.example.test/jobs/QS-2001',
                'source_url': 'https://careers.quantumsys.example.test/jobs/QS-2001',
                'deduplication_hash': 'quantum-qs-2001-hash'
            },
            {
                'company': quantum,
                'external_job_id': 'QS-2002',
                'title': 'Data Engineer',
                'description': 'Build and maintain data infrastructure. Design ETL pipelines and data warehouses.',
                'location': 'Austin, TX',
                'employment_type': Job.EmploymentType.FULL_TIME,
                'experience_required': '3-5 years',
                'minimum_experience_years': 3.0,
                'maximum_experience_years': 5.0,
                'skills': ['python', 'sql', 'spark', 'airflow', 'postgresql'],
                'keywords': ['data engineering', 'etl', 'data pipeline', 'big data'],
                'application_url': 'https://careers.quantumsys.example.test/jobs/QS-2002',
                'source_url': 'https://careers.quantumsys.example.test/jobs/QS-2002',
                'deduplication_hash': 'quantum-qs-2002-hash'
            },
            {
                'company': quantum,
                'external_job_id': 'QS-2003',
                'title': 'Research Scientist',
                'description': 'Conduct research in artificial intelligence and machine learning. Publish papers and develop novel algorithms.',
                'location': 'Remote',
                'employment_type': Job.EmploymentType.REMOTE,
                'experience_required': '5+ years',
                'minimum_experience_years': 5.0,
                'maximum_experience_years': None,
                'skills': ['python', 'tensorflow', 'pytorch', 'mathematics', 'statistics'],
                'keywords': ['research', 'ai research', 'machine learning', 'deep learning'],
                'application_url': 'https://careers.quantumsys.example.test/jobs/QS-2003',
                'source_url': 'https://careers.quantumsys.example.test/jobs/QS-2003',
                'deduplication_hash': 'quantum-qs-2003-hash'
            },
            # Apex Innovations jobs
            {
                'company': apex,
                'external_job_id': 'AP-3001',
                'title': 'Frontend Engineer',
                'description': 'Build responsive and accessible user interfaces. Work with React and modern CSS frameworks.',
                'location': 'Los Angeles, CA',
                'employment_type': Job.EmploymentType.FULL_TIME,
                'experience_required': '2-4 years',
                'minimum_experience_years': 2.0,
                'maximum_experience_years': 4.0,
                'skills': ['react', 'javascript', 'typescript', 'css', 'html'],
                'keywords': ['frontend', 'ui', 'ux', 'web development'],
                'application_url': 'https://careers.apexinnov.example.test/jobs/AP-3001',
                'source_url': 'https://careers.apexinnov.example.test/jobs/AP-3001',
                'deduplication_hash': 'apex-ap-3001-hash'
            },
            {
                'company': apex,
                'external_job_id': 'AP-3002',
                'title': 'Mobile Developer',
                'description': 'Develop mobile applications for iOS and Android. Work with React Native and native platforms.',
                'location': 'Chicago, IL',
                'employment_type': Job.EmploymentType.FULL_TIME,
                'experience_required': '3-5 years',
                'minimum_experience_years': 3.0,
                'maximum_experience_years': 5.0,
                'skills': ['react native', 'ios', 'android', 'javascript', 'typescript'],
                'keywords': ['mobile', 'ios', 'android', 'react native'],
                'application_url': 'https://careers.apexinnov.example.test/jobs/AP-3002',
                'source_url': 'https://careers.apexinnov.example.test/jobs/AP-3002',
                'deduplication_hash': 'apex-ap-3002-hash'
            },
            # Stellar Dynamics jobs
            {
                'company': stellar,
                'external_job_id': 'SD-4001',
                'title': 'Platform Engineer',
                'description': 'Build internal developer platforms and tools. Improve developer productivity and infrastructure reliability.',
                'location': 'Boston, MA',
                'employment_type': Job.EmploymentType.FULL_TIME,
                'experience_required': '4-6 years',
                'minimum_experience_years': 4.0,
                'maximum_experience_years': 6.0,
                'skills': ['go', 'kubernetes', 'docker', 'terraform', 'aws'],
                'keywords': ['platform', 'infrastructure', 'developer tools', 'devops'],
                'application_url': 'https://careers.stellardyn.example.test/jobs/SD-4001',
                'source_url': 'https://careers.stellardyn.example.test/jobs/SD-4001',
                'deduplication_hash': 'stellar-sd-4001-hash'
            },
            {
                'company': stellar,
                'external_job_id': 'SD-4002',
                'title': 'Security Engineer',
                'description': 'Implement security best practices and conduct security audits. Protect systems and data from threats.',
                'location': 'Remote',
                'employment_type': Job.EmploymentType.REMOTE,
                'experience_required': '3-5 years',
                'minimum_experience_years': 3.0,
                'maximum_experience_years': 5.0,
                'skills': ['security', 'penetration testing', 'cryptography', 'python', 'aws'],
                'keywords': ['security', 'cybersecurity', 'infosec', 'audit'],
                'application_url': 'https://careers.stellardyn.example.test/jobs/SD-4002',
                'source_url': 'https://careers.stellardyn.example.test/jobs/SD-4002',
                'deduplication_hash': 'stellar-sd-4002-hash'
            },
            {
                'company': stellar,
                'external_job_id': 'SD-4003',
                'title': 'Site Reliability Engineer',
                'description': 'Ensure system reliability and performance. Build monitoring and alerting systems.',
                'location': 'Denver, CO',
                'employment_type': Job.EmploymentType.FULL_TIME,
                'experience_required': '3-5 years',
                'minimum_experience_years': 3.0,
                'maximum_experience_years': 5.0,
                'skills': ['sre', 'monitoring', 'kubernetes', 'python', 'prometheus'],
                'keywords': ['sre', 'reliability', 'monitoring', 'observability'],
                'application_url': 'https://careers.stellardyn.example.test/jobs/SD-4003',
                'source_url': 'https://careers.stellardyn.example.test/jobs/SD-4003',
                'deduplication_hash': 'stellar-sd-4003-hash'
            }
        ]
        
        for job_data in jobs_data:
            job, created = Job.objects.get_or_create(
                company=job_data['company'],
                external_job_id=job_data['external_job_id'],
                defaults={
                    'title': job_data['title'],
                    'description': job_data['description'],
                    'location': job_data['location'],
                    'employment_type': job_data['employment_type'],
                    'experience_required': job_data['experience_required'],
                    'minimum_experience_years': job_data['minimum_experience_years'],
                    'maximum_experience_years': job_data['maximum_experience_years'],
                    'skills': job_data['skills'],
                    'keywords': job_data['keywords'],
                    'application_url': job_data['application_url'],
                    'source_url': job_data['source_url'],
                    'deduplication_hash': job_data['deduplication_hash'],
                    'status': Job.JobStatus.ACTIVE
                }
            )
            if created:
                self.stdout.write(f'  Created job: {job.company.name} - {job.title}')
            else:
                self.stdout.write(f'  Reused job: {job.company.name} - {job.title}')

    def seed_users_and_profiles(self):
        """Seed fictional development users and profiles."""
        self.stdout.write('Seeding users and profiles...')
        
        users_data = [
            {
                'email': 'dev.user1@example.test',
                'username': 'devuser1',
                'password': 'devpass123',
                'title': 'Senior Software Engineer',
                'years_of_experience': 6.0,
                'location': 'San Francisco, CA',
                'skills': ['python', 'django', 'postgresql', 'redis', 'docker'],
                'keywords': ['backend', 'distributed systems', 'api', 'scalability']
            },
            {
                'email': 'dev.user2@example.test',
                'username': 'devuser2',
                'password': 'devpass123',
                'title': 'Full Stack Developer',
                'years_of_experience': 4.0,
                'location': 'New York, NY',
                'skills': ['python', 'django', 'react', 'javascript', 'postgresql'],
                'keywords': ['full stack', 'web development', 'frontend', 'backend']
            }
        ]
        
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'username': user_data['username'],
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f'  Created user: {user.email}')
            else:
                self.stdout.write(f'  Reused user: {user.email}')
            
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'title': user_data['title'],
                    'years_of_experience': user_data['years_of_experience'],
                    'location': user_data['location'],
                    'skills': user_data['skills'],
                    'keywords': user_data['keywords']
                }
            )
            if profile_created:
                self.stdout.write(f'    Created profile for: {user.email}')
            else:
                self.stdout.write(f'    Reused profile for: {user.email}')

    def seed_match_scores(self):
        """Seed fictional match scores."""
        self.stdout.write('Seeding match scores...')
        
        user1 = User.objects.get(email='dev.user1@example.test')
        user2 = User.objects.get(email='dev.user2@example.test')
        profile1 = user1.profile
        profile2 = user2.profile
        
        # Get some jobs
        nexus_backend = Job.objects.get(external_job_id='NX-1001')
        nexus_devops = Job.objects.get(external_job_id='NX-1002')
        quantum_ml = Job.objects.get(external_job_id='QS-2001')
        quantum_data = Job.objects.get(external_job_id='QS-2002')
        apex_frontend = Job.objects.get(external_job_id='AP-3001')
        stellar_platform = Job.objects.get(external_job_id='SD-4001')
        
        match_scores_data = [
            # User 1 (backend engineer) matches
            {
                'user_profile': profile1,
                'job': nexus_backend,
                'final_score': Decimal('0.9200'),
                'skill_similarity_score': Decimal('0.9500'),
                'experience_match_score': Decimal('0.9000'),
                'keyword_overlap_score': Decimal('0.8500'),
                'version': 1
            },
            {
                'user_profile': profile1,
                'job': nexus_devops,
                'final_score': Decimal('0.7500'),
                'skill_similarity_score': Decimal('0.7000'),
                'experience_match_score': Decimal('0.8000'),
                'keyword_overlap_score': Decimal('0.8000'),
                'version': 1
            },
            {
                'user_profile': profile1,
                'job': quantum_ml,
                'final_score': Decimal('0.6500'),
                'skill_similarity_score': Decimal('0.6000'),
                'experience_match_score': Decimal('0.7000'),
                'keyword_overlap_score': Decimal('0.7000'),
                'version': 1
            },
            {
                'user_profile': profile1,
                'job': quantum_data,
                'final_score': Decimal('0.7000'),
                'skill_similarity_score': Decimal('0.7000'),
                'experience_match_score': Decimal('0.7000'),
                'keyword_overlap_score': Decimal('0.7000'),
                'version': 1
            },
            # User 2 (full stack developer) matches
            {
                'user_profile': profile2,
                'job': nexus_backend,
                'final_score': Decimal('0.7800'),
                'skill_similarity_score': Decimal('0.8000'),
                'experience_match_score': Decimal('0.7500'),
                'keyword_overlap_score': Decimal('0.7500'),
                'version': 1
            },
            {
                'user_profile': profile2,
                'job': apex_frontend,
                'final_score': Decimal('0.8500'),
                'skill_similarity_score': Decimal('0.9000'),
                'experience_match_score': Decimal('0.8000'),
                'keyword_overlap_score': Decimal('0.8000'),
                'version': 1
            },
            {
                'user_profile': profile2,
                'job': stellar_platform,
                'final_score': Decimal('0.6000'),
                'skill_similarity_score': Decimal('0.6000'),
                'experience_match_score': Decimal('0.6000'),
                'keyword_overlap_score': Decimal('0.6000'),
                'version': 1
            },
            {
                'user_profile': profile2,
                'job': quantum_data,
                'final_score': Decimal('0.7200'),
                'skill_similarity_score': Decimal('0.7500'),
                'experience_match_score': Decimal('0.7000'),
                'keyword_overlap_score': Decimal('0.7000'),
                'version': 1
            }
        ]
        
        for score_data in match_scores_data:
            match_score, created = MatchScore.objects.get_or_create(
                user_profile=score_data['user_profile'],
                job=score_data['job'],
                version=score_data['version'],
                defaults={
                    'final_score': score_data['final_score'],
                    'skill_similarity_score': score_data['skill_similarity_score'],
                    'experience_match_score': score_data['experience_match_score'],
                    'keyword_overlap_score': score_data['keyword_overlap_score']
                }
            )
            if created:
                self.stdout.write(f'  Created match score: {match_score.user_profile.user.email} - {match_score.job.title}')
            else:
                self.stdout.write(f'  Reused match score: {match_score.user_profile.user.email} - {match_score.job.title}')

    def seed_subscriptions(self):
        """Seed fictional development subscriptions."""
        self.stdout.write('Seeding subscriptions...')
        
        user1 = User.objects.get(email='dev.user1@example.test')
        user2 = User.objects.get(email='dev.user2@example.test')
        
        now = timezone.now()
        
        subscriptions_data = [
            {
                'user': user1,
                'plan': Subscription.Plan.PRO,
                'status': Subscription.Status.ACTIVE,
                'start_time': now - timedelta(days=15),
                'expiration_time': now + timedelta(days=15),
                'provider_subscription_id': 'dev-pro-sub-001'
            },
            {
                'user': user2,
                'plan': Subscription.Plan.FREE,
                'status': Subscription.Status.ACTIVE,
                'start_time': now - timedelta(days=30),
                'expiration_time': None,
                'provider_subscription_id': ''
            }
        ]
        
        for sub_data in subscriptions_data:
            subscription, created = Subscription.objects.get_or_create(
                user=sub_data['user'],
                defaults={
                    'plan': sub_data['plan'],
                    'status': sub_data['status'],
                    'start_time': sub_data['start_time'],
                    'expiration_time': sub_data['expiration_time'],
                    'provider_subscription_id': sub_data['provider_subscription_id']
                }
            )
            if created:
                self.stdout.write(f'  Created subscription: {subscription.user.email} - {subscription.plan}')
            else:
                self.stdout.write(f'  Reused subscription: {subscription.user.email} - {subscription.plan}')

    def seed_apply_clicks(self):
        """Seed fictional apply click events."""
        self.stdout.write('Seeding apply clicks...')
        
        user1 = User.objects.get(email='dev.user1@example.test')
        user2 = User.objects.get(email='dev.user2@example.test')
        
        nexus_backend = Job.objects.get(external_job_id='NX-1001')
        apex_frontend = Job.objects.get(external_job_id='AP-3001')
        quantum_ml = Job.objects.get(external_job_id='QS-2001')
        
        apply_clicks_data = [
            {
                'user': user1,
                'job': nexus_backend
            },
            {
                'user': user1,
                'job': quantum_ml
            },
            {
                'user': user2,
                'job': apex_frontend
            },
            {
                'user': user2,
                'job': nexus_backend
            }
        ]
        
        for click_data in apply_clicks_data:
            # Check if an apply click already exists for this user/job combination
            existing = ApplyClick.objects.filter(
                user=click_data['user'],
                job=click_data['job']
            ).first()
            
            if existing:
                self.stdout.write(f'  Reused apply click: {existing.user.email} - {existing.job.title}')
            else:
                apply_click = ApplyClick.objects.create(
                    user=click_data['user'],
                    job=click_data['job']
                )
                self.stdout.write(f'  Created apply click: {apply_click.user.email} - {apply_click.job.title}')

    def print_summary(self):
        """Print summary of seeded data."""
        self.stdout.write(self.style.SUCCESS('\nSeeded development data successfully.'))
        self.stdout.write(f'Companies: {Company.objects.count()}')
        self.stdout.write(f'Jobs: {Job.objects.count()}')
        self.stdout.write(f'Users: {User.objects.count()}')
        self.stdout.write(f'Profiles: {UserProfile.objects.count()}')
        self.stdout.write(f'Match scores: {MatchScore.objects.count()}')
        self.stdout.write(f'Subscriptions: {Subscription.objects.count()}')
        self.stdout.write(f'Apply clicks: {ApplyClick.objects.count()}')
