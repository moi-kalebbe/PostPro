"""
Admin configuration for agencies app.
"""

from django.contrib import admin
from .models import Agency


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan', 'subscription_status', 'max_projects', 'current_month_posts', 'created_at')
    list_filter = ('plan', 'subscription_status')
    search_fields = ('name', 'slug')
    readonly_fields = ('id', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'slug')
        }),
        ('Plan & Limits', {
            'fields': ('plan', 'max_projects', 'monthly_posts_limit', 'current_month_posts')
        }),
        ('AI Configuration', {
            'fields': ('default_text_model', 'default_image_model'),
            'description': 'OpenRouter API key is encrypted and not shown here.'
        }),
        ('Billing', {
            'fields': ('stripe_customer_id', 'subscription_status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
