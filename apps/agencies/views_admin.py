"""
Super Admin Panel views.
Platform-wide management for super admins.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
import json

from apps.accounts.decorators import super_admin_required
from apps.accounts.models import User
from apps.automation.models import Post, BatchJob, ActivityLog
from .models import Agency


@login_required
@super_admin_required
def admin_dashboard_view(request):
    """Super admin dashboard with platform KPIs."""
    
    # Date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Platform KPIs
    total_agencies = Agency.objects.count()
    active_agencies = Agency.objects.filter(subscription_status=Agency.SubscriptionStatus.ACTIVE).count()
    total_users = User.objects.count()
    total_posts = Post.objects.count()
    
    # Revenue placeholder (would integrate with Stripe)
    monthly_revenue = 0  # TODO: Implement Stripe integration
    
    # Platform costs
    cost_totals = Post.objects.aggregate(
        total_text_cost=Sum('text_generation_cost'),
        total_image_cost=Sum('image_generation_cost'),
        total_cost=Sum('total_cost')
    )
    
    # Agencies growth
    agencies_by_day = Agency.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Posts by day
    posts_by_day = Post.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Recent activity
    recent_activity = ActivityLog.objects.select_related(
        'actor_user', 'agency'
    ).order_by('-created_at')[:20]
    
    # Top agencies by posts
    top_agencies = Agency.objects.annotate(
        post_count=Count('projects__posts'),
        total_cost=Sum('projects__posts__total_cost')
    ).order_by('-post_count')[:10]
    
    context = {
        'total_agencies': total_agencies,
        'active_agencies': active_agencies,
        'total_users': total_users,
        'total_posts': total_posts,
        'monthly_revenue': monthly_revenue,
        'total_cost': cost_totals['total_cost'] or 0,
        'agencies_chart_data': json.dumps([
            {'date': item['date'].isoformat(), 'count': item['count']}
            for item in agencies_by_day
        ]),
        'posts_chart_data': json.dumps([
            {'date': item['date'].isoformat(), 'count': item['count']}
            for item in posts_by_day
        ]),
        'recent_activity': recent_activity,
        'top_agencies': top_agencies,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
@super_admin_required
def agencies_list_view(request):
    """List all agencies with filters."""
    
    # Filters
    plan_filter = request.GET.get('plan', '')
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    agencies = Agency.objects.annotate(
        posts_count=Count('projects__posts'),
        total_cost=Sum('projects__posts__total_cost')
    )
    
    if plan_filter:
        agencies = agencies.filter(plan=plan_filter)
    if status_filter:
        agencies = agencies.filter(subscription_status=status_filter)
    if search:
        agencies = agencies.filter(name__icontains=search)
    
    agencies = agencies.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(agencies, 20)
    page = request.GET.get('page', 1)
    agencies_page = paginator.get_page(page)
    
    context = {
        'agencies': agencies_page,
        'plan_choices': Agency.Plan.choices,
        'status_choices': Agency.SubscriptionStatus.choices,
        'plan_filter': plan_filter,
        'status_filter': status_filter,
        'search': search,
    }
    
    return render(request, 'admin_panel/agencies_list.html', context)


@login_required
@super_admin_required
def agency_detail_view(request, agency_id):
    """Agency detail page with tabs."""
    agency = get_object_or_404(Agency, id=agency_id)
    
    tab = request.GET.get('tab', 'overview')
    
    # Overview data
    projects = agency.projects.annotate(
        posts_count=Count('posts'),
        total_cost=Sum('posts__total_cost')
    )
    
    # Members
    members = agency.members.all()
    
    # Recent posts
    recent_posts = Post.objects.filter(
        project__agency=agency
    ).select_related('project').order_by('-created_at')[:20]
    
    # Activity logs
    activity_logs = ActivityLog.objects.filter(
        agency=agency
    ).select_related('actor_user').order_by('-created_at')[:50]
    
    context = {
        'agency': agency,
        'tab': tab,
        'projects': projects,
        'members': members,
        'recent_posts': recent_posts,
        'activity_logs': activity_logs,
    }
    
    return render(request, 'admin_panel/agency_detail.html', context)


@login_required
@super_admin_required
def agency_action_view(request, agency_id):
    """Handle agency actions (suspend, activate, etc)."""
    agency = get_object_or_404(Agency, id=agency_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'suspend':
            agency.subscription_status = Agency.SubscriptionStatus.SUSPENDED
            agency.save()
            messages.warning(request, f'Agency {agency.name} has been suspended.')
        
        elif action == 'activate':
            agency.subscription_status = Agency.SubscriptionStatus.ACTIVE
            agency.save()
            messages.success(request, f'Agency {agency.name} has been activated.')
        
        elif action == 'reset_posts':
            agency.reset_monthly_posts()
            messages.success(request, f'Monthly post counter reset for {agency.name}.')
        
        # Log action
        ActivityLog.objects.create(
            actor_user=request.user,
            agency=agency,
            action=f'AGENCY_{action.upper()}',
            entity_type='Agency',
            entity_id=str(agency.id),
            metadata={'action': action}
        )
    
    return redirect('admin_panel:agency_detail', agency_id=agency_id)
