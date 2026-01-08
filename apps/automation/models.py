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
    
    # WordPress integration
    wordpress_post_id = models.PositiveIntegerField(null=True, blank=True)
    wordpress_idempotency_key = models.CharField(max_length=64, blank=True, null=True)
    wordpress_edit_url = models.URLField(max_length=1000, blank=True)
    
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
