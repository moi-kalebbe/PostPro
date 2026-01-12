"""
Admin configuration for agencies app.
"""

from django.contrib import admin
from .models import Agency, AgencyClientPlan, SuperAdminConfig


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan', 'subscription_status', 'max_projects', 'current_month_posts', 'created_at')
    list_filter = ('plan', 'subscription_status')
    search_fields = ('name', 'slug', 'owner_name', 'owner_phone')
    readonly_fields = ('id', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'slug')
        }),
        ('Responsável', {
            'fields': ('owner_name', 'owner_phone', 'owner_email')
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


@admin.register(AgencyClientPlan)
class AgencyClientPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'agency', 'posts_per_month', 'price', 'is_active', 'created_at')
    list_filter = ('is_active', 'agency')
    search_fields = ('name', 'agency__name')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(SuperAdminConfig)
class SuperAdminConfigAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'wuzapi_connected', 'wuzapi_phone', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

