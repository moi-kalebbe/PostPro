# 🔧 Correção Completa - Modelos AI Inválidos

## Problema
Worker ` está usando `deepseek/deepseek-v3` que não existe no OpenRouter.

## Causa
A **agência** no banco de dados tem `default_text_model = 'deepseek/deepseek-v3'`.

## Solução Rápida

```bash
ssh root@157.230.32.101

# No banco PostgreSQL
docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db << 'SQL'

-- Verificar modelo atual
SELECT id, name, default_text_model FROM agencies;

-- Atualizar para deepseek-chat
UPDATE agencies 
SET default_text_model = 'deepseek/deepseek-chat' 
WHERE default_text_model LIKE '%deepseek-v3%';

-- Verificar atualização
SELECT id, name, default_text_model FROM agencies;

\q
SQL

# Limpar fila Redis para forçar novas tasks
docker exec -it $(docker ps -q -f name=postpro_redis) redis-cli FLUSHDB

# Ver logs
docker service logs --tail 30 -f postpro_postpro_worker
```

## Resultado Esperado
✅ `default_text_model` atualizado para `deepseek/deepseek-chat`  
✅ Novos posts gerados sem erro 400  
✅ Pipeline completo funcionando

## Próximo Teste
Criar novo plano editorial no WordPress e verificar que os posts são gerados com sucesso! 🚀
