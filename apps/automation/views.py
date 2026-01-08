"""
Automation views for PostPro.
Posts management and batch operations.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.db.models import Q
import json

from apps.accounts.decorators import agency_required, project_access_required
from apps.projects.models import Project
from .models import Post, BatchJob, PostArtifact
from .tasks import process_csv_batch, regenerate_post_step, publish_to_wordpress


@login_required
@agency_required
def posts_list_view(request):
    """List all posts for the agency."""
    agency = request.user.agency
    
    # Filters
    project_id = request.GET.get('project', '')
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    posts = Post.objects.filter(
        project__agency=agency
    ).select_related('project', 'batch_job')
    
    if project_id:
        posts = posts.filter(project_id=project_id)
    if status_filter:
        posts = posts.filter(status=status_filter)
    if search:
        posts = posts.filter(
            Q(keyword__icontains=search) | Q(title__icontains=search)
        )
    
    posts = posts.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(posts, 20)
    page = request.GET.get('page', 1)
    posts_page = paginator.get_page(page)
    
    # Projects for filter dropdown
    projects = Project.objects.filter(agency=agency)
    
    context = {
        'posts': posts_page,
        'projects': projects,
        'status_choices': Post.Status.choices,
        'project_filter': project_id,
        'status_filter': status_filter,
        'search': search,
    }
    
    return render(request, 'automation/posts_list.html', context)


@login_required
@agency_required
def post_detail_view(request, post_id):
    """Post detail modal content."""
    post = get_object_or_404(
        Post.objects.select_related('project'),
        id=post_id,
        project__agency=request.user.agency
    )
    
    # Get artifacts
    artifacts = post.artifacts.filter(is_active=True).order_by('step')
    
    context = {
        'post': post,
        'artifacts': artifacts,
    }
    
    return render(request, 'automation/post_detail.html', context)


@login_required
@agency_required
@require_POST
def post_regenerate_view(request, post_id):
    """Regenerate a post step."""
    post = get_object_or_404(
        Post,
        id=post_id,
        project__agency=request.user.agency
    )
    
    data = json.loads(request.body) if request.body else {}
    step = data.get('step', 'all')
    preserve_downstream = data.get('preserve_downstream', False)
    
    if step == 'all':
        # Regenerate entire post
        for s in ['research', 'strategy', 'article', 'image']:
            regenerate_post_step.delay(str(post.id), s)
    else:
        regenerate_post_step.delay(str(post.id), step, preserve_downstream)
    
    return JsonResponse({
        'success': True,
        'message': f'Regenerating {step}...'
    })


@login_required
@agency_required
@require_POST
def post_publish_view(request, post_id):
    """Publish a post to WordPress."""
    post = get_object_or_404(
        Post,
        id=post_id,
        project__agency=request.user.agency
    )
    
    if post.status == Post.Status.PUBLISHED:
        return JsonResponse({
            'success': False,
            'message': 'Post already published'
        })
    
    publish_to_wordpress.delay(str(post.id))
    
    return JsonResponse({
        'success': True,
        'message': 'Publishing to WordPress...'
    })


@login_required
@agency_required
@require_POST
def post_approve_view(request, post_id):
    """Approve a post for publishing."""
    post = get_object_or_404(
        Post,
        id=post_id,
        project__agency=request.user.agency
    )
    
    post.status = Post.Status.APPROVED
    post.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Post approved'
    })


@login_required
@project_access_required
@require_POST
def batch_upload_submit_view(request, project_id):
    """Handle batch upload form submission."""
    project = request.project
    
    # Get file
    csv_file = request.FILES.get('csv_file')
    if not csv_file:
        return JsonResponse({
            'success': False,
            'message': 'No file uploaded'
        }, status=400)
    
    # Validate file type
    filename = csv_file.name.lower()
    if not (filename.endswith('.csv') or filename.endswith('.xlsx')):
        return JsonResponse({
            'success': False,
            'message': 'Invalid file type. Use CSV or XLSX.'
        }, status=400)
    
    # Get options
    generate_images = request.POST.get('generate_images') == 'true'
    auto_publish = request.POST.get('auto_publish') == 'true'
    dry_run = request.POST.get('dry_run') == 'true'
    
    # Create batch job
    batch_job = BatchJob.objects.create(
        project=project,
        csv_file=csv_file,
        original_filename=csv_file.name,
        is_dry_run=dry_run,
        options={
            'generate_images': generate_images,
            'auto_publish': auto_publish,
        }
    )
    
    # Start processing
    process_csv_batch.delay(str(batch_job.id))
    
    return JsonResponse({
        'success': True,
        'batch_id': str(batch_job.id),
        'message': 'Batch started' if not dry_run else 'Simulation started'
    })


@login_required
@agency_required
@require_GET
def batch_status_view(request, batch_id):
    """Get batch job status."""
    batch_job = get_object_or_404(
        BatchJob.objects.select_related('project'),
        id=batch_id,
        project__agency=request.user.agency
    )
    
    response_data = {
        'id': str(batch_job.id),
        'status': batch_job.status,
        'total_rows': batch_job.total_rows,
        'processed_rows': batch_job.processed_rows,
        'progress_percent': batch_job.progress_percent,
        'is_dry_run': batch_job.is_dry_run,
        'estimated_cost': str(batch_job.estimated_cost),
    }
    
    if batch_job.status == BatchJob.Status.COMPLETED:
        response_data['error_log'] = batch_job.error_log
    
    if batch_job.status == BatchJob.Status.FAILED:
        response_data['error'] = batch_job.error_log.get('fatal_error', 'Unknown error')
    
    return JsonResponse(response_data)


@login_required
@agency_required
def batches_list_view(request):
    """List all batch jobs for the agency."""
    agency = request.user.agency
    
    batches = BatchJob.objects.filter(
        project__agency=agency
    ).select_related('project').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(batches, 20)
    page = request.GET.get('page', 1)
    batches_page = paginator.get_page(page)
    
    context = {
        'batches': batches_page,
    }
    
    return render(request, 'automation/batches_list.html', context)
