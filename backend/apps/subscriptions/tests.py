from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .models import Subscription
from apps.users.models import User


class SubscriptionModelTest(TestCase):
    """Test Subscription model functionality."""
    
    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
    
    def test_create_subscription(self):
        """Test creating a subscription."""
        now = timezone.now()
        subscription = Subscription.objects.create(
            user=self.user,
            plan=Subscription.Plan.PRO,
            status=Subscription.Status.ACTIVE,
            start_time=now,
            expiration_time=now + timedelta(days=30)
        )
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.plan, Subscription.Plan.PRO)
        self.assertEqual(subscription.status, Subscription.Status.ACTIVE)
    
    def test_subscription_plan_choices(self):
        """Test subscription plan choices."""
        now = timezone.now()
        subscription = Subscription.objects.create(
            user=self.user,
            plan=Subscription.Plan.PREMIUM,
            status=Subscription.Status.ACTIVE,
            start_time=now,
            expiration_time=now + timedelta(days=30)
        )
        self.assertEqual(subscription.plan, Subscription.Plan.PREMIUM)
    
    def test_subscription_status_choices(self):
        """Test subscription status choices."""
        now = timezone.now()
        subscription = Subscription.objects.create(
            user=self.user,
            plan=Subscription.Plan.FREE,
            status=Subscription.Status.EXPIRED,
            start_time=now,
            expiration_time=now
        )
        self.assertEqual(subscription.status, Subscription.Status.EXPIRED)
    
    def test_subscription_one_to_one_user(self):
        """Test one-to-one relationship between User and Subscription."""
        now = timezone.now()
        subscription1 = Subscription.objects.create(
            user=self.user,
            plan=Subscription.Plan.PRO,
            status=Subscription.Status.ACTIVE,
            start_time=now,
            expiration_time=now + timedelta(days=30)
        )
        # Creating another subscription for the same user should fail
        with self.assertRaises(Exception):
            Subscription.objects.create(
                user=self.user,
                plan=Subscription.Plan.PREMIUM,
                status=Subscription.Status.ACTIVE,
                start_time=now,
                expiration_time=now + timedelta(days=30)
            )
    
    def test_subscription_related_name(self):
        """Test related_name from User to Subscription."""
        now = timezone.now()
        subscription = Subscription.objects.create(
            user=self.user,
            plan=Subscription.Plan.PRO,
            status=Subscription.Status.ACTIVE,
            start_time=now,
            expiration_time=now + timedelta(days=30)
        )
        self.assertEqual(self.user.subscription, subscription)
