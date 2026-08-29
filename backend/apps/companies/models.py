from django.db import models


class Company(models.Model):
    """
    Company representing a verified job source.
    
    A Company represents an official source from which MatchHire can retrieve jobs.
    This model supports the future scraper system by providing the necessary
    configuration to identify and fetch jobs from company career portals.
    
    Important architectural invariant:
    - A company represents an official source for job ingestion
    - Jobs must enter MatchHire only through verified sources
    - No public API allows arbitrary users to create jobs
    """
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text='Company name'
    )
    
    # Stable identifier for URL generation and external references
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text='URL-friendly identifier for the company'
    )
    
    # Official careers portal URL
    careers_url = models.URLField(
        max_length=500,
        help_text='Official company careers page URL'
    )
    
    # Active/inactive state for source management
    # Use soft deactivation instead of deletion to preserve historical data
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this company source is active for job fetching'
    )
    
    # Scraper configuration placeholder
    # Future scraper implementations will use this to store configuration
    # without requiring schema changes for each new scraper type
    scraper_config = models.JSONField(
        default=dict,
        blank=True,
        help_text='Configuration for the scraper implementation'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies'
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['name']
    
    def __str__(self):
        return self.name
