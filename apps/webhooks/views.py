"""
API views for WordPress plugin integration.
"""

import json
import logging
import os
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings

from apps.projects.models import Project
from apps.automation.models import Post, BatchJob, EditorialPlan
from apps.automation.tasks import process_csv_batch, publish_to_wordpress, regenerate_post_step, sync_site_profile
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


@require_GET
@csrf_exempt
def debug_batch_jobs(request):
    """
    Debug endpoint to check batch job status and file accessibility.
    
    GET /api/v1/debug/batch-jobs
    """
    # Get last 10 jobs
    jobs = BatchJob.objects.all().order_by('-created_at')[:10]
    
    media_root = str(settings.MEDIA_ROOT)
    batch_uploads_path = os.path.join(media_root, 'batch_uploads')
    
    jobs_data = []
    for job in jobs:
        job_info = {
            "id": str(job.id),
            "original_filename": job.original_filename,
            "status": job.status,
            "progress": f"{job.processed_rows}/{job.total_rows}",
            "created_at": job.created_at.isoformat(),
            "error_log": job.error_log,
        }
        
        if job.csv_file:
            job_info["csv_file_field"] = str(job.csv_file)
            job_info["csv_file_path"] = job.csv_file.path
            job_info["file_exists"] = os.path.exists(job.csv_file.path)
            
            if os.path.exists(job.csv_file.path):
                job_info["file_size"] = os.path.getsize(job.csv_file.path)
                try:
                    with open(job.csv_file.path, 'r', encoding='utf-8') as f:
                        job_info["file_preview"] = f.read(200)
                except Exception as e:
                    job_info["file_read_error"] = str(e)
        else:
            job_info["csv_file_field"] = None
        
        jobs_data.append(job_info)
    
    # Get directory info
    batch_uploads_exists = os.path.exists(batch_uploads_path)
    batch_uploads_files = []
    if batch_uploads_exists:
        try:
            batch_uploads_files = os.listdir(batch_uploads_path)[:20]
        except Exception as e:
            batch_uploads_files = [f"Error: {e}"]
    
    return JsonResponse({
        "media_root": media_root,
        "media_root_exists": os.path.exists(media_root),
        "batch_uploads_path": batch_uploads_path,
        "batch_uploads_exists": batch_uploads_exists,
        "batch_uploads_files": batch_uploads_files,
        "jobs": jobs_data,
    })


@require_POST
@csrf_exempt
@license_required
def sync_site_profile_view(request):
    """
    Trigger site profile synchronization.
    
    POST /api/v1/project/sync-profile
    Headers: X-License-Key
    """
    project = request.project
    
    # Trigger task
    sync_site_profile.delay(str(project.id))
    
    return JsonResponse({
        "success": True,
        "message": "Synchronization started"
    })


@require_GET
@csrf_exempt
@license_required
def editorial_plan_view(request):
    """
    Get the latest active or pending editorial plan.
    
    GET /api/v1/project/editorial-plan
    Headers: X-License-Key
    """
    project = request.project
    
    # Get latest active or pending plan
    plan = EditorialPlan.objects.filter(
        project=project
    ).exclude(
        status=EditorialPlan.Status.REJECTED
    ).order_by('-created_at').first()
    
    if not plan:
        return JsonResponse({
            "success": True,
            "has_plan": False,
            "message": "No active plan found"
        })
    
    # Get items
    items = plan.items.all().order_by('day_index')
    
    items_data = []
    for item in items:
        # Determine status color/text for UI
        status_label = item.get_status_display()
        
        items_data.append({
            "id": str(item.id),
            "day": item.day_index,
            "title": item.title,
            "keyword": item.keyword_focus,
            "status": item.status,
            "status_label": status_label,
            "scheduled_date": item.scheduled_date.isoformat() if item.scheduled_date else None,
            "post_id": str(item.post.id) if item.post else None,
        })
    
    return JsonResponse({
        "success": True,
        "has_plan": True,
        "plan": {
            "id": str(plan.id),
            "status": plan.status,
            "status_label": plan.get_status_display(),
            "start_date": plan.start_date.isoformat(),
            "created_at": plan.created_at.isoformat(),
        },
        "items": items_data
    })


@require_POST
@csrf_exempt
@license_required
def save_keywords_view(request):
    """
    Save niche keywords for the project.
    
    POST /api/v1/project/keywords
    Headers: X-License-Key
    Body: {"keywords": ["keyword1", "keyword2", ...]}
    """
    project = request.project
    
    try:
        data = json.loads(request.body)
        keywords = data.get('keywords', [])
        
        # Validate: 5-10 keywords required
        if len(keywords) < 5:
            return JsonResponse({
                "success": False,
                "error": "Minimum 5 keywords required"
            }, status=400)
        
        if len(keywords) > 10:
            keywords = keywords[:10]  # Limit to 10
        
        # Save to project (use a JSONField or create a new model)
        # For now, store in project's metadata or create EditorialPlan
        from apps.automation.models import EditorialPlan
        from datetime import date, timedelta
        
        # Create or update pending plan with keywords
        plan, created = EditorialPlan.objects.update_or_create(
            project=project,
            status__in=[EditorialPlan.Status.PENDING_APPROVAL, EditorialPlan.Status.GENERATING],
            defaults={
                'keywords': keywords,
                'start_date': date.today() + timedelta(days=1),
                'status': EditorialPlan.Status.PENDING_APPROVAL,
            }
        )
        
        return JsonResponse({
            "success": True,
            "message": "Keywords saved successfully",
            "plan_id": str(plan.id),
            "keywords_count": len(keywords)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON body"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)
