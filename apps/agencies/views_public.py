"""
Views públicas para Landing Page da Agência.
Acessíveis sem login em /p/{agency-slug}/
"""

import json
import logging
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import Agency, AgencyLandingPage, AgencyLead, AgencyClientPlan

logger = logging.getLogger(__name__)


def public_landing_view(request, slug):
    """Renderiza a landing page pública da agência."""
    agency = get_object_or_404(Agency, slug=slug)
    
    # Check if landing page exists and is published
    try:
        landing_page = agency.landing_page
        if not landing_page.is_published:
            # Not published - show 404 or coming soon
            return render(request, 'landing_page/not_published.html', {
                'agency': agency
            }, status=404)
    except AgencyLandingPage.DoesNotExist:
        return render(request, 'landing_page/not_published.html', {
            'agency': agency
        }, status=404)
    
    # Get active plans
    plans = agency.client_plans.filter(is_active=True).order_by('order', 'posts_per_month')
    
    # UTM tracking from query params
    utm_data = {
        'utm_source': request.GET.get('utm_source', ''),
        'utm_medium': request.GET.get('utm_medium', ''),
        'utm_campaign': request.GET.get('utm_campaign', ''),
    }
    
    context = {
        'agency': agency,
        'landing_page': landing_page,
        'plans': plans,
        'utm_data': utm_data,
        'is_preview': False,
    }
    return render(request, 'landing_page/public_v2.html', context)


@csrf_exempt
@require_POST
def public_lead_submit_view(request, slug):
    """Recebe submissão de lead da landing page (AJAX)."""
    agency = get_object_or_404(Agency, slug=slug)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dados inválidos'
        }, status=400)
    
    # Validate required fields
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    
    if not name or not email:
        return JsonResponse({
            'success': False,
            'error': 'Nome e email são obrigatórios'
        }, status=400)
    
    # Get optional plan
    plan_id = data.get('plan_id')
    plan = None
    if plan_id:
        try:
            plan = AgencyClientPlan.objects.get(id=plan_id, agency=agency)
        except AgencyClientPlan.DoesNotExist:
            pass
    
    # Create lead
    lead = AgencyLead.objects.create(
        agency=agency,
        plan=plan,
        name=name,
        email=email,
        phone=data.get('phone', '').strip(),
        company_name=data.get('company_name', '').strip(),
        message=data.get('message', '').strip(),
        utm_source=data.get('utm_source', ''),
        utm_medium=data.get('utm_medium', ''),
        utm_campaign=data.get('utm_campaign', ''),
    )
    
    logger.info(f"New lead captured for agency {agency.name}: {name} ({email})")
    
    # Optional: Send WhatsApp notification
    try:
        if agency.wuzapi_connected and agency.wuzapi_token:
            from services.wuzapi import notify_new_lead
            notify_new_lead(agency, lead)
    except Exception as e:
        logger.warning(f"Failed to send WhatsApp notification: {e}")
    
    return JsonResponse({
        'success': True,
        'message': 'Obrigado pelo contato! Entraremos em contato em breve.'
    })
