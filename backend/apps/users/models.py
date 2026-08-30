from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication.
    
    This manager provides methods to create users and superusers using email
    as the primary identifier instead of username.
    """
    
    def create_user(self, email, username=None, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        
        Args:
            email: User's email address (required)
            username: Optional username (kept for compatibility with AbstractUser)
            password: User's password
            **extra_fields: Additional user fields
            
        Returns:
            User instance
            
        Raises:
            ValueError: If email is not provided
        """
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username=None, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        
        Args:
            email: Superuser's email address (required)
            username: Optional username
            password: Superuser's password
            **extra_fields: Additional user fields
            
        Returns:
            Superuser instance
            
        Raises:
            ValueError: If required superuser fields are invalid
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model for MatchHire.
    
    Extends Django's AbstractUser to provide authentication and user identity.
    Email is the primary identifier for authentication.
    
    Inherits from AbstractUser for compatibility with Django's authentication
    system, including password hashing, permissions, and admin integration.
    """
    email = models.EmailField(unique=True)
    username = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text='Optional username (kept for compatibility with AbstractUser)'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is USERNAME_FIELD, so no other required fields
    
    objects = UserManager()
    
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
