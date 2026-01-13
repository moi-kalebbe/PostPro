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

# Limites por plano da plataforma
PLAN_LIMITS = {
    'starter': {'max_projects': 10, 'monthly_posts_limit': 100},
    'pro': {'max_projects': 50, 'monthly_posts_limit': 500},
    'enterprise': {'max_projects': 100, 'monthly_posts_limit': 2000},
}

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
    
    # Owner/Responsible information
    owner_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Nome do responsável pela agência"
    )
    owner_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Telefone do responsável (usado para login e WhatsApp)"
    )
    owner_email = models.EmailField(
        blank=True,
        help_text="Email do responsável (opcional)"
    )
    
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
    
    # ===== WHATSAPP/WUZAPI FIELDS =====
    wuzapi_instance_url = models.URLField(
        default="https://wuzapi.nuvemchat.com",
        help_text="URL da instância Wuzapi"
    )
    wuzapi_user_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID do usuário na Wuzapi"
    )
    wuzapi_token = models.CharField(
        max_length=255,
        blank=True,
        help_text="Token de autenticação"
    )
    wuzapi_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Número WhatsApp conectado"
    )
    wuzapi_connected = models.BooleanField(
        default=False,
        help_text="Status da conexão"
    )
    wuzapi_connected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data/hora da última conexão"
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


class AgencyClientPlan(models.Model):
    """
    Planos que cada agência cria para seus clientes.
    Cada agência pode definir seus próprios planos com limites e preços.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency = models.ForeignKey(
        Agency,
        on_delete=models.CASCADE,
        related_name='client_plans'
    )
    name = models.CharField(
        max_length=100,
        help_text="Nome do plano (ex: Bronze, Prata, Ouro)"
    )
    posts_per_month = models.PositiveIntegerField(
        default=30,
        help_text="Limite de posts por mês para clientes deste plano"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Preço mensal (opcional)"
    )
    
    # Campos para Landing Page
    description = models.TextField(
        blank=True,
        help_text="Descrição detalhada do plano"
    )
    features = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de features, ex: ["10 posts", "Suporte 24h"]'
    )
    is_highlighted = models.BooleanField(
        default=False,
        help_text="Destaque visual na landing page (plano recomendado)"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Ordem de exibição (menor = primeiro)"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agency_client_plans'
        verbose_name = 'Agency Client Plan'
        verbose_name_plural = 'Agency Client Plans'
        ordering = ['agency', 'order', 'posts_per_month']
    
    def __str__(self):
        return f"{self.agency.name} - {self.name} ({self.posts_per_month} posts/mês)"
    
    def get_features_list(self):
        """Retorna features como lista (para template)."""
        if isinstance(self.features, list):
            return self.features
        return []


class SuperAdminConfig(models.Model):
    """
    Configurações globais do SuperAdmin (singleton).
    Inclui configurações de WhatsApp para envio de credenciais.
    """
    # WhatsApp/Wuzapi settings (mesmo padrão da Agency)
    wuzapi_instance_url = models.URLField(
        default="https://wuzapi.nuvemchat.com",
        help_text="URL da instância Wuzapi"
    )
    wuzapi_user_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID do usuário na Wuzapi"
    )
    wuzapi_token = models.CharField(
        max_length=255,
        blank=True,
        help_text="Token de autenticação"
    )
    wuzapi_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Número WhatsApp conectado"
    )
    wuzapi_connected = models.BooleanField(
        default=False,
        help_text="Status da conexão"
    )
    wuzapi_connected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data/hora da última conexão"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'superadmin_config'
        verbose_name = 'Super Admin Config'
        verbose_name_plural = 'Super Admin Configs'
    
    def __str__(self):
        status = "Conectado" if self.wuzapi_connected else "Desconectado"
        return f"SuperAdmin Config - WhatsApp {status}"
    
    @classmethod
    def get_instance(cls):
        """Retorna a única instância ou cria uma nova."""
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance


class AgencyLandingPage(models.Model):
    """
    Configuração da Landing Page da agência.
    Cada agência pode ter uma landing page pública com conteúdo gerado por IA.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency = models.OneToOneField(
        Agency,
        on_delete=models.CASCADE,
        related_name='landing_page'
    )
    
    # Conteúdo gerado por IA
    hero_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Título principal do hero"
    )
    hero_subtitle = models.TextField(
        blank=True,
        help_text="Subtítulo/descrição do hero"
    )
    about_section = models.TextField(
        blank=True,
        help_text="Texto da seção 'Sobre'"
    )
    cta_text = models.CharField(
        max_length=100,
        default="Começar Agora",
        help_text="Texto do botão CTA principal"
    )
    
    # Meta SEO
    meta_title = models.CharField(
        max_length=60,
        blank=True,
        help_text="Título SEO (máx 60 caracteres)"
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="Descrição SEO (máx 160 caracteres)"
    )
    
    # Conteúdo Estendido (V2)
    extended_content = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Conteúdo Estendido',
        help_text='Conteúdo adicional gerado por IA (FAQ, benefits, pain points, etc)'
    )
    
    # Contato
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Número WhatsApp para contato (ex: 5511999999999)"
    )
    email_contact = models.EmailField(
        blank=True,
        help_text="Email para contato"
    )
    
    # Controle
    is_published = models.BooleanField(
        default=False,
        help_text="Landing page está publicada e acessível?"
    )
    ai_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Quando o conteúdo foi gerado pela IA"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agency_landing_pages'
        verbose_name = 'Agency Landing Page'
        verbose_name_plural = 'Agency Landing Pages'
    
    def __str__(self):
        status = "Publicada" if self.is_published else "Rascunho"
        return f"Landing - {self.agency.name} ({status})"
    
    def get_public_url(self):
        """Retorna a URL pública da landing page."""
        from django.urls import reverse
        return reverse('public_landing', kwargs={'slug': self.agency.slug})
    
    def has_content(self):
        """Verifica se tem conteúdo básico preenchido."""
        return bool(self.hero_title and self.hero_subtitle)


class AgencyLead(models.Model):
    """
    Leads capturados pela landing page da agência.
    Cada submissão de formulário gera um lead.
    """
    
    class Status(models.TextChoices):
        NEW = 'new', 'Novo'
        CONTACTED = 'contacted', 'Contatado'
        CONVERTED = 'converted', 'Convertido'
        LOST = 'lost', 'Perdido'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency = models.ForeignKey(
        Agency,
        on_delete=models.CASCADE,
        related_name='leads'
    )
    plan = models.ForeignKey(
        AgencyClientPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads',
        help_text="Plano de interesse selecionado pelo lead"
    )
    
    # Dados do lead
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nome da empresa/site do lead"
    )
    message = models.TextField(
        blank=True,
        help_text="Mensagem opcional do lead"
    )
    
    # UTM tracking
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    
    # Status do lead
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )
    
    # Notas internas
    notes = models.TextField(
        blank=True,
        help_text="Notas internas sobre o lead"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agency_leads'
        verbose_name = 'Agency Lead'
        verbose_name_plural = 'Agency Leads'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.agency.name} ({self.get_status_display()})"
