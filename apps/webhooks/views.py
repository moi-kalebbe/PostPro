"""
API views for WordPress plugin integration.
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.projects.models import Project
from apps.automation.models import Post, BatchJob
from apps.automation.tasks import process_csv_batch, publish_to_wordpress, regenerate_post_step
from .middleware import license_required

logger = logging.getLogger(__name__)


@require_GET
@csrf_exempt
@license_required
def validate_license_view(request):
    """
    Validate a license key.
    
    GET /api/v1/validate-license
    Headers: X-License-Key
    
    Returns:
        {
            "valid": true,
            "project": {
                "id": "uuid",
                "name": "...",
                "wordpress_url": "..."
            },
            "agency": {
                "name": "...",
                "plan": "..."
            }
        }
    """
    project = request.project
    agency = request.agency
    
    return JsonResponse({
        "valid": True,
        "project": {
            "id": str(project.id),
            "name": project.name,
            "wordpress_url": project.wordpress_url,
            "tone": project.tone,
            "image_style": project.image_style,
        },
        "agency": {
            "name": agency.name,
            "plan": agency.plan,
            "posts_remaining": agency.posts_remaining,
        }
    })


@require_POST
@csrf_exempt
@license_required
def batch_upload_view(request):
    """
    Upload a batch of keywords for processing.
    
    POST /api/v1/batch-upload
    Headers: X-License-Key, Content-Type: multipart/form-data
    Body: csv_file, generate_images=true, auto_publish=false, dry_run=false
    
    Returns:
        {
            "success": true,
            "batch_id": "uuid",
            "message": "..."
        }
    """
    project = request.project
    
    # Get file
    csv_file = request.FILES.get('csv_file')
    if not csv_file:
        return JsonResponse({
            "success": False,
            "error": "No file provided"
        }, status=400)
    
    # Validate file
    filename = csv_file.name.lower()
    if not (filename.endswith('.csv') or filename.endswith('.xlsx')):
        return JsonResponse({
            "success": False,
            "error": "Invalid file type. Use CSV or XLSX."
        }, status=400)
    
    # Options
    generate_images = request.POST.get('generate_images', 'true').lower() == 'true'
    auto_publish = request.POST.get('auto_publish', 'false').lower() == 'true'
    dry_run = request.POST.get('dry_run', 'false').lower() == 'true'
    
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
        "success": True,
        "batch_id": str(batch_job.id),
        "message": "Batch processing started" if not dry_run else "Simulation started"
    })


@require_GET
@csrf_exempt
@license_required
def batch_status_view(request, batch_id):
    """
    Get status of a batch job.
    
    GET /api/v1/batch/<uuid>/status
    Headers: X-License-Key
    
    Returns:
        {
            "id": "uuid",
            "status": "processing",
            "progress": 50,
            "total_rows": 10,
            "processed_rows": 5,
            "estimated_cost": "0.1234"
        }
    """
    project = request.project
    
    try:
        batch_job = BatchJob.objects.get(id=batch_id, project=project)
    except BatchJob.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Batch not found"
        }, status=404)
    
    response_data = {
        "id": str(batch_job.id),
        "status": batch_job.status,
        "progress": batch_job.progress_percent,
        "total_rows": batch_job.total_rows,
        "processed_rows": batch_job.processed_rows,
        "is_dry_run": batch_job.is_dry_run,
        "estimated_cost": str(batch_job.estimated_cost),
    }
    
    if batch_job.status == BatchJob.Status.COMPLETED and batch_job.is_dry_run:
        response_data["simulation_report"] = batch_job.error_log.get("simulation_report", {})
    
    if batch_job.status == BatchJob.Status.FAILED:
        response_data["error"] = batch_job.error_log.get("fatal_error", "Unknown error")
    
    return JsonResponse(response_data)


@require_POST
@csrf_exempt
@license_required
def post_publish_view(request, post_id):
    """
    Publish a post to WordPress.
    
    POST /api/v1/posts/<uuid>/publish
    Headers: X-License-Key
    
    Returns:
        {
            "success": true,
            "message": "Publishing started"
        }
    """
    project = request.project
    
    try:
        post = Post.objects.get(id=post_id, project=project)
    except Post.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Post not found"
        }, status=404)
    
    if post.status == Post.Status.PUBLISHED:
        return JsonResponse({
            "success": True,
            "message": "Already published",
            "wordpress_post_id": post.wordpress_post_id,
            "edit_url": post.wordpress_edit_url,
        })
    
    # Start publish task
    publish_to_wordpress.delay(str(post.id))
    
    return JsonResponse({
        "success": True,
        "message": "Publishing to WordPress..."
    })


@require_POST
@csrf_exempt
@license_required
def post_regenerate_view(request, post_id):
    """
    Regenerate a post step.
    
    POST /api/v1/posts/<uuid>/regenerate
    Headers: X-License-Key
    Body: {"step": "research|strategy|article|image|all", "preserve_downstream": false}
    
    Returns:
        {
            "success": true,
            "message": "Regenerating..."
        }
    """
    project = request.project
    
    try:
        post = Post.objects.get(id=post_id, project=project)
    except Post.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Post not found"
        }, status=404)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}
    
    step = data.get('step', 'all')
    preserve_downstream = data.get('preserve_downstream', False)
    
    if step not in ['research', 'strategy', 'article', 'image', 'all']:
        return JsonResponse({
            "success": False,
            "error": f"Invalid step: {step}"
        }, status=400)
    
    if step == 'all':
        for s in ['research', 'strategy', 'article', 'image']:
            regenerate_post_step.delay(str(post.id), s)
    else:
        regenerate_post_step.delay(str(post.id), step, preserve_downstream)
    
    return JsonResponse({
        "success": True,
        "message": f"Regenerating {step}..."
    })


@require_GET
@csrf_exempt
@license_required
def post_detail_view(request, post_id):
    """
    Get post details.
    
    GET /api/v1/posts/<uuid>
    Headers: X-License-Key
    
    Returns:
        Post data including content, status, costs
    """
    project = request.project
    
    try:
        post = Post.objects.get(id=post_id, project=project)
    except Post.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Post not found"
        }, status=404)
    
    return JsonResponse({
        "id": str(post.id),
        "keyword": post.keyword,
        "title": post.title,
        "content": post.content,
        "meta_description": post.meta_description,
        "featured_image_url": post.featured_image_url,
        "status": post.status,
        "step_state": post.step_state,
        "wordpress_post_id": post.wordpress_post_id,
        "wordpress_edit_url": post.wordpress_edit_url,
        "text_generation_cost": str(post.text_generation_cost),
        "image_generation_cost": str(post.image_generation_cost),
        "total_cost": str(post.total_cost),
        "tokens_total": post.tokens_total,
        "created_at": post.created_at.isoformat(),
        "published_at": post.published_at.isoformat() if post.published_at else None,
    })
