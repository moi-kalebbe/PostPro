"""
Script de Limpeza Total e Reset do Banco de Dados para PostPro.
Remove todos os Posts, Planos Editoriais e Logs do projeto de teste.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.automation.models import Post, PostArtifact, EditorialPlan, EditorialPlanItem, ActivityLog
from apps.projects.models import Project

def reset_project_data():
    project = Project.objects.first()
    if not project:
        print("❌ Nenhum projeto encontrado para limpar.")
        return

    print(f"🧹 Iniciando limpeza do projeto: {project.name} ({project.id})")
    
    # 1. Delete Activity Logs
    logs_deleted, _ = ActivityLog.objects.filter(project=project).delete()
    print(f"   - Logs de atividade: {logs_deleted} removidos")
    
    # 2. Delete Posts (will cascade artifacts)
    posts_deleted, _ = Post.objects.filter(project=project).delete()
    print(f"   - Posts: {posts_deleted} removidos")
    
    # 3. Delete Editorial Plans (will cascade items)
    plans_deleted, _ = EditorialPlan.objects.filter(project=project).delete()
    print(f"   - Planos Editoriais: {plans_deleted} removidos")

    print("\n✅ LIMPEZA TOTAL CONCLUÍDA! O banco está zerado para testes.")

if __name__ == '__main__':
    reset_project_data()
