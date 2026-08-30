# Generated manually to add Spotify and Linear companies

from django.db import migrations


def add_spotify_and_linear_companies(apps, schema_editor):
    """Add Spotify and Linear companies to the database."""
    Company = apps.get_model('companies', 'Company')
    
    # Create Spotify company
    Company.objects.create(
        name='Spotify',
        slug='spotify',
        careers_url='https://jobs.lever.co/spotify',
        is_active=True,
        scraper_config={}
    )
    
    # Create Linear company
    Company.objects.create(
        name='Linear',
        slug='linear',
        careers_url='https://jobs.ashbyhq.com/linear',
        is_active=True,
        scraper_config={}
    )


def remove_spotify_and_linear_companies(apps, schema_editor):
    """Remove Spotify and Linear companies from the database."""
    Company = apps.get_model('companies', 'Company')
    
    Company.objects.filter(slug='spotify').delete()
    Company.objects.filter(slug='linear').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0002_company_idx_company_is_active'),
    ]

    operations = [
        migrations.RunPython(add_spotify_and_linear_companies, remove_spotify_and_linear_companies),
    ]
