"""
Project model for PostPro.
Represents a WordPress site connected to the platform.
"""

import uuid
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken


class Project(models.Model):
    """
    WordPress project connected to PostPro.
    Each project represents a WordPress site with its own settings.
    """
    
    class Tone(models.TextChoices):
        FORMAL = 'formal', 'Formal'
        CASUAL = 'casual', 'Casual'
        TECHNICAL = 'technical', 'Technical'
    
    class ImageStyle(models.TextChoices):
        PHOTOGRAPHIC = 'photographic', 'Photographic'
        ILLUSTRATION = 'illustration', 'Illustration'
        MINIMALIST = 'minimalist', 'Minimalist'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency = models.ForeignKey(
        'agencies.Agency',
        on_delete=models.CASCADE,
        related_name='projects'
    )
    
    # Basic info
    name = models.CharField(max_length=255)
    wordpress_url = models.URLField(max_length=500)
    license_key = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    
    # AI model overrides (use agency defaults if empty)
    text_model = models.CharField(max_length=100, blank=True, null=True)
    image_model = models.CharField(max_length=100, blank=True, null=True)
    research_model = models.CharField(
        max_length=100, 
        default='perplexity/sonar',
        help_text='Modelo para pesquisa (ex: perplexity/sonar)'
    )
    
    # Content settings
    tone = models.CharField(
        max_length=20,
        choices=Tone.choices,
        default=Tone.CASUAL
    )
    image_style = models.CharField(
        max_length=20,
        choices=ImageStyle.choices,
        default=ImageStyle.PHOTOGRAPHIC
    )
    
    # WordPress credentials (encrypted)
    wordpress_username = models.CharField(max_length=100, blank=True)
    wordpress_app_password_encrypted = models.TextField(blank=True, null=True)
    
    # Stats
    total_posts_generated = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # ===== CLIENT CONTACT FIELDS =====
    client_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Nome do responsável pelo projeto"
    )
    client_email = models.EmailField(
        blank=True,
        help_text="Email do cliente (opcional)"
    )
    client_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="WhatsApp do cliente (ex: 5519999999999)"
    )
    
    # Magic Link Access
    magic_link_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Token para acesso público"
    )
    
    # WhatsApp Access Tracking
    access_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Último envio via WhatsApp"
    )
    access_sent_count = models.IntegerField(
        default=0,
        help_text="Quantidade de envios"
    )
    
    # ===== PLANO DO CLIENTE =====
    client_plan = models.ForeignKey(
        'agencies.AgencyClientPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects',
        help_text="Plano do cliente para este projeto"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'projects'
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.wordpress_url})"
    
    def _get_fernet(self):
        """Get Fernet instance for encryption."""
        key = settings.ENCRYPTION_KEY.encode() if settings.ENCRYPTION_KEY else Fernet.generate_key()
        return Fernet(key)
    
    def set_wordpress_password(self, password: str):
        """Encrypt and store WordPress app password."""
        if password:
            fernet = self._get_fernet()
            self.wordpress_app_password_encrypted = fernet.encrypt(password.encode()).decode()
        else:
            self.wordpress_app_password_encrypted = None
    
    def get_wordpress_password(self) -> str | None:
        """Decrypt and return WordPress app password."""
        if not self.wordpress_app_password_encrypted:
            return None
        try:
            fernet = self._get_fernet()
            return fernet.decrypt(self.wordpress_app_password_encrypted.encode()).decode()
        except InvalidToken:
            return None
    
    def get_text_model(self) -> str:
        """Get text model (project override or agency default)."""
        return self.text_model or self.agency.default_text_model
    
    def get_image_model(self) -> str:
        """Get image model (project override or agency default)."""
        return self.image_model or self.agency.default_image_model
    
    def get_research_model(self) -> str:
        """Get research model."""
        return self.research_model
    
    def regenerate_license_key(self):
        """Generate a new license key."""
        self.license_key = uuid.uuid4()
        self.save(update_fields=['license_key'])
    
    def increment_posts(self, count: int = 1):
        """Increment post counter."""
        self.total_posts_generated += count
        self.save(update_fields=['total_posts_generated'])
    
    def get_monthly_limit(self) -> int:
        """Retorna limite mensal de posts (do plano ou padrão da agência)."""
        if self.client_plan:
            return self.client_plan.posts_per_month
        return self.agency.monthly_posts_limit
    
    def get_current_month_posts(self) -> int:
        """Conta posts do mês atual para este projeto."""
        from django.utils import timezone
        now = timezone.now()
        return self.posts.filter(
            created_at__year=now.year,
            created_at__month=now.month
        ).count()
    
    def can_generate_post(self) -> bool:
        """Verifica se pode gerar mais posts baseado no plano."""
        return self.get_current_month_posts() < self.get_monthly_limit()
    
    def get_posts_remaining(self) -> int:
        """Retorna quantos posts restam neste mês."""
        return max(0, self.get_monthly_limit() - self.get_current_month_posts())
    
    def get_magic_link_url(self) -> str:
        """Get the public magic link URL for this project."""
        from django.conf import settings as django_settings
        base_url = getattr(django_settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
        return f"{base_url}/projects/setup/{self.magic_link_token}/"
    
    @property
    def content_settings(self):
        """Get or create content settings for this project."""
        settings, _ = ProjectContentSettings.objects.get_or_create(project=self)
        return settings


class ProjectContentSettings(models.Model):
    """
    Per-project content generation settings.
    Controls language, word count, optional elements, and custom instructions.
    """
    
    class Language(models.TextChoices):
        PT_BR = 'pt-BR', 'Português (Brasil)'
        PT_PT = 'pt-PT', 'Português (Portugal)'
        EN_US = 'en-US', 'English (US)'
        EN_GB = 'en-GB', 'English (UK)'
        ES_ES = 'es-ES', 'Español (España)'
        ES_MX = 'es-MX', 'Español (México)'
        FR_FR = 'fr-FR', 'Français'
        DE_DE = 'de-DE', 'Deutsch'
        IT_IT = 'it-IT', 'Italiano'
    
    class ResearchDepth(models.TextChoices):
        BASIC = 'basic', 'Básico (3 fontes)'
        STANDARD = 'standard', 'Padrão (5 fontes)'
        DEEP = 'deep', 'Profundo (10+ fontes)'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='content_settings_obj'
    )
    
    # Language Settings
    language = models.CharField(
        max_length=10,
        choices=Language.choices,
        default=Language.PT_BR,
        help_text='Idioma principal do conteúdo gerado'
    )
    
    # Content Structure
    min_word_count = models.PositiveIntegerField(
        default=1200,
        help_text='Mínimo de palavras por artigo'
    )
    max_word_count = models.PositiveIntegerField(
        default=2000,
        help_text='Máximo de palavras por artigo'
    )
    h2_sections_min = models.PositiveIntegerField(
        default=5,
        help_text='Mínimo de seções H2'
    )
    h2_sections_max = models.PositiveIntegerField(
        default=8,
        help_text='Máximo de seções H2'
    )
    
    # Optional Elements
    include_introduction = models.BooleanField(
        default=True,
        help_text='Incluir introdução engajante'
    )
    include_summary = models.BooleanField(
        default=False,
        help_text='Incluir resumo executivo no início'
    )
    include_faq = models.BooleanField(
        default=True,
        help_text='Incluir seção de perguntas frequentes'
    )
    faq_questions_count = models.PositiveIntegerField(
        default=5,
        help_text='Número de perguntas no FAQ'
    )
    include_conclusion = models.BooleanField(
        default=True,
        help_text='Incluir conclusão com CTA'
    )
    
    # Research Settings
    research_depth = models.CharField(
        max_length=20,
        choices=ResearchDepth.choices,
        default=ResearchDepth.STANDARD,
        help_text='Profundidade da pesquisa de dados'
    )
    research_recency_days = models.PositiveIntegerField(
        default=90,
        help_text='Considerar dados dos últimos X dias'
    )
    
    # Custom Instructions
    custom_writing_style = models.TextField(
        blank=True,
        help_text='Instruções de estilo (ex: "Use linguagem jovem, inclua emojis")'
    )
    custom_instructions = models.TextField(
        blank=True,
        help_text='Instruções adicionais para o gerador de conteúdo'
    )
    avoid_topics = models.TextField(
        blank=True,
        help_text='Tópicos a evitar, um por linha'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'project_content_settings'
        verbose_name = 'Project Content Settings'
        verbose_name_plural = 'Project Content Settings'
    
    def __str__(self):
        return f"Settings for {self.project.name}"
    
    def get_avoid_topics_list(self) -> list[str]:
        """Return avoid_topics as a list."""
        if not self.avoid_topics:
            return []
        return [t.strip() for t in self.avoid_topics.split('\n') if t.strip()]


class ProjectRSSSettings(models.Model):
    """
    Per-project RSS feed configuration for automated news generation.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='rss_settings'
    )
    
    # Feed Configuration
    feed_url = models.URLField(
        max_length=1000,
        blank=True,
        help_text='URL do feed RSS (ex: https://rss.app/feeds/xxx.xml)'
    )
    is_active = models.BooleanField(
        default=False,
        help_text='Ativar monitoramento automático do feed'
    )
    
    # Processing Settings
    check_interval_minutes = models.PositiveIntegerField(
        default=60,
        help_text='Intervalo entre verificações (minutos)'
    )
    auto_publish = models.BooleanField(
        default=False,
        help_text='Publicar automaticamente no WordPress'
    )
    max_posts_per_day = models.PositiveIntegerField(
        default=5,
        help_text='Limite máximo de posts por dia'
    )
    
    # Content Settings
    download_images = models.BooleanField(
        default=True,
        help_text='Baixar imagens do feed para Supabase'
    )
    include_source_attribution = models.BooleanField(
        default=True,
        help_text='Incluir atribuição à fonte original no post'
    )
    
    # Filtering
    required_keywords = models.JSONField(
        default=list,
        blank=True,
        help_text='Palavras-chave obrigatórias (título ou descrição deve conter)'
    )
    blocked_keywords = models.JSONField(
        default=list,
        blank=True,
        help_text='Palavras-chave bloqueadas (ignorar itens que contenham)'
    )
    
    # Tracking
    last_checked_at = models.DateTimeField(null=True, blank=True)
    items_processed_today = models.PositiveIntegerField(default=0)
    last_reset_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'project_rss_settings'
        verbose_name = 'Project RSS Settings'
        verbose_name_plural = 'Project RSS Settings'
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"RSS for {self.project.name} ({status})"
    
    def reset_daily_counter(self):
        """Reset daily counter if date changed."""
        from datetime import date
        today = date.today()
        if self.last_reset_date != today:
            self.items_processed_today = 0
            self.last_reset_date = today
            self.save(update_fields=['items_processed_today', 'last_reset_date'])
    
    def can_process_more_today(self) -> bool:
        """Check if we can process more items today."""
        self.reset_daily_counter()
        return self.items_processed_today < self.max_posts_per_day
    
    def increment_daily_counter(self):
        """Increment items processed today."""
        self.items_processed_today += 1
        self.save(update_fields=['items_processed_today'])


class RSSFeed(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='rss_feeds',
        help_text='Projeto ao qual este feed pertence'
    )
    name = models.CharField(max_length=255, blank=True, help_text="Nome opcional para identificar o feed")
    feed_url = models.URLField(max_length=1000, help_text="URL do feed RSS (XML)")
    is_active = models.BooleanField(default=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'project_rss_feeds'
        verbose_name = 'RSS Feed'
        verbose_name_plural = 'RSS Feeds'
        ordering = ['-created_at']

    def __str__(self):
        return self.name or self.feed_url
