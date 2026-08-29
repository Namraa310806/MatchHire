from django.test import TestCase
from .models import Company


class CompanyModelTest(TestCase):
    """Test Company model functionality."""
    
    def test_create_company(self):
        """Test creating a company."""
        company = Company.objects.create(
            name='Tech Corp',
            slug='tech-corp',
            careers_url='https://techcorp.com/careers'
        )
        self.assertEqual(company.name, 'Tech Corp')
        self.assertEqual(company.slug, 'tech-corp')
        self.assertTrue(company.is_active)
    
    def test_company_name_unique(self):
        """Test that company name is unique."""
        Company.objects.create(
            name='Tech Corp',
            slug='tech-corp',
            careers_url='https://techcorp.com/careers'
        )
        with self.assertRaises(Exception):
            Company.objects.create(
                name='Tech Corp',
                slug='tech-corp-2',
                careers_url='https://techcorp.com/careers2'
            )
    
    def test_company_slug_unique(self):
        """Test that company slug is unique."""
        Company.objects.create(
            name='Tech Corp',
            slug='tech-corp',
            careers_url='https://techcorp.com/careers'
        )
        with self.assertRaises(Exception):
            Company.objects.create(
                name='Tech Corp 2',
                slug='tech-corp',
                careers_url='https://techcorp.com/careers2'
            )
    
    def test_company_scraper_config_json(self):
        """Test JSONField for scraper configuration."""
        company = Company.objects.create(
            name='Tech Corp',
            slug='tech-corp',
            careers_url='https://techcorp.com/careers',
            scraper_config={'scraper_type': 'custom', 'rate_limit': 10}
        )
        self.assertEqual(company.scraper_config['scraper_type'], 'custom')
        self.assertEqual(company.scraper_config['rate_limit'], 10)
