from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class MatchScore(models.Model):
    """
    MatchScore representing the persisted relationship between UserProfile and Job.
    
    This model stores the results of the future explainable matching engine.
    The matching formula is:
    - 50% skill similarity
    - 30% experience match
    - 20% keyword overlap
    
    This model enables the future matching system to explain why a user
    received a particular score by storing component scores.
    
    Important architectural notes:
    - This model does NOT implement the scoring algorithm in this phase
    - TF-IDF, embeddings, and matching logic are deferred to later phases
    - This is only the persistence layer for future matching results
    """
    
    # User profile reference
    user_profile = models.ForeignKey(
        'users.UserProfile',
        on_delete=models.CASCADE,
        related_name='match_scores',
        verbose_name='User Profile'
    )
    
    # Job reference
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='match_scores',
        verbose_name='Job'
    )
    
    # Final match score (0.0 to 1.0)
    final_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text='Final match score (0.0 to 1.0)'
    )
    
    # Component scores for explainability
    # These enable the matching system to explain why a score was calculated
    # All scores must be in the range 0.0 to 1.0
    skill_similarity_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text='Skill similarity component (50% weight)'
    )
    experience_match_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text='Experience match component (30% weight)'
    )
    keyword_overlap_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text='Keyword overlap component (20% weight)'
    )
    
    # Version information for tracking score updates
    # When a user's profile or a job changes, scores may be recalculated
    version = models.PositiveIntegerField(
        default=1,
        help_text='Version of the match score for tracking updates'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When this match score was first calculated'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When this match score was last recalculated'
    )
    
    class Meta:
        db_table = 'match_scores'
        verbose_name = 'Match Score'
        verbose_name_plural = 'Match Scores'
        ordering = ['-final_score']
        # Ensure a user has only one match score per job per version
        constraints = [
            models.UniqueConstraint(
                fields=['user_profile', 'job', 'version'],
                name='unique_user_job_version'
            )
        ]
    
    def __str__(self):
        return f"{self.user_profile.user.email} - {self.job.title} ({self.final_score})"
