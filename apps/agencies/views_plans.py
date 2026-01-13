"""
Views para CRUD de Planos de Cliente da Agência.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from apps.accounts.decorators import agency_required
from .models import Agency, AgencyClientPlan


@login_required
@agency_required
def plans_list_view(request):
    """Lista de planos da agência."""
    agency = request.user.agency
    plans = agency.client_plans.filter(is_active=True).order_by('order', 'posts_per_month')
    
    context = {
        'plans': plans,
    }
    return render(request, 'agencies/plans/list.html', context)


@login_required
@agency_required
def plan_create_view(request):
    """Criar novo plano."""
    agency = request.user.agency
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        posts_per_month = request.POST.get('posts_per_month', 30)
        price = request.POST.get('price', '').strip()
        description = request.POST.get('description', '').strip()
        features_raw = request.POST.get('features', '').strip()
        is_highlighted = request.POST.get('is_highlighted') == 'on'
        order = request.POST.get('order', 0)
        
        # Validação
        if not name:
            messages.error(request, 'Nome do plano é obrigatório.')
            return render(request, 'agencies/plans/form.html', {
                'form_data': request.POST,
            })
        
        try:
            posts_per_month = int(posts_per_month)
        except ValueError:
            posts_per_month = 30
        
        # Parse features (uma por linha)
        features = [f.strip() for f in features_raw.split('\n') if f.strip()]
        
        # Parse price
        price_value = None
        if price:
            try:
                price_value = float(price.replace(',', '.'))
            except ValueError:
                price_value = None
        
        try:
            order = int(order)
        except ValueError:
            order = 0
        
        # Criar plano
        plan = AgencyClientPlan.objects.create(
            agency=agency,
            name=name,
            posts_per_month=posts_per_month,
            price=price_value,
            description=description,
            features=features,
            is_highlighted=is_highlighted,
            order=order,
        )
        
        messages.success(request, f'Plano "{name}" criado com sucesso!')
        return redirect('dashboard:plans_list')
    
    return render(request, 'agencies/plans/form.html', {})


@login_required
@agency_required
def plan_edit_view(request, plan_id):
    """Editar plano existente."""
    agency = request.user.agency
    plan = get_object_or_404(AgencyClientPlan, id=plan_id, agency=agency)
    
    if request.method == 'POST':
        plan.name = request.POST.get('name', plan.name).strip()
        plan.description = request.POST.get('description', '').strip()
        
        posts_per_month = request.POST.get('posts_per_month', plan.posts_per_month)
        try:
            plan.posts_per_month = int(posts_per_month)
        except ValueError:
            pass
        
        price = request.POST.get('price', '').strip()
        if price:
            try:
                plan.price = float(price.replace(',', '.'))
            except ValueError:
                pass
        else:
            plan.price = None
        
        features_raw = request.POST.get('features', '').strip()
        plan.features = [f.strip() for f in features_raw.split('\n') if f.strip()]
        
        plan.is_highlighted = request.POST.get('is_highlighted') == 'on'
        
        order = request.POST.get('order', plan.order)
        try:
            plan.order = int(order)
        except ValueError:
            pass
        
        plan.save()
        messages.success(request, f'Plano "{plan.name}" atualizado!')
        return redirect('dashboard:plans_list')
    
    # Preparar features como texto (uma por linha)
    features_text = '\n'.join(plan.get_features_list())
    
    context = {
        'plan': plan,
        'features_text': features_text,
        'edit_mode': True,
    }
    return render(request, 'agencies/plans/form.html', context)


@login_required
@agency_required
@require_http_methods(["POST"])
def plan_delete_view(request, plan_id):
    """Excluir plano (soft delete)."""
    agency = request.user.agency
    plan = get_object_or_404(AgencyClientPlan, id=plan_id, agency=agency)
    
    # Verificar se há projetos usando este plano
    projects_count = plan.projects.count()
    
    if projects_count > 0:
        messages.error(
            request,
            f'Não é possível excluir o plano "{plan.name}" pois existem {projects_count} projeto(s) vinculado(s).'
        )
        return redirect('dashboard:plans_list')
    
    plan_name = plan.name
    plan.is_active = False
    plan.save()
    
    messages.success(request, f'Plano "{plan_name}" excluído com sucesso!')
    return redirect('dashboard:plans_list')
