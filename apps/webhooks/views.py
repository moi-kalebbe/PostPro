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
    Accepts pushed data from plugin or triggers background sync.
    
    POST /api/v1/project/sync-profile
    Headers: X-License-Key
    Body (optional): {site_title, categories, tags, ...}
    """
    project = request.project
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}
        
    # If data is provided, update synchronously (Push mode)
    if data and (data.get('categories') or data.get('site_title')):
        from apps.automation.models import SiteProfile
        from django.utils import timezone
        
        profile, created = SiteProfile.objects.get_or_create(
            project=project,
            defaults={
                'site_name': project.name,
                'home_url': project.wordpress_url,
            }
        )
        
        # Update fields
        if data.get('site_title'):
            profile.site_name = data['site_title']
        if data.get('site_description'):
            profile.site_description = data['site_description']
        if data.get('site_url'):
            profile.home_url = data['site_url']
        if data.get('language'):
            profile.language = data['language']
            
        if 'categories' in data:
            profile.categories = data['categories']
        if 'tags' in data:
            profile.tags = data['tags']
        if 'recent_posts' in data:
            profile.recent_posts = data['recent_posts']
            
        profile.last_synced_at = timezone.now()
        profile.save()
        
        return JsonResponse({
            "success": True,
            "message": "Profile synced successfully (pushed)",
            "profile_id": str(profile.id)
        })
    
    # Fallback: Trigger background task (Pull mode)
    sync_site_profile.delay(str(project.id))
    
    return JsonResponse({
        "success": True,
        "message": "Synchronization started (background)"
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
        
        # Check active/generating plans first
        plan = EditorialPlan.objects.filter(
            project=project,
            status__in=[EditorialPlan.Status.PENDING_APPROVAL, EditorialPlan.Status.GENERATING]
        ).first()

        if plan:
            plan.keywords = keywords
            plan.start_date = date.today() + timedelta(days=1)
            plan.status = EditorialPlan.Status.GENERATING
            plan.save()
        else:
            plan = EditorialPlan.objects.create(
                project=project,
                keywords=keywords,
                start_date=date.today() + timedelta(days=1),
                status=EditorialPlan.Status.GENERATING
            )
            
        # Trigger generation task logic
        from apps.automation.tasks import generate_editorial_plan
        generate_editorial_plan.delay(str(plan.id))
        
        return JsonResponse({
            "success": True,
            "message": "Keywords saved and plan generation started",
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


@require_POST
@csrf_exempt
@license_required
def approve_plan_item_view(request, item_id):
    """
    Approve a single editorial plan item and start generation.
    
    POST /api/v1/project/editorial-plan/item/<item_id>/approve
    Headers: X-License-Key
    """
    from apps.automation.models import EditorialPlanItem
    from apps.automation.tasks import generate_post_from_plan_item
    
    project = request.project
    
    try:
        item = EditorialPlanItem.objects.select_related('plan').get(
            id=item_id,
            plan__project=project
        )
    except EditorialPlanItem.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Item not found"
        }, status=404)
    
    if item.status not in [EditorialPlanItem.Status.PENDING, EditorialPlanItem.Status.FAILED]:
        return JsonResponse({
            "success": False,
            "error": f"Item cannot be approved (current status: {item.status})"
        }, status=400)
    
    # Mark as scheduled/generating
    item.status = EditorialPlanItem.Status.SCHEDULED
    item.save(update_fields=['status'])
    
    # Trigger post generation
    generate_post_from_plan_item.delay(str(item.id))
    
    return JsonResponse({
        "success": True,
        "message": "Item approved and generation started",
        "item_id": str(item.id),
        "status": item.status
    })


@require_POST
@csrf_exempt
@license_required
def approve_all_plan_items_view(request):
    """
    Approve all pending items in the current editorial plan.
    
    POST /api/v1/project/editorial-plan/approve-all
    Headers: X-License-Key
    """
    from apps.automation.models import EditorialPlanItem
    from apps.automation.tasks import generate_post_from_plan_item
    
    project = request.project
    
    # Get active plan
    plan = EditorialPlan.objects.filter(
        project=project
    ).exclude(
        status__in=[EditorialPlan.Status.REJECTED, EditorialPlan.Status.COMPLETED]
    ).order_by('-created_at').first()
    
    if not plan:
        return JsonResponse({
            "success": False,
            "error": "No active plan found"
        }, status=404)
    
    # Get pending items
    pending_items = plan.items.filter(
        status__in=[EditorialPlanItem.Status.PENDING, EditorialPlanItem.Status.FAILED]
    )
    
    count = pending_items.count()
    if count == 0:
        return JsonResponse({
            "success": True,
            "message": "No pending items to approve",
            "approved_count": 0
        })
    
    # Update all to SCHEDULED
    pending_items.update(status=EditorialPlanItem.Status.SCHEDULED)
    
    # Update plan status
    plan.status = EditorialPlan.Status.APPROVED
    plan.save(update_fields=['status'])
    
    # Trigger generation for each
    for item in plan.items.filter(status=EditorialPlanItem.Status.SCHEDULED):
        generate_post_from_plan_item.delay(str(item.id))
    
    return JsonResponse({
        "success": True,
        "message": f"All {count} items approved and generation started",
        "approved_count": count,
        "plan_status": plan.status
    })


@require_POST
@csrf_exempt
@license_required
def update_plan_item_view(request, item_id):
    """
    Update an editorial plan item (title/keyword).
    
    POST /api/v1/project/editorial-plan/item/<item_id>
    Headers: X-License-Key
    Body: {"title": "...", "keyword_focus": "..."}
    """
    from apps.automation.models import EditorialPlanItem
    
    project = request.project
    
    try:
        item = EditorialPlanItem.objects.select_related('plan').get(
            id=item_id,
            plan__project=project
        )
    except EditorialPlanItem.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Item not found"
        }, status=404)
    
    # Only allow edits on pending items
    if item.status not in [EditorialPlanItem.Status.PENDING, EditorialPlanItem.Status.FAILED]:
        return JsonResponse({
            "success": False,
            "error": "Cannot edit item that is already being processed"
        }, status=400)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON body"
        }, status=400)
    
    # Update fields
    if 'title' in data:
        item.title = data['title'][:500]
    if 'keyword_focus' in data:
        item.keyword_focus = data['keyword_focus'][:200]
    
    item.save(update_fields=['title', 'keyword_focus'])
    
    return JsonResponse({
        "success": True,
        "message": "Item updated",
        "item": {
            "id": str(item.id),
            "title": item.title,
            "keyword_focus": item.keyword_focus,
            "status": item.status
        }
    })


@require_POST
@csrf_exempt
@license_required
def reject_plan_view(request):
    """
    Reject current plan and regenerate with new topics.
    Avoids previously rejected topics.
    
    POST /api/v1/project/editorial-plan/reject
    Headers: X-License-Key
    """
    from apps.automation.models import EditorialPlan as EP
    from apps.automation.tasks import generate_editorial_plan
    from datetime import date, timedelta
    
    project = request.project
    
    # Get current active plan
    current_plan = EP.objects.filter(
        project=project
    ).exclude(
        status__in=[EP.Status.REJECTED, EP.Status.COMPLETED]
    ).order_by('-created_at').first()
    
    if not current_plan:
        return JsonResponse({
            "success": False,
            "error": "No active plan to reject"
        }, status=404)
    
    # Collect topics to avoid from current plan
    avoid_topics = list(current_plan.items.values_list('title', flat=True))
    
    # Also collect from previously rejected plans
    rejected_plans = EP.objects.filter(
        project=project,
        status=EP.Status.REJECTED
    )
    for rp in rejected_plans:
        avoid_topics.extend(list(rp.items.values_list('title', flat=True)))
    
    # Mark current as rejected
    current_plan.status = EP.Status.REJECTED
    current_plan.rejection_reason = "Rejected by user via plugin"
    current_plan.save(update_fields=['status', 'rejection_reason'])
    
    # Create new plan
    new_plan = EP.objects.create(
        project=project,
        keywords=current_plan.keywords,  # Reuse same keywords
        start_date=date.today() + timedelta(days=1),
        status=EP.Status.GENERATING
    )
    
    # Trigger generation with avoid list
    generate_editorial_plan.delay(str(new_plan.id), avoid_topics=avoid_topics)
    
    return JsonResponse({
        "success": True,
        "message": "Plan rejected. Generating new plan with fresh topics.",
        "rejected_plan_id": str(current_plan.id),
        "new_plan_id": str(new_plan.id),
        "avoided_topics_count": len(avoid_topics)
    })

