"""
Admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'agency', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'agency')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('PostPro', {'fields': ('role', 'agency')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('PostPro', {'fields': ('role', 'agency')}),
    )
