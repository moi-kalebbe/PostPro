"""
API URLs for WordPress plugin.
"""

from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # License validation
    path('validate-license', views.validate_license_view, name='validate_license'),
    
    # Project operations
    path('project/sync-profile', views.sync_site_profile_view, name='sync_profile'),
    path('project/editorial-plan', views.editorial_plan_view, name='editorial_plan'),
    path('project/keywords', views.save_keywords_view, name='save_keywords'),
    
    # Batch operations
    path('batch-upload', views.batch_upload_view, name='batch_upload'),
    path('batch/<uuid:batch_id>/status', views.batch_status_view, name='batch_status'),
    
    # Post operations
    path('posts/<uuid:post_id>', views.post_detail_view, name='post_detail'),
    path('posts/<uuid:post_id>/publish', views.post_publish_view, name='post_publish'),
    path('posts/<uuid:post_id>/regenerate', views.post_regenerate_view, name='post_regenerate'),
    
    # Debug (temporary)
    path('debug/batch-jobs', views.debug_batch_jobs, name='debug_batch_jobs'),
]
