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
from django.http import JsonResponse
from datetime import timedelta
import json
import secrets
import string

from apps.accounts.decorators import super_admin_required
from apps.accounts.models import User
from apps.automation.models import Post, BatchJob, ActivityLog
from .models import Agency, PLAN_LIMITS, SuperAdminConfig
from services.wuzapi import WuzapiService
import requests
from django.views.decorators.http import require_http_methods
from django.conf import settings


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
        
        elif action == 'delete':
            # Delete agency (destructive)
            agency_name = agency.name
            agency.delete()
            # Log action (before delete? No, after to confirm, but agency obj is gone. Use ID)
            ActivityLog.objects.create(
                actor_user=request.user,
                agency=None,  # Agency deleted
                action='AGENCY_DELETED',
                entity_type='Agency',
                entity_id=str(agency_id),
                metadata={'agency_name': agency_name}
            )
            messages.success(request, f'Agência {agency_name} excluída com sucesso.')
            return redirect('admin_panel:agencies_list')

        elif action == 'resend_credentials':
            # Generate new password and send via WhatsApp
            new_password = generate_password()
            
            # Buscando o owner através da relação reversa 'members'
            # (User tem FK para Agency com related_name='members')
            from apps.accounts.models import User
            owner = agency.members.filter(role=User.Role.AGENCY_OWNER).first()
            
            if owner:
                owner.set_password(new_password)
                owner.save()
                
                # Send WhatsApp
                config = SuperAdminConfig.get_instance()
                whatsapp_sent = False
                
                if config.wuzapi_connected:
                    # Create a temporary "agency-like" object for WuzapiService
                    class TempConfig:
                        def __init__(self, c):
                            self.wuzapi_instance_url = c.wuzapi_instance_url
                            self.wuzapi_token = c.wuzapi_token
                            self.wuzapi_connected = c.wuzapi_connected
                    
                    service = WuzapiService(TempConfig(config))
                    site_url = getattr(settings, 'SITE_URL', 'https://postpro.nuvemchat.com')
                    
                    message = f"""🔐 *Recuperação de Acesso - PostPro*

Olá {agency.owner_name}!

Aqui estão suas novas credenciais de acesso para a agência *{agency.name}*:

🌐 URL: {site_url}/auth/login/
👤 Login: {owner.username}
🔑 Nova Senha: {new_password}

Recomendamos alterar sua senha após o primeiro acesso. 🚀"""
                    
                    # Sanitize destination phone
                    import re
                    dest_phone = re.sub(r'\D', '', agency.owner_phone)
                    if not dest_phone.startswith('55'):
                        dest_phone = '55' + dest_phone
                        
                    result = service.send_message(dest_phone, message)
                    whatsapp_sent = result.get('success', False)
                
                if whatsapp_sent:
                    messages.success(request, f'Novas credenciais enviadas para {agency.owner_phone} via WhatsApp.')
                else:
                    messages.warning(request, f'Senha resetada ({new_password}), mas falha ao enviar WhatsApp. Verifique a conexão.')
            else:
                messages.error(request, 'Agência sem usuário dono vinculado.')

        # Log action (if not deleted)
        if action != 'delete':
            ActivityLog.objects.create(
                actor_user=request.user,
                agency=agency,
                action=f'AGENCY_{action.upper()}',
                entity_type='Agency',
                entity_id=str(agency.id),
                metadata={'action': action}
            )
    
    return redirect('admin_panel:agency_detail', agency_id=agency_id)


def generate_password(length=12):
    """Gera senha segura aleatória."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@login_required
@super_admin_required
def agency_create_view(request):
    """Create new agency with user account."""
    from django.conf import settings
    
    if request.method == 'POST':
        # Get form data
        agency_name = request.POST.get('agency_name', '').strip()
        owner_name = request.POST.get('owner_name', '').strip()
        owner_phone = request.POST.get('owner_phone', '').strip()
        owner_email = request.POST.get('owner_email', '').strip()
        plan = request.POST.get('plan', 'starter')
        send_whatsapp = request.POST.get('send_whatsapp') == 'on'
        
        # Validation - Email agora é obrigatório para login
        if not agency_name or not owner_name or not owner_phone or not owner_email:
            messages.error(request, 'Nome da agência, nome do responsável, telefone e email são obrigatórios.')
            return render(request, 'admin_panel/agency_form.html', {
                'plan_limits': PLAN_LIMITS,
                'form_data': request.POST,
            })
        
        # Format phone for username
        import re
        phone_cleaned = re.sub(r'\D', '', owner_phone)
        if not phone_cleaned.startswith('55'):
            phone_cleaned = '55' + phone_cleaned
        
        # Check if user already exists (by email - usado como username para login)
        if User.objects.filter(email=owner_email).exists():
            messages.error(request, f'Já existe um usuário com este email: {owner_email}')
            return render(request, 'admin_panel/agency_form.html', {
                'plan_limits': PLAN_LIMITS,
                'form_data': request.POST,
            })
        
        # Get plan limits
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS['starter'])
        
        # Create agency
        agency = Agency.objects.create(
            name=agency_name,
            owner_name=owner_name,
            owner_phone=owner_phone,
            owner_email=owner_email,
            plan=plan,
            max_projects=limits['max_projects'],
            monthly_posts_limit=limits['monthly_posts_limit'],
        )
        
        # Generate password
        password = generate_password()
        
        # Create user (usando email como username para login funcionar)
        user = User.objects.create_user(
            username=owner_email,
            email=owner_email,
            password=password,
            first_name=owner_name.split()[0] if owner_name else '',
            last_name=' '.join(owner_name.split()[1:]) if len(owner_name.split()) > 1 else '',
            role=User.Role.AGENCY_OWNER,
            agency=agency,
        )
        
        # Send WhatsApp if enabled
        whatsapp_sent = False
        if send_whatsapp:
            config = SuperAdminConfig.get_instance()
            if config.wuzapi_connected:
                # Create a temporary "agency-like" object for WuzapiService
                class TempConfig:
                    def __init__(self, c):
                        self.wuzapi_instance_url = c.wuzapi_instance_url
                        self.wuzapi_token = c.wuzapi_token
                        self.wuzapi_connected = c.wuzapi_connected
                
                service = WuzapiService(TempConfig(config))
                site_url = getattr(settings, 'SITE_URL', 'https://postpro.nuvemchat.com')
                
                message = f"""🎉 *Bem-vindo ao PostPro!*

Olá {owner_name}!

Sua agência *{agency_name}* foi criada com sucesso!

📱 *Seus dados de acesso:*
🌐 URL: {site_url}/auth/login/
👤 Login: {owner_email}
🔑 Senha: {password}

📊 *Seu plano:*
- Até {limits['max_projects']} projetos
- Até {limits['monthly_posts_limit']} posts/mês

Acesse agora e comece a automatizar! 🚀"""
                
                result = service.send_message(owner_phone, message)
                whatsapp_sent = result.get('success', False)
        
        # Log action
        ActivityLog.objects.create(
            actor_user=request.user,
            agency=agency,
            action='AGENCY_CREATED',
            entity_type='Agency',
            entity_id=str(agency.id),
            metadata={
                'plan': plan,
                'whatsapp_sent': whatsapp_sent,
            }
        )
        
        if whatsapp_sent:
            messages.success(request, f'Agência "{agency_name}" criada! Credenciais enviadas via WhatsApp para {owner_phone}.')
        else:
            messages.success(request, f'Agência "{agency_name}" criada! Login: {owner_email} / Senha: {password}')
        
        return redirect('admin_panel:agencies_list')
    
    context = {
        'plan_limits': PLAN_LIMITS,
    }
    return render(request, 'admin_panel/agency_form.html', context)


@login_required
@super_admin_required
def agency_edit_view(request, agency_id):
    """Edit existing agency."""
    agency = get_object_or_404(Agency, id=agency_id)
    
    if request.method == 'POST':
        # Get form data
        agency.name = request.POST.get('agency_name', agency.name).strip()
        agency.owner_name = request.POST.get('owner_name', agency.owner_name).strip()
        agency.owner_phone = request.POST.get('owner_phone', agency.owner_phone).strip()
        agency.owner_email = request.POST.get('owner_email', agency.owner_email).strip()
        plan = request.POST.get('plan', agency.plan)
        
        # Update plan limits if plan changed
        if plan != agency.plan:
            limits = PLAN_LIMITS.get(plan, PLAN_LIMITS['starter'])
            agency.plan = plan
            agency.max_projects = limits['max_projects']
            agency.monthly_posts_limit = limits['monthly_posts_limit']
        
        agency.save()
        
        # Log action
        ActivityLog.objects.create(
            actor_user=request.user,
            agency=agency,
            action='AGENCY_UPDATED',
            entity_type='Agency',
            entity_id=str(agency.id),
            metadata={'plan': plan}
        )
        
        messages.success(request, f'Agência "{agency.name}" atualizada com sucesso!')
        return redirect('admin_panel:agencies_list')
    
    context = {
        'agency': agency,
        'plan_limits': PLAN_LIMITS,
        'edit_mode': True,
    }
    return render(request, 'admin_panel/agency_form.html', context)


@login_required
@super_admin_required
def superadmin_whatsapp_view(request):
    """SuperAdmin WhatsApp configuration page."""
    config = SuperAdminConfig.get_instance()
    
    context = {
        'config': config,
    }
    return render(request, 'admin_panel/superadmin_whatsapp.html', context)


@require_http_methods(["POST"])
def superadmin_whatsapp_connect_view(request):
    """Handle WhatsApp connection for SuperAdmin with strict flow."""
    try:
        # 1. Ler o corpo JSON
        data = json.loads(request.body.decode('utf-8'))
        action = data.get('action')
        
        # 2. Pegar configuração
        config = SuperAdminConfig.objects.first()
        if not config:
            return JsonResponse({'success': False, 'message': 'Config não encontrada'})
        
        base_url = config.wuzapi_instance_url.rstrip('/')
        
        # Headers para Admin (Criar Usuário)
        admin_headers = {
            'Authorization': settings.WUZAPI_ADMIN_TOKEN,
            'Content-Type': 'application/json'
        }
        
        # Headers para Sessão (Connect, QR, Disconnect) - Usa o token do USUÁRIO
        user_headers = {
            'Token': config.wuzapi_token if config.wuzapi_token else '',
            'Content-Type': 'application/json'
        }
        
        # 4. AÇÕES
        if action == 'reset':
            config.wuzapi_user_id = None
            config.wuzapi_token = None
            config.wuzapi_phone = ''
            config.wuzapi_connected = False
            config.wuzapi_connected_at = None
            config.save()
            return JsonResponse({'success': True, 'message': 'Reset realizado'})
        
        elif action == 'create_user':
            # Criar usuário via Admin API
            # Endpoint: /admin/users
            if not config.wuzapi_user_id or not config.wuzapi_token:
                import secrets
                new_token = secrets.token_hex(32)
                user_name = "superadmin_whatsapp"
                
                try:
                    site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
                    webhook_url = f"{site_url}/api/v1/webhook/wuzapi/superadmin/"
                    
                    payload = {
                        "name": user_name,
                        "token": new_token,
                        "webhook": webhook_url,
                        "events": "Message,ReadReceipt"
                    }
                    
                    # POST /admin/users
                    response = requests.post(
                        f"{base_url}/admin/users",
                        headers=admin_headers,
                        json=payload,
                        timeout=10
                    )
                    
                    if response.status_code in [200, 201]:
                        result = response.json()
                        # Salvar config
                        config.wuzapi_user_id = result.get('id')
                        config.wuzapi_token = new_token
                        config.save()
                        return JsonResponse({'success': True, 'user_id': config.wuzapi_user_id, 'message': 'Usuário criado'})
                    else:
                        return JsonResponse({
                            'success': False,
                            'message': f'Erro ao criar usuário: HTTP {response.status_code}',
                            'detail': response.text
                        })
                except Exception as e:
                     return JsonResponse({
                        'success': False,
                        'message': f'Erro de conexão ao criar usuário: {str(e)}'
                    })
            return JsonResponse({'success': True, 'message': 'Usuário já existe'})
        
        elif action == 'connect':
            # Conectar sessão (Usa headers de Usuário)
            # Endpoint: /session/connect
            if not config.wuzapi_token:
                return JsonResponse({'success': False, 'message': 'Usuário não criado. Resete a configuração.'})
            
            try:
                response = requests.post(
                    f"{base_url}/session/connect",
                    headers=user_headers,
                    json={"Subscribe": ["Message"], "Immediate": False},
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # A resposta pode conter o QR code diretamente ou apenas indicar sucesso
                    qr_code = result.get('qr_code') or result.get('qrcode')
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Sessão iniciada',
                        'qrcode': qr_code
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': f'Erro HTTP {response.status_code}',
                        'detail': response.text
                    })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Erro de conexão no connect: {str(e)}'
                })
        
        elif action == 'get_qr':
            # Buscar QR Code (Usa headers de Usuário)
            # Endpoint: /session/qr
            if not config.wuzapi_token:
                return JsonResponse({'success': False, 'message': 'Usuário não conectado'})
            
            try:
                response = requests.get(
                    f"{base_url}/session/qr",
                    headers=user_headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Wuzapi retorna algo como { "data": { "QRCode": "..." } } ou direto
                    data_obj = result.get('data', {})
                    if isinstance(data_obj, dict):
                        qr_code = data_obj.get('QRCode') or data_obj.get('qr_code')
                    else:
                        qr_code = None
                        
                    if not qr_code:
                         qr_code = result.get('qr_code') or result.get('qrcode')

                    if qr_code:
                        return JsonResponse({
                            'success': True,
                            'qr_code': qr_code,
                            'qrcode': qr_code
                        })
                    else:
                        return JsonResponse({'success': False, 'message': 'QR ainda não gerado'})
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'QR não disponível ainda'
                    })
            except Exception as e:
                 return JsonResponse({'success': False, 'message': str(e)})
        
        elif action == 'disconnect':
            # Desconectar (Usa headers de Usuário)
            # Endpoint: /session/logout
            if config.wuzapi_token:
                try:
                    response = requests.post(
                        f"{base_url}/session/logout",
                        headers=user_headers,
                        timeout=10
                    )
                    
                    config.wuzapi_connected = False
                    config.wuzapi_phone = ''
                    config.wuzapi_connected_at = None
                    config.save()
                    
                    return JsonResponse({'success': True, 'message': 'Desconectado'})
                except Exception as e:
                    return JsonResponse({'success': False, 'message': str(e)})
            return JsonResponse({'success': True, 'message': 'Já desconectado'})
        
        return JsonResponse({'success': False, 'message': 'Ação inválida'})
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        })


@login_required
@super_admin_required
def superadmin_whatsapp_status_view(request):
    """Get WhatsApp connection status for SuperAdmin."""
    config = SuperAdminConfig.get_instance()
    
    if not config.wuzapi_token:
        return JsonResponse({
            'success': True,
            'connected': False,
            'needs_setup': True,
        })
    
    class TempConfig:
        def __init__(self, c):
            self.wuzapi_instance_url = c.wuzapi_instance_url
            self.wuzapi_token = c.wuzapi_token
            self.wuzapi_connected = c.wuzapi_connected
        
        def save(self, **kwargs):
            pass
    
    service = WuzapiService(TempConfig(config))
    result = service.get_status()
    
    if result['success']:
        connected = result.get('connected', False)
        if connected != config.wuzapi_connected:
            config.wuzapi_connected = connected
            if connected:
                config.wuzapi_connected_at = timezone.now()
            config.save()
        
        return JsonResponse({
            'success': True,
            'connected': connected,
            'logged_in': result.get('logged_in', False),
        })
    
    return JsonResponse(result)

