"""
Dashboard URLs for agency panel.
"""

from django.urls import path
from . import views_dashboard

app_name = 'dashboard'

urlpatterns = [
    path('', views_dashboard.dashboard_view, name='index'),
    path('settings/', views_dashboard.settings_view, name='settings'),
    path('usage/', views_dashboard.usage_view, name='usage'),
    path('settings/branding/', views_dashboard.branding_settings, name='branding_settings'),
]
