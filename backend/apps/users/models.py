from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for MatchHire.
    
    Extends Django's AbstractUser to provide authentication and user identity.
    This is early in the project, so we can establish a clean custom user model.
    """
    email = models.EmailField(unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.email


class UserProfile(models.Model):
    """
    User profile containing professional information for matching.
    
    This model stores structured profile data that will be populated
    through the future resume processing pipeline. It maintains a
    one-to-one relationship with the User model.
    
    JSONB fields are used for flexible extracted metadata that may
    vary between resume parsing implementations, while core fields
    remain structured for querying and matching.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='User'
    )
    
    # Core professional information
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text='Current or most recent job title'
    )
    years_of_experience = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text='Total years of professional experience'
    )
    
    # Location information
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text='Current location (city, state/country)'
    )
    
    # Skills and keywords (structured fields for matching)
    # Skills: A list of normalized concrete skills/capabilities/technologies.
    # Examples: ["python", "django", "postgresql", "redis"]
    # Keywords: A list of normalized broader terms extracted from profile content
    # useful for keyword/domain overlap.
    # Examples: ["backend", "distributed systems", "scalability", "rest api"]
    # The exact normalization algorithm belongs to future resume processing phases.
    skills = models.JSONField(
        default=list,
        blank=True,
        help_text='List of normalized concrete skills/capabilities/technologies'
    )
    keywords = models.JSONField(
        default=list,
        blank=True,
        help_text='List of normalized broader terms for keyword/domain overlap'
    )
    
    # Flexible metadata for resume parsing results
    # This allows the resume pipeline to store additional structured
    # data without requiring schema changes for each new field
    profile_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional structured metadata from resume processing'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.email} - Profile"
