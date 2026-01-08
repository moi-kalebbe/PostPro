"""
Admin configuration for projects app.
"""

from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'agency', 'wordpress_url', 'tone', 'is_active', 'total_posts_generated', 'created_at')
    list_filter = ('agency', 'tone', 'image_style', 'is_active')
    search_fields = ('name', 'wordpress_url', 'agency__name')
    readonly_fields = ('id', 'license_key', 'total_posts_generated', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('id', 'agency', 'name', 'license_key')
        }),
        ('WordPress', {
            'fields': ('wordpress_url', 'wordpress_username')
        }),
        ('AI Settings', {
            'fields': ('text_model', 'image_model', 'tone', 'image_style')
        }),
        ('Status', {
            'fields': ('is_active', 'total_posts_generated')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
