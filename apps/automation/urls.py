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
    
    # Batches
    path('batches/', views.batches_list_view, name='batches_list'),
    path('batches/<uuid:batch_id>/status/', views.batch_status_view, name='batch_status'),
    
    # Batch upload (project-scoped)
    path('projects/<uuid:project_id>/batch-upload/', views.batch_upload_submit_view, name='batch_upload_submit'),
]
