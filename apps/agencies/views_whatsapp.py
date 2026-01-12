"""
WhatsApp/Wuzapi configuration views for agencies.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST

from apps.accounts.decorators import agency_required
from services.wuzapi import WuzapiService


@login_required
@agency_required
def whatsapp_config_view(request):
    """WhatsApp configuration page."""
    agency = request.user.agency
    
    context = {
        'agency': agency,
        'is_configured': bool(agency.wuzapi_token),
        'is_connected': agency.wuzapi_connected,
    }
    
    return render(request, 'agencies/whatsapp_config.html', context)


@login_required
@agency_required
@require_POST
def whatsapp_setup_view(request):
    """Create Wuzapi user for the agency."""
    agency = request.user.agency
    service = WuzapiService(agency)
    
    # If user already exists, delete first
    if agency.wuzapi_user_id:
        service.delete_wuzapi_user()
    
    # Create new user
    result = service.create_wuzapi_user()
    
    if result['success']:
        return JsonResponse({
            'success': True,
            'message': 'Configuração criada! Agora conecte seu WhatsApp.'
        })
    
    return JsonResponse(result, status=400)


@login_required
@agency_required
@require_POST
def whatsapp_connect_view(request):
    """Start WhatsApp connection."""
    agency = request.user.agency
    
    if not agency.wuzapi_token:
        return JsonResponse({
            'success': False,
            'message': 'Configure o WhatsApp primeiro'
        }, status=400)
    
    service = WuzapiService(agency)
    result = service.connect()
    
    return JsonResponse(result)


@login_required
@agency_required
def whatsapp_qr_view(request):
    """Get QR code for WhatsApp connection."""
    agency = request.user.agency
    
    if not agency.wuzapi_token:
        return JsonResponse({
            'success': False,
            'message': 'Configure o WhatsApp primeiro'
        }, status=400)
    
    service = WuzapiService(agency)
    result = service.get_qr_code()
    
    return JsonResponse(result)


@login_required
@agency_required
def whatsapp_status_view(request):
    """Check WhatsApp connection status."""
    agency = request.user.agency
    
    if not agency.wuzapi_token:
        return JsonResponse({
            'success': False,
            'connected': False,
            'message': 'WhatsApp não configurado'
        })
    
    service = WuzapiService(agency)
    result = service.get_status()
    
    return JsonResponse(result)


@login_required
@agency_required
@require_POST
def whatsapp_disconnect_view(request):
    """Disconnect WhatsApp."""
    agency = request.user.agency
    
    if not agency.wuzapi_token:
        return JsonResponse({
            'success': False,
            'message': 'WhatsApp não configurado'
        }, status=400)
    
    service = WuzapiService(agency)
    result = service.disconnect()
    
    if result['success']:
        messages.success(request, 'WhatsApp desconectado.')
    
    return JsonResponse(result)
