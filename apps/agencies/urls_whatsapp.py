"""
WhatsApp configuration URLs for agencies.
"""

from django.urls import path
from . import views_whatsapp

app_name = 'whatsapp'

urlpatterns = [
    path('', views_whatsapp.whatsapp_config_view, name='config'),
    path('setup/', views_whatsapp.whatsapp_setup_view, name='setup'),
    path('connect/', views_whatsapp.whatsapp_connect_view, name='connect'),
    path('qr/', views_whatsapp.whatsapp_qr_view, name='qr'),
    path('status/', views_whatsapp.whatsapp_status_view, name='status'),
    path('disconnect/', views_whatsapp.whatsapp_disconnect_view, name='disconnect'),
]
