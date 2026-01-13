"""
URLs para Landing Page da Agência.
"""

from django.urls import path
from . import views_landing

urlpatterns = [
    path('landing/', views_landing.landing_config_view, name='landing_config'),
    path('landing/generate-ai/', views_landing.landing_generate_ai_view, name='landing_generate_ai'),
    path('landing/preview/', views_landing.landing_preview_view, name='landing_preview'),
    path('leads/', views_landing.leads_list_view, name='leads_list'),
    path('leads/<uuid:lead_id>/status/', views_landing.lead_status_update_view, name='lead_status_update'),
]
