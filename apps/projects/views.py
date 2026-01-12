"""
Project views for PostPro.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count

from apps.accounts.decorators import agency_required, project_access_required
from apps.automation.models import Post, BatchJob
from .models import Project, RSSFeed
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
            
            # Save extra content settings
            settings = project.content_settings
            settings.min_word_count = form.cleaned_data.get('min_word_count', 1200)
            settings.max_word_count = form.cleaned_data.get('max_word_count', 2000)
            settings.save()

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
    from apps.automation.models import EditorialPlan, RSSItem
    editorial_plan = EditorialPlan.objects.filter(
        project=project,
        status__in=[EditorialPlan.Status.GENERATING, EditorialPlan.Status.ACTIVE, EditorialPlan.Status.PENDING_APPROVAL, EditorialPlan.Status.APPROVED]
    ).order_by('-created_at').first()
    
    editorial_items = []
    if editorial_plan:
        editorial_items = editorial_plan.items.all().order_by('day_index')[:30]
    
    # RSS Settings
    from .models import ProjectRSSSettings
    try:
        rss_settings = project.rss_settings
    except ProjectRSSSettings.DoesNotExist:
        rss_settings = None
    
    # RSS Items (pending and recent)
    rss_items = RSSItem.objects.filter(
        project=project
    ).order_by('-created_at')[:20]
    
    # RSS Feeds
    feeds = project.rss_feeds.all()
    
    context = {
        'project': project,
        'recent_posts': recent_posts,
        'stats': stats,
        'editorial_plan': editorial_plan,
        'editorial_items': editorial_items,
        'rss_settings': rss_settings,
        'rss_items': rss_items,
        'feeds': feeds,
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
            
            # Save extra content settings
            settings = project.content_settings
            settings.min_word_count = form.cleaned_data.get('min_word_count', 1200)
            settings.max_word_count = form.cleaned_data.get('max_word_count', 2000)
            settings.save()

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


@login_required
@project_access_required
def editorial_item_delete_view(request, project_id, item_id):
    """Delete a single editorial plan item and optionally from WordPress."""
    from django.http import JsonResponse
    from django.views.decorators.http import require_POST
    from apps.automation.models import EditorialPlanItem, ActivityLog
    from services.wordpress import WordPressService
    import json
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required'}, status=405)
    
    project = request.project
    
    try:
        item = EditorialPlanItem.objects.select_related('plan', 'post').get(
            id=item_id,
            plan__project=project
        )
    except EditorialPlanItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Item não encontrado'}, status=404)
    
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}
    
    delete_from_wp = data.get('delete_from_wordpress', False)
    wp_result = None
    
    # If item has a linked post published to WordPress, delete it
    if delete_from_wp and item.post and item.post.wordpress_post_id:
        try:
            wp_password = project.get_wordpress_password()
            if wp_password and project.wordpress_username:
                wp_service = WordPressService(
                    site_url=project.wordpress_url,
                    username=project.wordpress_username,
                    app_password=wp_password
                )
                wp_result = wp_service.delete_post(item.post.wordpress_post_id)
        except Exception as e:
            wp_result = {'success': False, 'message': str(e)}
    
    # Log activity
    ActivityLog.objects.create(
        agency=project.agency,
        project=project,
        actor_user=request.user,
        action="EDITORIAL_ITEM_DELETED",
        entity_type="EditorialPlanItem",
        entity_id=str(item.id),
        metadata={
            "title": item.title,
            "keyword": item.keyword_focus,
            "deleted_from_wp": delete_from_wp,
            "wp_result": wp_result,
        }
    )
    
    # Delete associated post if exists
    if item.post:
        item.post.delete()
    
    # Delete the item
    item.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Item excluído com sucesso',
        'deleted_from_wordpress': wp_result.get('success', False) if wp_result else False,
    })


@login_required
@project_access_required
def editorial_items_bulk_delete_view(request, project_id):
    """Delete multiple editorial plan items at once."""
    from django.http import JsonResponse
    from apps.automation.models import EditorialPlanItem, ActivityLog
    from services.wordpress import WordPressService
    import json
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required'}, status=405)
    
    project = request.project
    
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    
    item_ids = data.get('item_ids', [])
    delete_from_wp = data.get('delete_from_wordpress', False)
    
    if not item_ids:
        return JsonResponse({'success': False, 'message': 'Nenhum item selecionado'}, status=400)
    
    # Get items
    items = EditorialPlanItem.objects.filter(
        id__in=item_ids,
        plan__project=project
    ).select_related('plan', 'post')
    
    deleted_count = 0
    wp_deleted_count = 0
    
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
    
    for item in items:
        try:
            # Delete from WordPress if applicable
            if wp_service and item.post and item.post.wordpress_post_id:
                result = wp_service.delete_post(item.post.wordpress_post_id)
                if result.get('success'):
                    wp_deleted_count += 1
            
            # Log activity
            ActivityLog.objects.create(
                agency=project.agency,
                project=project,
                actor_user=request.user,
                action="EDITORIAL_ITEM_DELETED",
                entity_type="EditorialPlanItem",
                entity_id=str(item.id),
                metadata={
                    "title": item.title,
                    "bulk_delete": True,
                }
            )
            
            # Delete associated post
            if item.post:
                item.post.delete()
            
            # Delete item
            item.delete()
            deleted_count += 1
            
        except Exception as e:
            continue
    
    return JsonResponse({
        'success': True,
        'message': f'{deleted_count} item(ns) excluído(s)',
        'deleted_count': deleted_count,
        'wp_deleted_count': wp_deleted_count,
    })


@login_required
@project_access_required
def rss_settings_view(request, project_id):
    """Save RSS feed general settings for a project."""
    from .models import ProjectRSSSettings
    
    project = request.project
    
    if request.method != 'POST':
        return redirect('projects:detail', project_id=project.id)
    
    # Get or create RSS settings
    rss_settings, created = ProjectRSSSettings.objects.get_or_create(
        project=project,
        defaults={
            'is_active': False,
        }
    )
    
    # Update settings from form (Global Settings)
    rss_settings.check_interval_minutes = int(request.POST.get('check_interval_minutes', 60))
    rss_settings.max_posts_per_day = int(request.POST.get('max_posts_per_day', 5))
    rss_settings.is_active = 'is_active' in request.POST
    rss_settings.auto_publish = 'auto_publish' in request.POST
    rss_settings.download_images = 'download_images' in request.POST
    rss_settings.include_source_attribution = 'include_source_attribution' in request.POST
    
    rss_settings.save()
    
    messages.success(request, 'Configurações RSS globais salvas com sucesso!')
    return redirect('projects:detail', project_id=project.id)


@login_required
@project_access_required
def rss_feed_create_view(request, project_id):
    """Add a new RSS feed to the project."""
    project = request.project
    
    if request.method == 'POST':
        feed_url = request.POST.get('feed_url', '').strip()
        name = request.POST.get('name', '').strip()
        
        if not feed_url:
            messages.error(request, 'URL do feed é obrigatória.')
            return redirect('projects:detail', project_id=project.id)
            
        try:
            from services.rss import RSSService
            rss_service = RSSService()
            is_valid, message = rss_service.validate_feed_url(feed_url)
            
            if is_valid:
                RSSFeed.objects.create(
                    project=project,
                    feed_url=feed_url,
                    name=name or message.split(' ')[0] # Simple fallback or just url
                )
                messages.success(request, 'Feed adicionado com sucesso!')
            else:
                messages.error(request, f'Erro ao validar feed: {message}')
        except Exception as e:
            messages.error(request, f'Erro ao adicionar feed: {e}')
            
    return redirect('projects:detail', project_id=project.id)


@login_required
@project_access_required
def rss_feed_delete_view(request, project_id, feed_id):
    """Delete an RSS feed."""
    feed = get_object_or_404(RSSFeed, id=feed_id, project=request.project)
    
    if request.method == 'POST':
        feed.delete()
        messages.success(request, 'Feed removido com sucesso.')
        
    return redirect('projects:detail', project_id=project_id)
