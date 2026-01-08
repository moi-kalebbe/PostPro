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
    path('<uuid:project_id>/regenerate-key/', views.project_regenerate_key_view, name='regenerate_key'),
    path('<uuid:project_id>/batch-upload/', views.project_batch_upload_view, name='batch_upload'),
]
