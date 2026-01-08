"""
Admin panel URLs for super admins.
"""

from django.urls import path
from . import views_admin

app_name = 'admin_panel'

urlpatterns = [
    path('dashboard/', views_admin.admin_dashboard_view, name='dashboard'),
    path('agencies/', views_admin.agencies_list_view, name='agencies_list'),
    path('agencies/<uuid:agency_id>/', views_admin.agency_detail_view, name='agency_detail'),
    path('agencies/<uuid:agency_id>/action/', views_admin.agency_action_view, name='agency_action'),
]
