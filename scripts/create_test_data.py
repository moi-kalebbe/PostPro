"""
Script para criar dados de teste no banco de dados local.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.automation.models import EditorialPlan, EditorialPlanItem
from apps.projects.models import Project
from datetime import date, timedelta

# Get the test project
project = Project.objects.first()
if project:
    print(f'Projeto: {project.name} ({project.id})')
    
    # Delete existing plans and items for clean start
    existing_plans = EditorialPlan.objects.filter(project=project)
    if existing_plans.exists():
        print(f'Removendo {existing_plans.count()} planos existentes...')
        existing_plans.delete()
    
    # Create new editorial plan
    plan = EditorialPlan.objects.create(
        project=project,
        keywords=['marketing digital', 'SEO', 'redes sociais', 'email marketing', 'conteudo'],
        start_date=date.today(),
        status='active'
    )
    print(f'Plano criado: {plan.id}')
    
    # Create some test items
    today = date.today()
    test_items = [
        ('Como Criar uma Estrategia de Marketing Digital do Zero', 'estrategia marketing digital'),
        ('10 Metricas Essenciais de Marketing Digital para Acompanhar', 'metricas marketing digital'),
        ('SEO para Iniciantes: Guia Completo para Ranquear no Google', 'seo para iniciantes'),
        ('Como Criar uma Campanha de Email Marketing que Converte', 'email marketing conversao'),
        ('7 Estrategias de Marketing de Conteudo que Funcionam', 'estrategias marketing conteudo'),
        ('Guia Definitivo de Marketing no TikTok para Empresas', 'marketing tiktok'),
        ('Como Fazer Analise de Concorrentes no Marketing Digital', 'analise concorrentes marketing'),
        ('Melhores Ferramentas de Marketing Digital em 2024', 'ferramentas marketing digital'),
        ('Como Criar uma Landing Page que Converte: Passo a Passo', 'landing page conversao'),
        ('Marketing B2B vs B2C: Principais Diferencas e Estrategias', 'marketing b2b b2c'),
    ]
    
    for i, (title, keyword) in enumerate(test_items, 1):
        # Generate external_id
        external_id = f"{project.id}_{plan.id}_day_{i}"
        
        item = EditorialPlanItem.objects.create(
            plan=plan,
            day_index=i,
            title=title,
            keyword_focus=keyword,
            scheduled_date=today + timedelta(days=i),
            status='pending',
            external_id=external_id
        )
        print(f'  Item {i}: {title[:40]}...')
    
    print(f'\n✅ Total items no plano: {plan.items.count()}')
    print(f'\n🔗 Acesse: http://localhost:8000/projects/{project.id}/')
else:
    print('❌ Nenhum projeto encontrado! Crie um projeto primeiro.')
