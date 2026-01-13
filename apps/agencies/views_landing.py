"""
Views para Landing Page da Agência.
CRUD e geração de copy com IA.
"""

import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.decorators import agency_required
from .models import Agency, AgencyLandingPage, AgencyLead

logger = logging.getLogger(__name__)


@login_required
@agency_required
def landing_config_view(request):
    """Configurar landing page da agência."""
    agency = request.user.agency
    
    # Get or create landing page
    landing_page, created = AgencyLandingPage.objects.get_or_create(
        agency=agency,
        defaults={
            'cta_text': 'Começar Agora',
        }
    )
    
    if request.method == 'POST':
        # Update landing page fields
        landing_page.hero_title = request.POST.get('hero_title', '').strip()
        landing_page.hero_subtitle = request.POST.get('hero_subtitle', '').strip()
        landing_page.about_section = request.POST.get('about_section', '').strip()
        landing_page.cta_text = request.POST.get('cta_text', 'Começar Agora').strip()
        landing_page.meta_title = request.POST.get('meta_title', '').strip()
        landing_page.meta_description = request.POST.get('meta_description', '').strip()
        landing_page.whatsapp_number = request.POST.get('whatsapp_number', '').strip()
        landing_page.email_contact = request.POST.get('email_contact', '').strip()
        landing_page.is_published = request.POST.get('is_published') == 'on'
        
        landing_page.save()
        messages.success(request, 'Landing page atualizada com sucesso!')
        return redirect('dashboard:landing_config')
    
    # Get plans for preview
    plans = agency.client_plans.filter(is_active=True).order_by('order', 'posts_per_month')
    
    context = {
        'landing_page': landing_page,
        'plans': plans,
        'public_url': f"/p/{agency.slug}/" if landing_page.is_published else None,
    }
    return render(request, 'agencies/landing/config.html', context)


@login_required
@agency_required
@require_POST
def landing_generate_ai_view(request):
    """Gerar copy da landing page com IA (AJAX) - V2."""
    agency = request.user.agency
    
    # Check if agency has API key
    if not agency.get_openrouter_key():
        return JsonResponse({
            'success': False,
            'error': 'Você precisa configurar sua chave OpenRouter API antes de gerar conteúdo com IA.'
        }, status=400)
    
    try:
        from services.landing_page_ai import LandingPageAIService, CopyTone
        
        # Get or create landing page
        landing_page, _ = AgencyLandingPage.objects.get_or_create(
            agency=agency,
            defaults={'cta_text': 'Começar Agora'}
        )
        
        # Get tone from request (default: professional)
        tone_value = request.POST.get('tone', 'professional')
        try:
            tone = CopyTone(tone_value)
        except ValueError:
            tone = CopyTone.PROFESSIONAL
        
        # Generate copy with V2 service
        service = LandingPageAIService(agency=agency, tone=tone)
        content = service.update_landing_page(landing_page, use_cache=False)
        
        return JsonResponse({
            'success': True,
            'message': 'Conteúdo gerado com sucesso!',
            'data': {
                'hero_title': landing_page.hero_title,
                'hero_subtitle': landing_page.hero_subtitle,
                'about_section': landing_page.about_section,
                'cta_text': landing_page.cta_text,
                'meta_title': landing_page.meta_title,
                'meta_description': landing_page.meta_description,
            },
            'extended': content  # Full AI response including FAQ, benefits, etc.
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error generating landing copy: {e}\n{error_details}")
        return JsonResponse({
            'success': False,
            'error': f'Erro: {str(e)}',
            'detail': error_details
        }, status=500)


@login_required
@agency_required
def landing_preview_view(request):
    """Preview da landing page (iframe ou full page)."""
    agency = request.user.agency
    
    try:
        landing_page = agency.landing_page
    except AgencyLandingPage.DoesNotExist:
        messages.warning(request, 'Configure sua landing page primeiro.')
        return redirect('dashboard:landing_config')
    
    plans = agency.client_plans.filter(is_active=True).order_by('order', 'posts_per_month')
    
    context = {
        'agency': agency,
        'landing_page': landing_page,
        'plans': plans,
        'is_preview': True,
    }
    return render(request, 'landing_page/public_v2.html', context)


@login_required
@agency_required
def leads_list_view(request):
    """Lista de leads capturados."""
    agency = request.user.agency
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    leads = agency.leads.all().order_by('-created_at')
    
    if status_filter:
        leads = leads.filter(status=status_filter)
    
    # Stats
    stats = {
        'total': agency.leads.count(),
        'new': agency.leads.filter(status='new').count(),
        'contacted': agency.leads.filter(status='contacted').count(),
        'converted': agency.leads.filter(status='converted').count(),
    }
    
    context = {
        'leads': leads,
        'stats': stats,
        'status_filter': status_filter,
        'status_choices': AgencyLead.Status.choices,
    }
    return render(request, 'agencies/landing/leads.html', context)


@login_required
@agency_required
@require_POST
def lead_status_update_view(request, lead_id):
    """Atualizar status do lead (AJAX)."""
    agency = request.user.agency
    
    lead = get_object_or_404(AgencyLead, id=lead_id, agency=agency)
    
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        notes = data.get('notes')
        
        if new_status and new_status in dict(AgencyLead.Status.choices):
            lead.status = new_status
        
        if notes is not None:
            lead.notes = notes
        
        lead.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Lead atualizado!',
            'status': lead.status,
            'status_display': lead.get_status_display(),
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dados inválidos'
        }, status=400)
