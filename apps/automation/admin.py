"""
Django admin configuration for automation app.
"""

from django.contrib import admin
from .models import (
    BatchJob, Post, PostArtifact, IdempotencyKey, ActivityLog,
    SiteProfile, TrendPack, EditorialPlan, EditorialPlanItem, AIModelPolicy
)


@admin.register(BatchJob)
class BatchJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'status', 'total_rows', 'processed_rows', 'progress_percent', 'created_at')
    list_filter = ('status', 'is_dry_run', 'created_at')
    search_fields = ('id', 'project__name', 'original_filename')
    readonly_fields = ('id', 'created_at', 'completed_at', 'progress_percent')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'project', 'original_filename', 'csv_file')
        }),
        ('Progress', {
            'fields': ('status', 'total_rows', 'processed_rows', 'progress_percent')
        }),
        ('Options', {
            'fields': ('is_dry_run', 'estimated_cost', 'options')
        }),
        ('Errors', {
            'fields': ('error_log',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at')
        }),
    )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'project', 'status', 'external_id', 'post_status', 'wordpress_post_id', 'created_at')
    list_filter = ('status', 'post_status', 'created_at')
    search_fields = ('keyword', 'title', 'external_id', 'project__name')
    readonly_fields = ('id', 'created_at', 'published_at', 'total_cost')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'batch_job', 'project', 'keyword', 'external_id')
        }),
        ('Content', {
            'fields': ('title', 'content', 'meta_description', 'featured_image_url')
        }),
        ('SEO', {
            'fields': ('seo_data',),
            'classes': ('collapse',)
        }),
        ('Status & Scheduling', {
            'fields': ('status', 'post_status', 'scheduled_at')
        }),
        ('AI Data', {
            'fields': ('research_data', 'strategy_data', 'step_state'),
            'classes': ('collapse',)
        }),
        ('WordPress', {
            'fields': ('wordpress_post_id', 'wordpress_idempotency_key', 'wordpress_edit_url')
        }),
        ('Costs', {
            'fields': ('text_generation_cost', 'image_generation_cost', 'total_cost', 'tokens_total')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'published_at')
        }),
    )


@admin.register(PostArtifact)
class PostArtifactAdmin(admin.ModelAdmin):
    list_display = ('post', 'step', 'model_used', 'is_active', 'cost', 'created_at')
    list_filter = ('step', 'is_active', 'created_at')
    search_fields = ('post__keyword', 'model_used')
    readonly_fields = ('id', 'created_at')


@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ('scope', 'key_hash', 'project', 'status', 'created_at')
    list_filter = ('scope', 'status', 'created_at')
    search_fields = ('key_hash', 'project__name')
    readonly_fields = ('id', 'created_at', 'completed_at')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor_user', 'agency', 'project', 'entity_type', 'created_at')
    list_filter = ('action', 'entity_type', 'created_at')
    search_fields = ('action', 'entity_id', 'actor_user__email')
    readonly_fields = ('id', 'created_at')


@admin.register(SiteProfile)
class SiteProfileAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'project', 'language', 'last_synced_at', 'created_at')
    list_filter = ('language', 'created_at', 'last_synced_at')
    search_fields = ('site_name', 'home_url', 'project__name')
    readonly_fields = ('id', 'created_at', 'last_synced_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'project', 'home_url', 'site_name', 'site_description', 'language')
        }),
        ('Content Analysis', {
            'fields': ('categories', 'tags', 'recent_posts', 'main_pages', 'sitemap_url'),
            'classes': ('collapse',)
        }),
        ('AI Analysis', {
            'fields': ('content_themes', 'tone_analysis', 'target_audience'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_synced_at')
        }),
    )


@admin.register(TrendPack)
class TrendPackAdmin(admin.ModelAdmin):
    list_display = ('id', 'agency', 'model_used', 'recency_days', 'tokens_used', 'cost', 'created_at', 'expires_at')
    list_filter = ('model_used', 'recency_days', 'created_at')
    search_fields = ('id', 'agency__name')
    readonly_fields = ('id', 'created_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'agency', 'keywords', 'recency_days')
        }),
        ('Perplexity Response', {
            'fields': ('model_used', 'insights'),
            'classes': ('collapse',)
        }),
        ('Cost', {
            'fields': ('tokens_used', 'cost')
        }),
        ('Cache', {
            'fields': ('created_at', 'expires_at')
        }),
    )


@admin.register(EditorialPlan)
class EditorialPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'status', 'start_date', 'posts_per_day', 'approved_by', 'created_at')
    list_filter = ('status', 'start_date', 'created_at')
    search_fields = ('id', 'project__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'project', 'site_profile', 'keywords')
        }),
        ('Trend Research', {
            'fields': ('trend_pack',)
        }),
        ('Status', {
            'fields': ('status', 'rejection_reason')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('Schedule', {
            'fields': ('start_date', 'posts_per_day')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(EditorialPlanItem)
class EditorialPlanItemAdmin(admin.ModelAdmin):
    list_display = ('day_index', 'title', 'plan', 'keyword_focus', 'status', 'scheduled_date', 'post')
    list_filter = ('status', 'scheduled_date', 'created_at')
    search_fields = ('title', 'keyword_focus', 'external_id', 'plan__project__name')
    readonly_fields = ('id', 'created_at', 'external_id')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'plan', 'day_index', 'external_id')
        }),
        ('Content', {
            'fields': ('title', 'keyword_focus', 'cluster', 'search_intent')
        }),
        ('Trends', {
            'fields': ('trend_references',),
            'classes': ('collapse',)
        }),
        ('Scheduling', {
            'fields': ('status', 'scheduled_date', 'post')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(AIModelPolicy)
class AIModelPolicyAdmin(admin.ModelAdmin):
    list_display = ('agency', 'preset_category', 'is_active', 'image_provider', 'created_at')
    list_filter = ('preset_category', 'is_active', 'image_provider', 'created_at')
    search_fields = ('agency__name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'agency', 'preset_category', 'is_active')
        }),
        ('Text Models', {
            'fields': (
                'planning_trends_model', 'planning_titles_model',
                'outline_model', 'article_model', 'seo_model',
                'qa_model', 'rewrite_model'
            )
        }),
        ('Perplexity Config', {
            'fields': ('max_search_requests_per_plan', 'trends_recency_days')
        }),
        ('Image Generation', {
            'fields': (
                'image_provider', 'image_model_openrouter',
                'pollinations_model', 'pollinations_width', 'pollinations_height',
                'pollinations_safe', 'pollinations_private',
                'pollinations_enhance', 'pollinations_nologo'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
