"""
Project views for PostPro.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count

from apps.accounts.decorators import agency_required, project_access_required
from apps.automation.models import Post, BatchJob
from .models import Project
from .forms import ProjectForm


@login_required
@agency_required
def project_list_view(request):
    """List all projects for the agency."""
    agency = request.user.agency
    
    projects = Project.objects.filter(
        agency=agency
    ).annotate(
        posts_count=Count('posts'),
        pending_count=Count('posts', filter=models.Q(posts__status=Post.Status.PENDING_REVIEW)),
        total_cost=Sum('posts__total_cost')
    ).order_by('-created_at')
    
    context = {
        'projects': projects,
        'can_create': agency.can_create_project,
    }
    
    return render(request, 'projects/list.html', context)


@login_required
@agency_required
def project_create_view(request):
    """Create a new project."""
    agency = request.user.agency
    
    if not agency.can_create_project:
        messages.error(request, f'Limite de projetos atingido ({agency.max_projects}). Faça upgrade do plano.')
        return redirect('projects:list')
    
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.agency = agency
            
            # Handle password encryption
            password = form.cleaned_data.get('wordpress_password')
            if password:
                project.set_wordpress_password(password)
            
            project.save()
            messages.success(request, f'Projeto "{project.name}" criado com sucesso!')
            return redirect('projects:detail', project_id=project.id)
    else:
        form = ProjectForm()
    
    context = {
        'form': form,
        'is_edit': False,
    }
    
    return render(request, 'projects/form.html', context)


@login_required
@project_access_required
def project_detail_view(request, project_id):
    """Project detail page."""
    project = request.project
    
    # Recent posts
    recent_posts = Post.objects.filter(
        project=project
    ).order_by('-created_at')[:10]
    
    # Stats
    stats = Post.objects.filter(project=project).aggregate(
        total_posts=Count('id'),
        published=Count('id', filter=models.Q(status=Post.Status.PUBLISHED)),
        pending=Count('id', filter=models.Q(status=Post.Status.PENDING_REVIEW)),
        failed=Count('id', filter=models.Q(status=Post.Status.FAILED)),
        total_cost=Sum('total_cost'),
        total_tokens=Sum('tokens_total')
    )
    
    # Editorial Plan (latest active or pending)
    from apps.automation.models import EditorialPlan
    editorial_plan = EditorialPlan.objects.filter(
        project=project,
        status__in=[EditorialPlan.Status.GENERATING, EditorialPlan.Status.ACTIVE, EditorialPlan.Status.PENDING_APPROVAL, EditorialPlan.Status.APPROVED]
    ).order_by('-created_at').first()
    
    editorial_items = []
    if editorial_plan:
        editorial_items = editorial_plan.items.all().order_by('day_index')[:30]
    
    context = {
        'project': project,
        'recent_posts': recent_posts,
        'stats': stats,
        'editorial_plan': editorial_plan,
        'editorial_items': editorial_items,
    }
    
    return render(request, 'projects/detail.html', context)


@login_required
@project_access_required
def project_edit_view(request, project_id):
    """Edit project settings."""
    project = request.project
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save(commit=False)
            
            # Handle password update
            password = form.cleaned_data.get('wordpress_password')
            if password:
                project.set_wordpress_password(password)
            
            project.save()
            messages.success(request, 'Projeto atualizado com sucesso!')
            return redirect('projects:detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project)
    
    context = {
        'form': form,
        'project': project,
        'is_edit': True,
    }
    
    return render(request, 'projects/form.html', context)


@login_required
@project_access_required
def project_regenerate_key_view(request, project_id):
    """Regenerate project license key."""
    project = request.project
    
    if request.method == 'POST':
        project.regenerate_license_key()
        messages.success(request, 'License key regenerada. Atualize o plugin WordPress.')
    
    return redirect('projects:detail', project_id=project.id)


@login_required
@project_access_required
def project_batch_upload_view(request, project_id):
    """Batch upload wizard."""
    project = request.project
    
    context = {
        'project': project,
    }
    
    return render(request, 'projects/batch_upload.html', context)


# Import models for Q filter
from django.db import models
