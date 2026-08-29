from django.db import models


class ApplyClick(models.Model):
    """
    ApplyClick model tracking when users apply to jobs.
    
    MatchHire does not submit job applications itself. The flow is:
    User -> MatchHire job -> Apply -> record click/event -> official company application URL
    
    This model supports analytics around this event without storing
    application form data, resumes, passwords, or sensitive information.
    
    Important architectural notes:
    - This does NOT store application form data
    - This does NOT store resumes or application answers
    - Analytics dashboards are deferred to later phases
    """
    
    # User reference
    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='apply_clicks',
        verbose_name='User',
        help_text='User who clicked apply (nullable for anonymous tracking if needed)'
    )
    
    # Job reference
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='apply_clicks',
        verbose_name='Job'
    )
    
    # Timestamp of the click event
    clicked_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the user clicked apply'
    )
    
    # Optional event metadata for analytics
    # This can store context like device type, referrer, etc.
    # without requiring schema changes for each new analytics field
    event_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional event metadata for analytics'
    )
    
    class Meta:
        db_table = 'apply_clicks'
        verbose_name = 'Apply Click'
        verbose_name_plural = 'Apply Clicks'
        ordering = ['-clicked_at']
        indexes = [
            models.Index(
                fields=['job', '-clicked_at'],
                name='idx_applyclick_job_clicked_at'
            ),
            models.Index(
                fields=['user', '-clicked_at'],
                name='idx_applyclick_user_clicked_at'
            )
        ]
    
    def __str__(self):
        return f"{self.user.email if self.user else 'Anonymous'} - {self.job.title} at {self.clicked_at}"
