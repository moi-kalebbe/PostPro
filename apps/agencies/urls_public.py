"""
URLs públicas para Landing Pages das Agências.
"""

from django.urls import path
from . import views_public

urlpatterns = [
    path('<slug:slug>/', views_public.public_landing_view, name='public_landing'),
    path('<slug:slug>/lead/', views_public.public_lead_submit_view, name='public_lead_submit'),
]
