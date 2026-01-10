"""
Admin configuration for projects app.
"""

from django.contrib import admin
from .models import Project, ProjectContentSettings


class ProjectContentSettingsInline(admin.StackedInline):
    """Inline editor for project content settings."""
    model = ProjectContentSettings
    can_delete = False
    verbose_name = 'Content Settings'
    verbose_name_plural = 'Content Settings'
    
    fieldsets = (
        ('🌍 Idioma', {
            'fields': ('language',),
            'description': 'Idioma principal para geração de conteúdo'
        }),
        ('📏 Estrutura do Artigo', {
            'fields': (
                ('min_word_count', 'max_word_count'),
                ('h2_sections_min', 'h2_sections_max'),
            ),
        }),
        ('✨ Elementos Opcionais', {
            'fields': (
                'include_introduction',
                'include_summary',
                ('include_faq', 'faq_questions_count'),
                'include_conclusion',
            ),
        }),
        ('🔍 Pesquisa', {
            'fields': (
                'research_depth',
                'research_recency_days',
            ),
            'classes': ('collapse',),
        }),
        ('✏️ Personalização', {
            'fields': (
                'custom_writing_style',
                'custom_instructions',
                'avoid_topics',
            ),
            'classes': ('collapse',),
        }),
    )


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'agency', 'wordpress_url', 'tone', 'is_active', 'total_posts_generated', 'created_at')
    list_filter = ('agency', 'tone', 'image_style', 'is_active')
    search_fields = ('name', 'wordpress_url', 'agency__name')
    readonly_fields = ('id', 'license_key', 'total_posts_generated', 'created_at', 'updated_at')
    inlines = [ProjectContentSettingsInline]
    
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


@admin.register(ProjectContentSettings)
class ProjectContentSettingsAdmin(admin.ModelAdmin):
    """Standalone admin for content settings (for bulk editing)."""
    list_display = ('project', 'language', 'min_word_count', 'include_faq', 'updated_at')
    list_filter = ('language', 'include_faq', 'include_summary', 'research_depth')
    search_fields = ('project__name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('project',)
        }),
        ('🌍 Idioma', {
            'fields': ('language',)
        }),
        ('📏 Estrutura do Artigo', {
            'fields': (
                ('min_word_count', 'max_word_count'),
                ('h2_sections_min', 'h2_sections_max'),
            )
        }),
        ('✨ Elementos Opcionais', {
            'fields': (
                'include_introduction',
                'include_summary',
                ('include_faq', 'faq_questions_count'),
                'include_conclusion',
            )
        }),
        ('🔍 Pesquisa', {
            'fields': (
                'research_depth',
                'research_recency_days',
            )
        }),
        ('✏️ Personalização', {
            'fields': (
                'custom_writing_style',
                'custom_instructions',
                'avoid_topics',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

