"""
Dashboard URLs for agency panel.
"""

from django.urls import path
from . import views_dashboard
from . import views_plans
from . import views_landing

app_name = 'dashboard'

urlpatterns = [
    path('', views_dashboard.dashboard_view, name='index'),
    path('settings/', views_dashboard.settings_view, name='settings'),
    path('usage/', views_dashboard.usage_view, name='usage'),
    path('settings/branding/', views_dashboard.branding_settings, name='branding_settings'),
    
    # Planos de Cliente
    path('plans/', views_plans.plans_list_view, name='plans_list'),
    path('plans/create/', views_plans.plan_create_view, name='plan_create'),
    path('plans/<uuid:plan_id>/edit/', views_plans.plan_edit_view, name='plan_edit'),
    path('plans/<uuid:plan_id>/delete/', views_plans.plan_delete_view, name='plan_delete'),
    
    # Landing Page
    path('landing/', views_landing.landing_config_view, name='landing_config'),
    path('landing/generate-ai/', views_landing.landing_generate_ai_view, name='landing_generate_ai'),
    path('landing/preview/', views_landing.landing_preview_view, name='landing_preview'),
    
    # Leads
    path('leads/', views_landing.leads_list_view, name='leads_list'),
    path('leads/<uuid:lead_id>/status/', views_landing.lead_status_update_view, name='lead_status_update'),
]
