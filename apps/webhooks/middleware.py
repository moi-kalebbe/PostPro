"""
License validation middleware for API endpoints.
"""

from functools import wraps
from django.http import JsonResponse

from apps.projects.models import Project


def license_required(view_func):
    """
    Decorator to validate X-License-Key header.
    Attaches project and agency to request.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Get license key from header
        license_key = request.headers.get('X-License-Key', '')
        
        if not license_key:
            return JsonResponse({
                "success": False,
                "error": "Missing X-License-Key header"
            }, status=401)
        
        # Find project
        try:
            project = Project.objects.select_related('agency').get(
                license_key=license_key,
                is_active=True
            )
        except Project.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Invalid license key"
            }, status=401)
        
        # Check agency status
        agency = project.agency
        if not agency.is_subscription_active:
            return JsonResponse({
                "success": False,
                "error": "Subscription inactive"
            }, status=403)
        
        # Attach to request
        request.project = project
        request.agency = agency
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


class LicenseValidationMiddleware:
    """
    Middleware to validate license for /api/ routes.
    
    Note: Using decorator-based approach is preferred.
    This middleware is for reference if you need global validation.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only apply to /api/v1/ routes
        if request.path.startswith('/api/v1/'):
            license_key = request.headers.get('X-License-Key', '')
            
            if license_key:
                try:
                    project = Project.objects.select_related('agency').get(
                        license_key=license_key,
                        is_active=True
                    )
                    request.project = project
                    request.agency = project.agency
                except Project.DoesNotExist:
                    pass
        
        return self.get_response(request)
