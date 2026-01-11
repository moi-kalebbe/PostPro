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



from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

def validate_image_size(file):
    """Valida tamanho máximo de 2MB para logos e 500KB para favicon"""
    limit_mb = 2 if 'logo' in file.name.lower() else 0.5
    limit_bytes = limit_mb * 1024 * 1024
    
    if file.size > limit_bytes:
        raise ValidationError(f'Arquivo muito grande. Máximo: {limit_mb}MB')

def agency_logo_path(instance, filename):
    """Path dinâmico: agencies/{agency_id}/logos/{filename}"""
    import os
    ext = os.path.splitext(filename)[1]
    return f'agencies/{instance.id}/logos/logo_light{ext}'

def agency_logo_dark_path(instance, filename):
    import os
    ext = os.path.splitext(filename)[1]
    return f'agencies/{instance.id}/logos/logo_dark{ext}'

def agency_favicon_path(instance, filename):
    import os
    ext = os.path.splitext(filename)[1]
    return f'agencies/{instance.id}/favicon{ext}'

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
        default='qwen/qwen3-32b',  # Melhor custo-benefício validado (ATUALIZADO 2026-01)
        help_text='Modelo de texto padrão para novos projetos'
    )
    default_image_model = models.CharField(
        max_length=100,
        default='pollinations/flux',  # Gratuito via Pollinations.ai
        help_text='Modelo de imagem padrão para novos projetos'
    )
    
    # Billing
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE
    )

    # ===== BRANDING FIELDS =====
    
    # Nome customizado (exibido no painel)
    display_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Nome exibido no painel. Se vazio, usa o campo 'name'"
    )
    
    # Logo Light (tema claro)
    logo_light = models.ImageField(
        upload_to=agency_logo_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['png', 'jpg', 'jpeg', 'svg', 'webp']),
            validate_image_size
        ],
        help_text="Logo para tema claro (PNG/SVG transparente, 200x50px recomendado)"
    )
    
    # Logo Dark (tema escuro)
    logo_dark = models.ImageField(
        upload_to=agency_logo_dark_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['png', 'jpg', 'jpeg', 'svg', 'webp']),
            validate_image_size
        ],
        help_text="Logo para tema escuro (PNG/SVG transparente, 200x50px recomendado)"
    )
    
    # Favicon
    favicon = models.ImageField(
        upload_to=agency_favicon_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['png', 'ico']),
            validate_image_size
        ],
        help_text="Favicon (ICO ou PNG, 32x32px ou 64x64px)"
    )
    
    # Cores do tema (override das variáveis CSS)
    primary_color = models.CharField(
        max_length=7,
        blank=True,
        default='#FF6B35',
        help_text="Cor primária em HEX (#FF6B35)"
    )
    
    secondary_color = models.CharField(
        max_length=7,
        blank=True,
        default='#004E89',
        help_text="Cor secundária em HEX"
    )
    
    # Meta
    branding_updated_at = models.DateTimeField(auto_now=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agencies'
        verbose_name = 'Agency'
        verbose_name_plural = 'Agencies'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.get_display_name()
    
    def get_display_name(self):
        """Retorna display_name ou fallback para name"""
        return self.display_name or self.name
    
    def get_logo_url(self, theme='light'):
        """Retorna URL do logo baseado no tema atual"""
        logo = self.logo_dark if theme == 'dark' else self.logo_light
        
        if logo and hasattr(logo, 'url'):
            return logo.url
        
        # Fallback para logo padrão PostPro
        return f'/static/img/logo-{theme}.png'
    
    def get_favicon_url(self):
        """Retorna URL do favicon ou padrão"""
        if self.favicon and hasattr(self.favicon, 'url'):
            return self.favicon.url
        return '/static/img/favicon.ico'
    
    def has_custom_branding(self):
        """Verifica se agência tem branding customizado"""
        return bool(self.logo_light or self.logo_dark or self.favicon)
    
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
