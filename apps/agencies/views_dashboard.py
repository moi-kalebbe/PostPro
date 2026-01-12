"""
Agency Dashboard views.
These are the views for agency owners/members.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
import json

from apps.accounts.decorators import agency_required
from apps.projects.models import Project
from apps.automation.models import Post, BatchJob
from .forms import AgencyBrandingForm
from apps.projects.models import Project
from apps.automation.models import Post, BatchJob


@login_required
@agency_required
def dashboard_view(request):
    """Agency dashboard with KPIs and charts."""
    agency = request.user.agency
    
    # Date range for charts (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # KPIs
    total_projects = Project.objects.filter(agency=agency).count()
    total_posts = Post.objects.filter(project__agency=agency).count()
    published_posts = Post.objects.filter(
        project__agency=agency,
        status=Post.Status.PUBLISHED
    ).count()
    pending_posts = Post.objects.filter(
        project__agency=agency,
        status=Post.Status.PENDING_REVIEW
    ).count()
    
    # Cost totals
    cost_data = Post.objects.filter(
        project__agency=agency
    ).aggregate(
        total_text_cost=Sum('text_generation_cost'),
        total_image_cost=Sum('image_generation_cost'),
        total_cost=Sum('total_cost')
    )
    
    # Posts per day (for chart)
    posts_by_day = Post.objects.filter(
        project__agency=agency,
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Costs per day
    costs_by_day = Post.objects.filter(
        project__agency=agency,
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        cost=Sum('total_cost')
    ).order_by('date')
    
    # Recent posts
    recent_posts = Post.objects.filter(
        project__agency=agency
    ).select_related('project').order_by('-created_at')[:10]
    
    # Recent batches
    recent_batches = BatchJob.objects.filter(
        project__agency=agency
    ).select_related('project').order_by('-created_at')[:5]

    # Costs by Step (using Artifacts)
    from apps.automation.models import PostArtifact
    step_costs = PostArtifact.objects.filter(
        post__project__agency=agency,
        is_active=True
    ).values('step').annotate(
        total_cost=Sum('cost'),
        total_tokens=Sum('tokens_used'), 
        count=Count('id')
    ).order_by('step')
    
    context = {
        'agency': agency,
        'total_projects': total_projects,
        'total_posts': total_posts,
        'published_posts': published_posts,
        'pending_posts': pending_posts,
        'total_text_cost': cost_data['total_text_cost'] or 0,
        'total_image_cost': cost_data['total_image_cost'] or 0,
        'total_cost': cost_data['total_cost'] or 0,
        'posts_chart_data': json.dumps([
            {'date': item['date'].isoformat(), 'count': item['count']}
            for item in posts_by_day
        ]),
        'costs_chart_data': json.dumps([
            {'date': item['date'].isoformat(), 'cost': float(item['cost'] or 0)}
            for item in costs_by_day
        ]),
        'recent_posts': recent_posts,
        'recent_batches': recent_batches,
        'step_costs': step_costs,
    }
    
    return render(request, 'dashboard/index.html', context)


@login_required
@agency_required
def settings_view(request):
    """Agency settings page."""
    agency = request.user.agency
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_api_key':
            api_key = request.POST.get('openrouter_api_key', '').strip()
            if api_key:
                agency.set_openrouter_key(api_key)
                agency.save()
                messages.success(request, 'OpenRouter API key atualizada com sucesso!')
            else:
                messages.error(request, 'Por favor, insira uma API key válida.')
        
        elif action == 'test_api_key':
            is_valid, message = agency.validate_openrouter_key()
            if is_valid:
                messages.success(request, f'✓ {message}')
            else:
                messages.error(request, f'✗ {message}')
        
        elif action == 'update_models':
            agency.default_text_model = request.POST.get('default_text_model', agency.default_text_model)
            agency.default_image_model = request.POST.get('default_image_model', agency.default_image_model)
            agency.save()
            messages.success(request, 'Modelos padrão atualizados!')
        
        return redirect('dashboard:settings')
    
    # Check if API key exists
    has_api_key = bool(agency.get_openrouter_key())
    
    context = {
        'agency': agency,
        'has_api_key': has_api_key,
        'team_members': agency.members.all(),
        'is_configured': bool(agency.wuzapi_token),
        'is_connected': agency.wuzapi_connected,
    }
    
    return render(request, 'dashboard/settings.html', context)


@login_required
@agency_required
def branding_settings(request):
    """Agency branding settings view."""
    agency = request.user.agency
    
    if request.method == 'POST':
        form = AgencyBrandingForm(request.POST, request.FILES, instance=agency)
        if form.is_valid():
            form.save()
            messages.success(request, 'Branding atualizado com sucesso!')
            return redirect('dashboard:branding_settings')
        else:
            messages.error(request, 'Erro ao atualizar branding. Verifique o formulário.')
    else:
        form = AgencyBrandingForm(instance=agency)
    
    return render(request, 'agencies/branding_settings.html', {
        'form': form,
        'agency': agency
    })


@login_required
@agency_required
def usage_view(request):
    """Usage and cost reports."""
    agency = request.user.agency
    
    # Date range
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Aggregate costs by project
    costs_by_project = Project.objects.filter(
        agency=agency
    ).annotate(
        posts_count=Count('posts'),
        tokens=Sum('posts__tokens_total'),
        text_cost=Sum('posts__text_generation_cost'),
        image_cost=Sum('posts__image_generation_cost'),
        total_cost=Sum('posts__total_cost')
    ).order_by('-total_cost')
    
    # Daily breakdown
    daily_breakdown = Post.objects.filter(
        project__agency=agency,
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        posts=Count('id'),
        text_cost=Sum('text_generation_cost'),
        image_cost=Sum('image_generation_cost'),
        total=Sum('total_cost')
    ).order_by('date')
    
    # Totals for period
    period_totals = Post.objects.filter(
        project__agency=agency,
        created_at__gte=start_date
    ).aggregate(
        total_posts=Count('id'),
        total_tokens=Sum('tokens_total'),
        total_text_cost=Sum('text_generation_cost'),
        total_image_cost=Sum('image_generation_cost'),
        total_cost=Sum('total_cost')
    )

    # Prepare Type Chart Data
    type_chart_data = {
        'text': float(period_totals['total_text_cost'] or 0),
        'image': float(period_totals['total_image_cost'] or 0)
    }
    
    context = {
        'agency': agency,
        'days': days,
        'costs_by_project': costs_by_project,
        'daily_breakdown': daily_breakdown,
        'total_posts': period_totals['total_posts'] or 0,
        'total_cost': period_totals['total_cost'] or 0,
        'avg_cost': (period_totals['total_cost'] or 0) / (period_totals['total_posts'] or 1),
        'total_tokens': period_totals['total_tokens'] or 0,
        'daily_chart_data': json.dumps([
            {
                'date': item['date'].isoformat(),
                'text_cost': float(item['text_cost'] or 0),
                'image_cost': float(item['image_cost'] or 0),
                'total': float(item['total'] or 0),
                'cost': float(item['total'] or 0) # For simple line chart
            }
            for item in daily_breakdown
        ]),
        'type_chart_data': json.dumps(type_chart_data)
    }
    
    return render(request, 'dashboard/usage.html', context)
