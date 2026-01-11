-- ============================================================================
-- Script SQL para Migração de Modelos Obsoletos para Modelos Validados
-- Data: 2026-01-11
-- Objetivo: Atualizar projetos e agências existentes que usam modelos obsoletos
-- ============================================================================

-- ============================================================================
-- BACKUP PRIMEIRO! Execute antes de aplicar este script:
-- pg_dump -U postgres -d postpro > backup_antes_migracao_$(date +%Y%m%d_%H%M%S).sql
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. ATUALIZAR PROJETOS - Modelos de Texto
-- ============================================================================

-- Substituir modelos obsoletos por Qwen3 32B (melhor custo-benefício)
UPDATE projects_project 
SET text_model = 'qwen/qwen3-32b' 
WHERE text_model IN (
    'deepseek/deepseek-chat',               -- Obsoleto
    'meta-llama/llama-3.1-70b-instruct',    -- Obsoleto
    'google/gemini-flash-1.5',              -- Obsoleto
    'openai/gpt-4o-mini',                   -- Obsoleto
    'anthropic/claude-3.5-sonnet',          -- Não validado
    'anthropic/claude-sonnet-4',            -- Não validado
    'google/gemini-pro-1.5'                 -- Obsoleto
);

-- Registrar no log quantos foram atualizados
-- SELECT COUNT(*) AS projetos_texto_atualizados FROM projects_project WHERE text_model = 'qwen/qwen3-32b';

-- ============================================================================
-- 2. ATUALIZAR PROJETOS - Modelos de Pesquisa (Research)
-- ============================================================================

-- Substituir Perplexity Llama antigo por Perplexity Sonar
UPDATE projects_project 
SET research_model = 'perplexity/sonar' 
WHERE research_model LIKE '%llama-3.1-sonar%';

-- ============================================================================
-- 3. ATUALIZAR PROJETOS - Modelos de Imagem
-- ============================================================================

-- Substituir DALL-E 3 por Pollinations Flux (gratuito, melhor custo-benefício)
UPDATE projects_project 
SET image_model = 'pollinations/flux' 
WHERE image_model IN (
    'openai/dall-e-3',
    'pollinations/turbo'  -- Atualizar para Flux (melhor qualidade)
);

-- ============================================================================
-- 4. ATUALIZAR AGÊNCIAS - Default Text Model
-- ============================================================================

UPDATE agencies_agency 
SET default_text_model = 'qwen/qwen3-32b' 
WHERE default_text_model NOT IN (
    -- Lista de modelos VALIDADOS (manter se já estiver usando)
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
    'mistralai/codestral-2508'
);

-- ============================================================================
-- 5. ATUALIZAR AGÊNCIAS - Default Image Model
-- ============================================================================

UPDATE agencies_agency 
SET default_image_model = 'pollinations/flux' 
WHERE default_image_model NOT IN (
    -- Lista de modelos de imagem VALIDADOS
    'pollinations/flux',
    'pollinations/turbo',
    'pollinations/flux-realism',
    'pollinations/gptimage',
    'pollinations/gptimage-large',
    'meta-llama/llama-3.2-11b-vision-instruct',
    'z-ai/glm-4.6v',
    'google/gemini-2.5-flash-image'
);

-- ============================================================================
-- 6. VERIFICAÇÃO FINAL - Contar registros atualizados
-- ============================================================================

SELECT 
    'Projetos com texto atualizado' AS categoria,
    COUNT(*) AS total
FROM projects_project 
WHERE text_model = 'qwen/qwen3-32b'

UNION ALL

SELECT 
    'Projetos com imagem atualizada',
    COUNT(*)
FROM projects_project 
WHERE image_model = 'pollinations/flux'

UNION ALL

SELECT 
    'Agências com texto padrão atualizado',
    COUNT(*)
FROM agencies_agency 
WHERE default_text_model = 'qwen/qwen3-32b'

UNION ALL

SELECT 
    'Agências com imagem padrão atualizada',
    COUNT(*)
FROM agencies_agency 
WHERE default_image_model = 'pollinations/flux';

-- ============================================================================
-- 7. LISTAR QUALQUER MODELO QUE AINDA NÃO ESTEJA VALIDADO
-- ============================================================================

-- Projetos com modelos de texto não validados
SELECT DISTINCT text_model, COUNT(*) AS quantidade
FROM projects_project 
WHERE text_model NOT IN (
    '', 'qwen/qwen3-32b', 'deepseek/deepseek-v3', 'mistralai/mistral-small-3',
    'meta-llama/llama-4-scout', 'anthropic/claude-3-haiku', 'openai/gpt-4o',
    'qwen/qwen3-coder-480b-a35b', 'anthropic/claude-3.7-sonnet-thinking',
    'openai/gpt-5-chat', 'openai/gpt-5.2-pro', 'mistralai/mistral-large-3-2512',
    'mistralai/codestral-2508'
)
GROUP BY text_model;

COMMIT;

-- ============================================================================
-- NOTAS PÓS-MIGRAÇÃO:
-- ============================================================================
-- 1. Reiniciar o worker: docker restart postpro_worker
-- 2. Monitorar logs por 24h: docker logs -f postpro_worker
-- 3. Verificar custos no OpenRouter dashboard
-- 4. Se houver erros 404, verificar este script e ajustar manualmente
-- ============================================================================
