"""
Admin panel URLs for super admins.
"""

from django.urls import path
from . import views_admin

app_name = 'admin_panel'

urlpatterns = [
    path('dashboard/', views_admin.admin_dashboard_view, name='dashboard'),
    path('agencies/', views_admin.agencies_list_view, name='agencies_list'),
    path('agencies/create/', views_admin.agency_create_view, name='agency_create'),
    path('agencies/<uuid:agency_id>/', views_admin.agency_detail_view, name='agency_detail'),
    path('agencies/<uuid:agency_id>/edit/', views_admin.agency_edit_view, name='agency_edit'),
    path('agencies/<uuid:agency_id>/action/', views_admin.agency_action_view, name='agency_action'),
    # SuperAdmin WhatsApp Configuration
    path('whatsapp/', views_admin.superadmin_whatsapp_view, name='superadmin_whatsapp'),
    path('whatsapp/connect/', views_admin.superadmin_whatsapp_connect_view, name='superadmin_whatsapp_connect'),
    path('whatsapp/status/', views_admin.superadmin_whatsapp_status_view, name='superadmin_whatsapp_status'),
]
