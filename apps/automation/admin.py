"""
Admin configuration for automation app.
"""

from django.contrib import admin
from .models import BatchJob, Post, PostArtifact, IdempotencyKey, ActivityLog


@admin.register(BatchJob)
class BatchJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'status', 'total_rows', 'processed_rows', 'is_dry_run', 'created_at')
    list_filter = ('status', 'is_dry_run', 'project__agency')
    search_fields = ('project__name',)
    readonly_fields = ('id', 'created_at', 'completed_at')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'project', 'status', 'total_cost', 'wordpress_post_id', 'created_at')
    list_filter = ('status', 'project__agency')
    search_fields = ('keyword', 'title', 'project__name')
    readonly_fields = ('id', 'created_at', 'published_at')


@admin.register(PostArtifact)
class PostArtifactAdmin(admin.ModelAdmin):
    list_display = ('post', 'step', 'model_used', 'tokens_used', 'cost', 'is_active', 'created_at')
    list_filter = ('step', 'is_active')
    readonly_fields = ('id', 'created_at')


@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ('scope', 'key_hash', 'status', 'project', 'created_at')
    list_filter = ('scope', 'status')
    readonly_fields = ('id', 'created_at', 'completed_at')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor_user', 'agency', 'entity_type', 'created_at')
    list_filter = ('action', 'agency')
    search_fields = ('action', 'entity_type')
    readonly_fields = ('id', 'created_at')
