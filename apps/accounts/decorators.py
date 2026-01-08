"""
Permission decorators for PostPro.
Multi-tenant access control.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden


def super_admin_required(view_func):
    """Require super admin role."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_super_admin:
            messages.error(request, 'Acesso restrito a administradores.')
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper


def agency_required(view_func):
    """Require user to belong to an agency."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        # Super admins can access if agency_id in URL
        if request.user.is_super_admin:
            return view_func(request, *args, **kwargs)
        
        if not request.user.agency:
            # Log out the user to prevent redirect loop
            from django.contrib.auth import logout
            logout(request)
            messages.error(request, 'Você precisa pertencer a uma agência para acessar. Entre em contato com o administrador.')
            return redirect('accounts:login')
        
        if not request.user.agency.is_subscription_active:
            messages.warning(request, 'Sua assinatura está suspensa.')
            return redirect('dashboard:settings')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def agency_owner_required(view_func):
    """Require agency owner role."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if request.user.is_super_admin:
            return view_func(request, *args, **kwargs)
        
        if not request.user.is_agency_owner:
            messages.error(request, 'Acesso restrito ao proprietário da agência.')
            return redirect('dashboard:index')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def project_access_required(view_func):
    """Require access to a specific project."""
    @wraps(view_func)
    def wrapper(request, project_id, *args, **kwargs):
        from apps.projects.models import Project
        
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            messages.error(request, 'Projeto não encontrado.')
            return redirect('projects:list')
        
        # Check tenant access
        if not request.user.is_super_admin:
            if not request.user.agency or request.user.agency.id != project.agency_id:
                messages.error(request, 'Você não tem acesso a este projeto.')
                return redirect('projects:list')
        
        # Attach project to request
        request.project = project
        return view_func(request, project_id, *args, **kwargs)
    return wrapper
