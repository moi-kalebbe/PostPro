#!/usr/bin/env python
"""
Script Django para migrar modelos obsoletos para modelos validados.
Alternativa ao SQL direto - usa Django ORM.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.projects.models import Project
from apps.agencies.models import Agency

# ============================================================================
# MODELOS VALIDADOS
# ============================================================================

VALID_TEXT_MODELS = [
    '', 
    'qwen/qwen3-32b',
    'deepseek/deepseek-v3',
    'mistralai/mistral-small-3',
    'meta-llama/llama-4-scout',
    'anthropic/claude-3-haiku',
    'openai/gpt-4o',
    'qwen/qwen3-coder-480b-a35b',
    'anthropic/claude-3.7-sonnet-thinking',
    'openai/gpt-5-chat',
    'openai/gpt-5.2-pro',
    'mistralai/mistral-large-3-2512',
    'mistralai/codestral-2508',
]

VALID_IMAGE_MODELS = [
    '',
    'pollinations/flux',
    'pollinations/turbo',
    'pollinations/flux-realism',
    'pollinations/gptimage',
    'pollinations/gptimage-large',
    'meta-llama/llama-3.2-11b-vision-instruct',
    'z-ai/glm-4.6v',
    'google/gemini-2.5-flash-image',
]

# Mapeamento de modelos obsoletos -> modelos validados
OBSOLETE_TO_VALID_TEXT = {
    'deepseek/deepseek-chat': 'qwen/qwen3-32b',
    'meta-llama/llama-3.1-70b-instruct': 'qwen/qwen3-32b',
    'google/gemini-flash-1.5': 'qwen/qwen3-32b',
    'openai/gpt-4o-mini': 'qwen/qwen3-32b',
    'anthropic/claude-3.5-sonnet': 'anthropic/claude-3-haiku',
    'anthropic/claude-sonnet-4': 'anthropic/claude-3.7-sonnet-thinking',
    'google/gemini-pro-1.5': 'openai/gpt-4o',
}

OBSOLETE_TO_VALID_IMAGE = {
    'openai/dall-e-3': 'pollinations/flux',
    'pollinations/turbo': 'pollinations/flux',
}

def migrate_projects():
    """Migra modelos de projetos."""
    print("\n🔄 Migrando modelos de PROJETOS...\n")
    
    # Migrar modelos de texto
    text_updated = 0
    for old_model, new_model in OBSOLETE_TO_VALID_TEXT.items():
        count = Project.objects.filter(text_model=old_model).update(text_model=new_model)
        if count > 0:
            print(f"  ✅ {count} projeto(s): '{old_model}' → '{new_model}'")
            text_updated += count
    
    # Migrar modelos de pesquisa (Perplexity)
    research_count = Project.objects.filter(
        research_model__contains='llama-3.1-sonar'
    ).update(research_model='perplexity/sonar')
    if research_count > 0:
        print(f"  ✅ {research_count} projeto(s): Perplexity Llama → Perplexity Sonar")
    
    # Migrar modelos de imagem
    image_updated = 0
    for old_model, new_model in OBSOLETE_TO_VALID_IMAGE.items():
        count = Project.objects.filter(image_model=old_model).update(image_model=new_model)
        if count > 0:
            print(f"  ✅ {count} projeto(s): '{old_model}' → '{new_model}'")
            image_updated += count
    
    print(f"\n✅ Total de projetos atualizados:")
    print(f"   - Texto: {text_updated}")
    print(f"   - Pesquisa: {research_count}")
    print(f"   - Imagem: {image_updated}")

def migrate_agencies():
    """Migra modelos padrão de agências."""
    print("\n🔄 Migrando modelos padrão de AGÊNCIAS...\n")
    
    # Migrar texto
    text_agencies = Agency.objects.exclude(default_text_model__in=VALID_TEXT_MODELS)
    text_count = text_agencies.count()
    if text_count > 0:
        text_agencies.update(default_text_model='qwen/qwen3-32b')
        print(f"  ✅ {text_count} agência(s): default_text_model → 'qwen/qwen3-32b'")
    
    # Migrar imagem
    image_agencies = Agency.objects.exclude(default_image_model__in=VALID_IMAGE_MODELS)
    image_count = image_agencies.count()
    if image_count > 0:
        image_agencies.update(default_image_model='pollinations/flux')
        print(f"  ✅ {image_count} agência(s): default_image_model → 'pollinations/flux'")
    
    print(f"\n✅ Total de agências atualizadas:")
    print(f"   - Texto: {text_count}")
    print(f"   - Imagem: {image_count}")

def verify_migration():
    """Verifica se ainda há modelos não validados."""
    print("\n🔍 Verificando modelos não validados...\n")
    
    # Projetos com modelos de texto inválidos
    invalid_text_projects = Project.objects.exclude(text_model__in=VALID_TEXT_MODELS)
    if invalid_text_projects.exists():
        print("⚠️  Projetos com modelos de TEXTO não validados:")
        for model in invalid_text_projects.values_list('text_model', flat=True).distinct():
            count = invalid_text_projects.filter(text_model=model).count()
            print(f"   - '{model}': {count} projeto(s)")
    else:
        print("✅ Todos os projetos usam modelos de texto validados")
    
    # Projetos com modelos de imagem inválidos
    invalid_image_projects = Project.objects.exclude(image_model__in=VALID_IMAGE_MODELS)
    if invalid_image_projects.exists():
        print("\n⚠️  Projetos com modelos de IMAGEM não validados:")
        for model in invalid_image_projects.values_list('image_model', flat=True).distinct():
            count = invalid_image_projects.filter(image_model=model).count()
            print(f"   - '{model}': {count} projeto(s)")
    else:
        print("✅ Todos os projetos usam modelos de imagem validados")
    
    # Agências
    invalid_text_agencies = Agency.objects.exclude(default_text_model__in=VALID_TEXT_MODELS)
    if invalid_text_agencies.exists():
        print(f"\n⚠️  {invalid_text_agencies.count()} agência(s) com default_text_model não validado")
    
    invalid_image_agencies = Agency.objects.exclude(default_image_model__in=VALID_IMAGE_MODELS)
    if invalid_image_agencies.exists():
        print(f"⚠️  {invalid_image_agencies.count()} agência(s) com default_image_model não validado")

def main():
    print("=" * 80)
    print("🚀 MIGRAÇÃO DE MODELOS OBSOLETOS PARA MODELOS VALIDADOS")
    print("=" * 80)
    
    # Contagem inicial
    total_projects = Project.objects.count()
    total_agencies = Agency.objects.count()
    print(f"\n📊 Base de dados:")
    print(f"   - Projetos: {total_projects}")
    print(f"   - Agências: {total_agencies}")
    
    # Executar migrações
    migrate_projects()
    migrate_agencies()
    
    # Verificar resultado
    verify_migration()
    
    print("\n" + "=" * 80)
    print("✅ MIGRAÇÃO CONCLUÍDA!")
    print("=" * 80)
    print("\n📝 Próximos passos:")
    print("   1. Reiniciar worker: docker restart postpro_worker")
    print("   2. Monitorar logs: docker logs -f postpro_worker")
    print("   3. Testar criação de novo post")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Migração cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERRO durante migração: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
