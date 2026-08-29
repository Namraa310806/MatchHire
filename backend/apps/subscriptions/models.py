from django.db import models


class Subscription(models.Model):
    """
    Subscription model representing user subscription state.
    
    This model represents subscription state required by the future billing system.
    It does NOT implement Razorpay, payment endpoints, or webhooks in this phase.
    
    Important architectural notes:
    - This is only the persistence layer for subscription state
    - Payment processing logic is deferred to later phases
    - Pricing logic is not implemented in the model
    """
    
    class Plan(models.TextChoices):
        FREE = 'FREE', 'Free'
        PRO = 'PRO', 'Pro'
        PREMIUM = 'PREMIUM', 'Premium'
    
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        CANCELLED = 'CANCELLED', 'Cancelled'
        EXPIRED = 'EXPIRED', 'Expired'
        PENDING = 'PENDING', 'Pending'
    
    # User relationship
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name='User'
    )
    
    # Plan selection using controlled choices
    plan = models.CharField(
        max_length=20,
        choices=Plan.choices,
        default=Plan.FREE,
        help_text='Subscription plan'
    )
    
    # Payment provider subscription identifier
    # This will be populated by the future payment integration
    provider_subscription_id = models.CharField(
        max_length=200,
        blank=True,
        help_text='Payment provider subscription identifier (e.g., Razorpay subscription ID)'
    )
    
    # Subscription status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text='Subscription status'
    )
    
    # Time tracking
    start_time = models.DateTimeField(
        help_text='When the subscription started'
    )
    expiration_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the subscription expires or renews'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions'
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
    
    def __str__(self):
        return f"{self.user.email} - {self.plan} ({self.status})"
