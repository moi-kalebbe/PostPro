"""
URL configuration for PostPro.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path('django-admin/', admin.site.urls),
    
    # Authentication
    path('auth/', include('apps.accounts.urls')),
    
    # Dashboard (Agency Panel)
    path('dashboard/', include('apps.agencies.urls_dashboard')),
    
    # Admin Panel (Super Admin)
    path('admin/', include('apps.agencies.urls_admin')),
    
    # Projects
    path('projects/', include('apps.projects.urls')),
    
    # Automation (Posts, Batches)
    path('automation/', include('apps.automation.urls')),
    
    # API (Webhooks for WordPress)
    path('api/v1/', include('apps.webhooks.urls')),
    
    # Home redirect
    path('', include('apps.accounts.urls_home')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
