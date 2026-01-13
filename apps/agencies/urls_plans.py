"""
URLs para CRUD de Planos de Cliente.
"""

from django.urls import path
from . import views_plans

# Estas URLs serão incluídas em urls_dashboard.py ou diretamente no app
urlpatterns = [
    path('plans/', views_plans.plans_list_view, name='plans_list'),
    path('plans/create/', views_plans.plan_create_view, name='plan_create'),
    path('plans/<uuid:plan_id>/edit/', views_plans.plan_edit_view, name='plan_edit'),
    path('plans/<uuid:plan_id>/delete/', views_plans.plan_delete_view, name='plan_delete'),
]
