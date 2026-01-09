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
@agency_required
@require_POST
def post_delete_view(request, post_id):
    """
    Delete a single post.
    
    Body: {"delete_from_wordpress": true/false}
    """
    from services.wordpress import WordPressService
    from .models import ActivityLog
    
    post = get_object_or_404(
        Post.objects.select_related('project', 'project__agency'),
        id=post_id,
        project__agency=request.user.agency
    )
    
    data = json.loads(request.body) if request.body else {}
    delete_from_wp = data.get('delete_from_wordpress', False)
    
    project = post.project
    wp_result = None
    
    # Delete from WordPress if requested and post was published
    if delete_from_wp and post.wordpress_post_id:
        try:
            wp_password = project.get_wordpress_password()
            if wp_password and project.wordpress_username:
                wp_service = WordPressService(
                    site_url=project.wordpress_url,
                    username=project.wordpress_username,
                    app_password=wp_password
                )
                wp_result = wp_service.delete_post(post.wordpress_post_id)
        except Exception as e:
            wp_result = {'success': False, 'message': str(e)}
    
    # Store info for response before deleting
    post_keyword = post.keyword
    post_title = post.title
    
    # Log activity
    ActivityLog.objects.create(
        agency=project.agency,
        project=project,
        actor_user=request.user,
        action="POST_DELETED",
        entity_type="Post",
        entity_id=str(post.id),
        metadata={
            "keyword": post_keyword,
            "title": post_title,
            "deleted_from_wp": delete_from_wp,
            "wp_result": wp_result,
        }
    )
    
    # Delete from local database
    post.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Post deletado com sucesso',
        'deleted_from_wordpress': wp_result.get('success', False) if wp_result else False,
        'wp_message': wp_result.get('message', '') if wp_result else '',
    })


@login_required
@agency_required
@require_POST
def posts_bulk_delete_view(request):
    """
    Delete multiple posts at once.
    
    Body: {"post_ids": ["uuid1", "uuid2", ...], "delete_from_wordpress": true/false}
    """
    from services.wordpress import WordPressService
    from .models import ActivityLog
    
    data = json.loads(request.body) if request.body else {}
    post_ids = data.get('post_ids', [])
    delete_from_wp = data.get('delete_from_wordpress', False)
    
    if not post_ids:
        return JsonResponse({
            'success': False,
            'message': 'Nenhum post selecionado'
        }, status=400)
    
    agency = request.user.agency
    
    # Get all posts
    posts = Post.objects.filter(
        id__in=post_ids,
        project__agency=agency
    ).select_related('project', 'project__agency')
    
    deleted_count = 0
    wp_deleted_count = 0
    errors = []
    
    # Group posts by project for efficient WordPress deletion
    posts_by_project = {}
    for post in posts:
        if post.project.id not in posts_by_project:
            posts_by_project[post.project.id] = {
                'project': post.project,
                'posts': []
            }
        posts_by_project[post.project.id]['posts'].append(post)
    
    # Process deletions
    for project_id, data in posts_by_project.items():
        project = data['project']
        project_posts = data['posts']
        
        # Initialize WordPress service if needed
        wp_service = None
        if delete_from_wp:
            try:
                wp_password = project.get_wordpress_password()
                if wp_password and project.wordpress_username:
                    wp_service = WordPressService(
                        site_url=project.wordpress_url,
                        username=project.wordpress_username,
                        app_password=wp_password
                    )
            except Exception:
                pass
        
        for post in project_posts:
            try:
                # Delete from WordPress if applicable
                if wp_service and post.wordpress_post_id:
                    result = wp_service.delete_post(post.wordpress_post_id)
                    if result.get('success'):
                        wp_deleted_count += 1
                
                # Log activity
                ActivityLog.objects.create(
                    agency=agency,
                    project=project,
                    actor_user=request.user,
                    action="POST_DELETED",
                    entity_type="Post",
                    entity_id=str(post.id),
                    metadata={
                        "keyword": post.keyword,
                        "bulk_delete": True,
                    }
                )
                
                # Delete from local database
                post.delete()
                deleted_count += 1
                
            except Exception as e:
                errors.append({
                    'post_id': str(post.id),
                    'keyword': post.keyword,
                    'error': str(e)
                })
    
    return JsonResponse({
        'success': True,
        'message': f'{deleted_count} post(s) deletado(s)',
        'deleted_count': deleted_count,
        'wp_deleted_count': wp_deleted_count,
        'errors': errors if errors else None,
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
