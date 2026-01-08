"""
Agency model for PostPro.
Multi-tenant core entity with encrypted API keys.
"""

import uuid
from django.db import models
from django.utils.text import slugify
from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken
import requests


class Agency(models.Model):
    """
    Agency (tenant) model.
    Each agency has its own projects, team, and billing.
    """
    
    class Plan(models.TextChoices):
        STARTER = 'starter', 'Starter'
        PRO = 'pro', 'Pro'
        ENTERPRISE = 'enterprise', 'Enterprise'
    
    class SubscriptionStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PAST_DUE = 'past_due', 'Past Due'
        SUSPENDED = 'suspended', 'Suspended'
        CANCELED = 'canceled', 'Canceled'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    
    # Plan and limits
    plan = models.CharField(max_length=20, choices=Plan.choices, default=Plan.STARTER)
    max_projects = models.PositiveIntegerField(default=3)
    monthly_posts_limit = models.PositiveIntegerField(default=100)
    current_month_posts = models.PositiveIntegerField(default=0)
    
    # OpenRouter API (BYOK - encrypted)
    openrouter_api_key_encrypted = models.TextField(blank=True, null=True)
    default_text_model = models.CharField(
        max_length=100,
        default='anthropic/claude-3.5-sonnet'
    )
    default_image_model = models.CharField(
        max_length=100,
        default='openai/gpt-4o-mini'
    )
    
    # Billing
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agencies'
        verbose_name = 'Agency'
        verbose_name_plural = 'Agencies'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure unique slug
            counter = 1
            original_slug = self.slug
            while Agency.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def _get_fernet(self):
        """Get Fernet instance for encryption."""
        key = settings.ENCRYPTION_KEY.encode() if settings.ENCRYPTION_KEY else Fernet.generate_key()
        return Fernet(key)
    
    def set_openrouter_key(self, api_key: str):
        """Encrypt and store OpenRouter API key."""
        if api_key:
            fernet = self._get_fernet()
            self.openrouter_api_key_encrypted = fernet.encrypt(api_key.encode()).decode()
        else:
            self.openrouter_api_key_encrypted = None
    
    def get_openrouter_key(self) -> str | None:
        """Decrypt and return OpenRouter API key."""
        if not self.openrouter_api_key_encrypted:
            return None
        try:
            fernet = self._get_fernet()
            return fernet.decrypt(self.openrouter_api_key_encrypted.encode()).decode()
        except InvalidToken:
            return None
    
    def validate_openrouter_key(self) -> tuple[bool, str]:
        """Validate OpenRouter API key by making a test request."""
        api_key = self.get_openrouter_key()
        if not api_key:
            return False, 'No API key configured'
        
        try:
            response = requests.get(
                'https://openrouter.ai/api/v1/models',
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=10
            )
            
            if response.status_code == 200:
                return True, 'API key is valid'
            elif response.status_code == 401:
                return False, 'Invalid API key'
            elif response.status_code == 402:
                return False, 'Insufficient credits on OpenRouter'
            else:
                return False, f'OpenRouter error: {response.status_code}'
        except requests.RequestException as e:
            return False, f'Connection error: {str(e)}'
    
    @property
    def is_subscription_active(self):
        return self.subscription_status == self.SubscriptionStatus.ACTIVE
    
    @property
    def projects_count(self):
        return self.projects.count()
    
    @property
    def can_create_project(self):
        return self.projects_count < self.max_projects
    
    @property
    def posts_remaining(self):
        return max(0, self.monthly_posts_limit - self.current_month_posts)
    
    def reset_monthly_posts(self):
        """Reset monthly post counter (call on billing cycle)."""
        self.current_month_posts = 0
        self.save(update_fields=['current_month_posts'])
