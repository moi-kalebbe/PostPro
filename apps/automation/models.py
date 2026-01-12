"""
Automation models for PostPro.
BatchJob, Post, PostArtifact, IdempotencyKey, ActivityLog.
"""

import uuid
import hashlib
from django.db import models
from django.utils import timezone


class BatchJob(models.Model):
    """
    Batch job for processing CSV/XLSX keyword imports.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='batch_jobs'
    )
    
    # File info
    csv_file = models.FileField(upload_to='batch_uploads/', blank=True, null=True)
    original_filename = models.CharField(max_length=255, blank=True)
    
    # Progress
    total_rows = models.PositiveIntegerField(default=0)
    processed_rows = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Error tracking
    error_log = models.JSONField(default=dict, blank=True)
    
    # Cost estimation (for dry-run)
    estimated_cost = models.DecimalField(
        max_digits=10, decimal_places=4, default=0
    )
    is_dry_run = models.BooleanField(default=False)
    
    # Options
    options = models.JSONField(default=dict, blank=True)
    # options = {
    #   "generate_images": true,
    #   "auto_publish": false,
    #   "dry_run": false
    # }
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'batch_jobs'
        verbose_name = 'Batch Job'
        verbose_name_plural = 'Batch Jobs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Batch {self.id} - {self.project.name} ({self.status})"
    
    @property
    def progress_percent(self):
        if self.total_rows == 0:
            return 0
        return int((self.processed_rows / self.total_rows) * 100)
    
    def mark_completed(self):
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def mark_failed(self, error: str):
        self.status = self.Status.FAILED
        self.completed_at = timezone.now()
        self.error_log['fatal_error'] = error
        self.save(update_fields=['status', 'completed_at', 'error_log'])


class Post(models.Model):
    """
    Generated blog post with full pipeline state.
    """
    
    class Status(models.TextChoices):
        GENERATING = 'generating', 'Generating'
        PENDING_REVIEW = 'pending_review', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        PUBLISHED = 'published', 'Published'
        FAILED = 'failed', 'Failed'
    
    class ArticleType(models.TextChoices):
        BLOG = 'blog', 'Blog Post'
        NEWS = 'news', 'News Article'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch_job = models.ForeignKey(
        BatchJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='posts'
    )
    
    # Content
    keyword = models.CharField(max_length=500)
    title = models.CharField(max_length=500, blank=True)
    content = models.TextField(blank=True)  # HTML
    meta_description = models.CharField(max_length=300, blank=True)
    featured_image_url = models.URLField(max_length=1000, blank=True)
    
    # AI pipeline data
    research_data = models.JSONField(default=dict, blank=True)
    strategy_data = models.JSONField(default=dict, blank=True)
    
    # Step state for reprocessing
    step_state = models.JSONField(default=dict, blank=True)
    # step_state = {
    #   "research": "completed",
    #   "strategy": "completed",
    #   "article": "completed",
    #   "image": "completed"
    # }
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.GENERATING
    )
    
    # NEW: External ID for idempotency
    external_id = models.CharField(max_length=100, unique=True, db_index=True, null=True, blank=True)
    # Format: {site_id}_{plan_id}_day_{day_index} OR {batch_id}_row_{index}
    
    # NEW: SEO data
    seo_data = models.JSONField(default=dict, blank=True)
    # {keyword, seo_title, seo_description, internal_link, faq, article_type, blog_posting_data}
    
    # NEW: Scheduled publishing
    post_status = models.CharField(max_length=20, default='draft')  # draft/future/publish
    scheduled_at = models.DateTimeField(null=True, blank=True)
    
    # NEW: Article type for SEO schema
    article_type = models.CharField(
        max_length=10,
        choices=ArticleType.choices,
        default=ArticleType.BLOG,
        help_text='Tipo de artigo: Blog Post ou News Article'
    )
    
    # NEW: Source attribution for RSS/News posts
    source_url = models.URLField(
        max_length=1000,
        blank=True,
        help_text='URL da notícia original (para posts RSS)'
    )
    source_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Nome do portal de origem'
    )
    
    # WordPress integration
    wordpress_post_id = models.PositiveIntegerField(null=True, blank=True)
    wordpress_idempotency_key = models.CharField(max_length=64, blank=True, null=True)
    wordpress_edit_url = models.URLField(max_length=1000, blank=True, null=True)
    
    # Cost tracking
    text_generation_cost = models.DecimalField(
        max_digits=10, decimal_places=6, default=0
    )
    image_generation_cost = models.DecimalField(
        max_digits=10, decimal_places=6, default=0
    )
    total_cost = models.DecimalField(
        max_digits=10, decimal_places=6, default=0
    )
    tokens_total = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'posts'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.keyword[:50]} ({self.status})"
    
    def generate_wordpress_idempotency_key(self):
        """Generate idempotency key for WordPress publish."""
        data = f"{self.project_id}:{self.id}:publish_v1"
        self.wordpress_idempotency_key = hashlib.sha256(data.encode()).hexdigest()
        return self.wordpress_idempotency_key
    
    def update_total_cost(self):
        """Recalculate total cost from text + image."""
        self.total_cost = self.text_generation_cost + self.image_generation_cost
        self.save(update_fields=['total_cost'])
    
    def mark_published(self, wordpress_post_id: int, edit_url: str = ''):
        """Mark post as published."""
        self.wordpress_post_id = wordpress_post_id
        self.wordpress_edit_url = edit_url
        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=[
            'wordpress_post_id', 'wordpress_edit_url',
            'status', 'published_at'
        ])


class PostArtifact(models.Model):
    """
    Versioned artifact for each pipeline step.
    Allows reprocessing without losing history.
    """
    
    class Step(models.TextChoices):
        RESEARCH = 'research', 'Research'
        STRATEGY = 'strategy', 'Strategy'
        ARTICLE = 'article', 'Article'
        IMAGE = 'image', 'Image'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='artifacts'
    )
    step = models.CharField(max_length=20, choices=Step.choices)
    
    # Prompts used
    input_prompt = models.TextField(blank=True)
    system_prompt = models.TextField(blank=True)
    
    # AI response
    model_used = models.CharField(max_length=100, blank=True)
    provider_response = models.JSONField(default=dict, blank=True)
    parsed_output = models.JSONField(default=dict, blank=True)
    
    # Stats
    tokens_used = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Active version flag
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'post_artifacts'
        verbose_name = 'Post Artifact'
        verbose_name_plural = 'Post Artifacts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', 'step', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.post.keyword[:30]} - {self.step} (active={self.is_active})"
    
    def deactivate_previous(self):
        """Deactivate previous artifacts for the same step."""
        PostArtifact.objects.filter(
            post=self.post,
            step=self.step,
            is_active=True
        ).exclude(id=self.id).update(is_active=False)


class IdempotencyKey(models.Model):
    """
    Idempotency keys to prevent duplicate operations.
    """
    
    class Scope(models.TextChoices):
        WORDPRESS_PUBLISH = 'wordpress_publish', 'WordPress Publish'
        POST_GENERATION = 'post_generation', 'Post Generation'
        BATCH_ROW = 'batch_row', 'Batch Row'
    
    class Status(models.TextChoices):
        RESERVED = 'reserved', 'Reserved'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scope = models.CharField(max_length=30, choices=Scope.choices)
    key_hash = models.CharField(max_length=64, unique=True, db_index=True)
    
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='idempotency_keys'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='idempotency_keys'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RESERVED
    )
    
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'idempotency_keys'
        verbose_name = 'Idempotency Key'
        verbose_name_plural = 'Idempotency Keys'
    
    def __str__(self):
        return f"{self.scope}: {self.key_hash[:16]}..."
    
    def complete(self, metadata: dict = None):
        """Mark key as completed."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        if metadata:
            self.metadata.update(metadata)
        self.save()
    
    def fail(self, error: str = None):
        """Mark key as failed."""
        self.status = self.Status.FAILED
        self.completed_at = timezone.now()
        if error:
            self.metadata['error'] = error
        self.save()


class ActivityLog(models.Model):
    """
    Audit log for important actions.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Actor
    actor_user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    
    # Context
    agency = models.ForeignKey(
        'agencies.Agency',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    
    # Action details
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'activity_logs'
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agency', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
    
    def __str__(self):
        actor = self.actor_user.email if self.actor_user else 'System'
        return f"{actor}: {self.action}"


class SiteProfile(models.Model):
    """
    Cached analysis of a WordPress site's existing content.
    Used for anti-cannibalization and context-aware content generation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='site_profiles'
    )
    
    # Site metadata
    home_url = models.URLField(max_length=500)
    site_name = models.CharField(max_length=255)
    site_description = models.TextField(blank=True)
    language = models.CharField(max_length=10, default='pt-BR')
    
    # Content analysis
    categories = models.JSONField(default=list, blank=True)  # [{name, slug, count}]
    tags = models.JSONField(default=list, blank=True)
    recent_posts = models.JSONField(default=list, blank=True)  # Last 20 posts
    main_pages = models.JSONField(default=list, blank=True)  # Top 10 pages
    sitemap_url = models.URLField(max_length=500, blank=True)
    
    # AI-generated summary
    content_themes = models.JSONField(default=list, blank=True)  # Detected themes/topics
    tone_analysis = models.TextField(blank=True)
    target_audience = models.TextField(blank=True)
    
    # Metadata
    last_synced_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'site_profiles'
        verbose_name = 'Site Profile'
        verbose_name_plural = 'Site Profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.site_name} ({self.project.name})"


class TrendPack(models.Model):
    """
    Cached trend research from Perplexity Sonar.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency = models.ForeignKey(
        'agencies.Agency',
        on_delete=models.CASCADE,
        related_name='trend_packs'
    )
    
    # Input
    keywords = models.JSONField(default=list)
    recency_days = models.PositiveIntegerField(default=7)  # 7 or 30
    
    # Perplexity response
    model_used = models.CharField(max_length=100)  # perplexity/sonar or sonar-pro-search
    insights = models.JSONField(default=list)  # 10-30 trend insights
    # Each insight: {title, summary, references: [{title, url, date}], relevance_score}
    
    # Cost tracking
    tokens_used = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Cache
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Auto-expire after 7 days
    
    class Meta:
        db_table = 'trend_packs'
        verbose_name = 'Trend Pack'
        verbose_name_plural = 'Trend Packs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"TrendPack {self.id} - {len(self.keywords)} keywords"


class EditorialPlan(models.Model):
    """
    30-day editorial plan with approval workflow.
    """
    class Status(models.TextChoices):
        GENERATING = 'generating', 'Generating'
        PENDING_APPROVAL = 'pending_approval', 'Pending Approval'
        APPROVED = 'approved', 'Approved'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        REJECTED = 'rejected', 'Rejected'
        FAILED = 'failed', 'Failed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='editorial_plans'
    )
    site_profile = models.ForeignKey(
        SiteProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='editorial_plans'
    )
    
    # Input keywords (5-10)
    keywords = models.JSONField(default=list)
    
    # Trend research
    trend_pack = models.ForeignKey(
        TrendPack,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='editorial_plans'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.GENERATING
    )
    
    # Approval
    approved_by = models.ForeignKey(
        'accounts.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_plans'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Publishing schedule
    start_date = models.DateField()
    posts_per_day = models.PositiveIntegerField(default=1)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'editorial_plans'
        verbose_name = 'Editorial Plan'
        verbose_name_plural = 'Editorial Plans'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Plan {self.id} - {self.project.name} ({self.status})"


class EditorialPlanItem(models.Model):
    """
    Individual title/topic in a 30-day plan.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SCHEDULED = 'scheduled', 'Scheduled'
        GENERATING = 'generating', 'Generating'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(
        EditorialPlan,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    # Generated title & metadata
    day_index = models.PositiveIntegerField()  # 1-30
    title = models.CharField(max_length=500)
    keyword_focus = models.CharField(max_length=200)
    cluster = models.CharField(max_length=100, blank=True)  # Topic cluster
    search_intent = models.CharField(max_length=50, blank=True)  # informational/commercial/navigational
    
    # Trend connection
    trend_references = models.JSONField(default=list, blank=True)  # Links to TrendPack insights
    
    # Scheduling
    scheduled_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Link to generated post
    post = models.ForeignKey(
        Post,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='editorial_plan_item'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    external_id = models.CharField(max_length=100, unique=True, db_index=True)
    # Format: {site_id}_{plan_id}_day_{day_index}
    
    class Meta:
        db_table = 'editorial_plan_items'
        verbose_name = 'Editorial Plan Item'
        verbose_name_plural = 'Editorial Plan Items'
        ordering = ['plan', 'day_index']
        indexes = [
            models.Index(fields=['plan', 'day_index']),
            models.Index(fields=['external_id']),
        ]
    
    def __str__(self):
        return f"Day {self.day_index}: {self.title[:50]}"
    
    def generate_external_id(self):
        """Generate external_id for idempotency."""
        project_id = str(self.plan.project_id)
        plan_id = str(self.plan.id)
        return f"{project_id}_{plan_id}_day_{self.day_index}"


class AIModelPolicy(models.Model):
    """
    Agency-level AI model configuration per stage.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency = models.ForeignKey(
        'agencies.Agency',
        on_delete=models.CASCADE,
        related_name='model_policies'
    )
    
    # Preset category (optional, for UI convenience)
    preset_category = models.CharField(max_length=20, blank=True)  # free/budget/premium
    
    # Text models by stage
    planning_trends_model = models.CharField(max_length=100, default='perplexity/sonar')
    planning_titles_model = models.CharField(max_length=100, default='mistralai/mistral-nemo')
    outline_model = models.CharField(max_length=100, default='mistralai/mistral-nemo')
    article_model = models.CharField(max_length=100, default='openai/gpt-oss-120b')
    seo_model = models.CharField(max_length=100, default='openai/gpt-5-nano')
    qa_model = models.CharField(max_length=100, default='openai/gpt-5-nano')
    rewrite_model = models.CharField(max_length=100, blank=True)  # For reprocessing
    
    # Perplexity config
    max_search_requests_per_plan = models.PositiveIntegerField(default=3)
    trends_recency_days = models.PositiveIntegerField(default=7)  # 7 or 30
    
    # Image generation
    image_provider = models.CharField(max_length=20, default='openrouter')  # openrouter | pollinations
    image_model_openrouter = models.CharField(max_length=100, blank=True)
    pollinations_model = models.CharField(max_length=100, blank=True)
    pollinations_width = models.PositiveIntegerField(default=1920)
    pollinations_height = models.PositiveIntegerField(default=1080)
    pollinations_safe = models.BooleanField(default=True)
    pollinations_private = models.BooleanField(default=True)
    pollinations_enhance = models.BooleanField(default=False)
    pollinations_nologo = models.BooleanField(default=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_model_policies'
        verbose_name = 'AI Model Policy'
        verbose_name_plural = 'AI Model Policies'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Policy for {self.agency.name} ({self.preset_category or 'custom'})"


class RSSItem(models.Model):
    """
    RSS feed item tracking for deduplication and processing.
    Each item represents a news article from an external RSS feed.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        SKIPPED = 'skipped', 'Skipped'
        FAILED = 'failed', 'Failed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='rss_items'
    )
    
    # Source data (from RSS feed)
    source_url = models.URLField(
        max_length=1000,
        db_index=True,
        help_text='URL original da notícia'
    )
    source_title = models.CharField(max_length=500)
    source_description = models.TextField(blank=True)
    source_image_url = models.URLField(max_length=1000, blank=True)
    source_published_at = models.DateTimeField(null=True, blank=True)
    source_author = models.CharField(max_length=255, blank=True)
    source_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text='SHA256 hash for deduplication'
    )
    
    # Processing status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    error_message = models.TextField(blank=True)
    
    # Generated post link
    post = models.ForeignKey(
        Post,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='rss_source_items'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'rss_items'
        verbose_name = 'RSS Item'
        verbose_name_plural = 'RSS Items'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'source_hash']),
            models.Index(fields=['project', 'status']),
        ]
        # Unique constraint: same URL per project
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'source_url'],
                name='unique_rss_item_per_project'
            )
        ]
    
    def __str__(self):
        return f"{self.source_title[:50]} ({self.status})"
    
    def mark_processing(self):
        """Mark item as being processed."""
        self.status = self.Status.PROCESSING
        self.save(update_fields=['status'])
    
    def mark_completed(self, post: Post):
        """Mark item as completed with generated post."""
        from django.utils import timezone
        self.status = self.Status.COMPLETED
        self.post = post
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'post', 'processed_at'])
    
    def mark_failed(self, error: str):
        """Mark item as failed with error message."""
        from django.utils import timezone
        self.status = self.Status.FAILED
        self.error_message = error
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'processed_at'])
    
    def mark_skipped(self, reason: str = ""):
        """Mark item as skipped (e.g., filtered out)."""
        from django.utils import timezone
        self.status = self.Status.SKIPPED
        self.error_message = reason
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'processed_at'])
