"""
Project URLs.
"""

from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list_view, name='list'),
    path('new/', views.project_create_view, name='create'),
    path('<uuid:project_id>/', views.project_detail_view, name='detail'),
    path('<uuid:project_id>/edit/', views.project_edit_view, name='edit'),
    path('<uuid:project_id>/delete/', views.project_delete_view, name='delete'),
    path('<uuid:project_id>/regenerate-key/', views.project_regenerate_key_view, name='regenerate_key'),
    # REMOVED: CSV Upload feature - keywords now sent via WordPress plugin
    # path('<uuid:project_id>/batch-upload/', views.project_batch_upload_view, name='batch_upload'),
    # Editorial Plan Item deletion
    path('<uuid:project_id>/editorial-item/<uuid:item_id>/delete/', views.editorial_item_delete_view, name='editorial_item_delete'),
    path('<uuid:project_id>/editorial-items/bulk-delete/', views.editorial_items_bulk_delete_view, name='editorial_items_bulk_delete'),
    # RSS Feed Settings & Management
    path('<uuid:project_id>/rss-settings/', views.rss_settings_view, name='rss_settings'),
    path('<uuid:project_id>/rss/feed/add/', views.rss_feed_create_view, name='rss_feed_create'),
    path('<uuid:project_id>/rss/feed/<int:feed_id>/delete/', views.rss_feed_delete_view, name='rss_feed_delete'),
    
    # WhatsApp Access
    path('<uuid:project_id>/send-access/', views.project_send_access_view, name='send_access'),
    
    # Public Magic Link (no login required)
    path('setup/<uuid:token>/', views.project_setup_view, name='setup'),
    path('setup/<uuid:token>/download/', views.project_plugin_download_view, name='plugin_download'),
]
