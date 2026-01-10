"""
Automation URLs.
"""

from django.urls import path
from . import views

app_name = 'automation'

urlpatterns = [
    # Posts
    path('posts/', views.posts_list_view, name='posts_list'),
    path('posts/<uuid:post_id>/', views.post_detail_view, name='post_detail'),
    path('posts/<uuid:post_id>/regenerate/', views.post_regenerate_view, name='post_regenerate'),
    path('posts/<uuid:post_id>/publish/', views.post_publish_view, name='post_publish'),
    path('posts/<uuid:post_id>/approve/', views.post_approve_view, name='post_approve'),
    path('posts/<uuid:post_id>/delete/', views.post_delete_view, name='post_delete'),
    path('posts/bulk-delete/', views.posts_bulk_delete_view, name='posts_bulk_delete'),
    
    # Batches
    path('batches/', views.batches_list_view, name='batches_list'),
    path('batches/<uuid:batch_id>/status/', views.batch_status_view, name='batch_status'),
    path('batches/<uuid:batch_id>/delete/', views.batch_delete_view, name='batch_delete'),
    path('batches/bulk-delete/', views.batches_bulk_delete_view, name='batches_bulk_delete'),
    
    # REMOVED: CSV Upload feature - keywords now sent via WordPress plugin
    # path('projects/<uuid:project_id>/batch-upload/', views.batch_upload_submit_view, name='batch_upload_submit'),
]
