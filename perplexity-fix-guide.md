# 🚨 Correção Crítica - Modelo Perplexity Atualizado

## Problema Identificado
O modelo `perplexity/llama-3.1-sonar-large-128k-online` **não existe mais** no OpenRouter, causando erro 404 na geração de posts.

## Solu Aplicada
✅ Atualizado para `perplexity/sonar` (modelo atual disponível)
✅ Migration criada: `0004_alter_project_research_model.py`
✅ Código pushed para GitHub

## Próximos Passos

### 1. Aguardar CI/CD (2-3 minutos)
O GitHub Actions está fazendo build da nova imagem com a correção.

### 2. Atualizar Serviços em Produção

```bash
ssh root@157.230.32.101

# Atualizar Worker (CRÍTICO)
docker service update --image ghcr.io/moi-kalebbe/postpro:latest --force postpro_postpro_worker

# Atualizar Web
docker service update --image ghcr.io/moi-kalebbe/postpro:latest --force postpro_postpro_web

# Aguardar reinicialização
sleep 30
```

### 3. Atualizar Projeto no Banco de Dados

```bash
# Conectar ao PostgreSQL
docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db

# Atualizar o projeto existente
UPDATE projects 
SET research_model = 'perplexity/sonar' 
WHERE research_model LIKE '%llama-3.1-sonar%';

# Verificar
SELECT name, research_model FROM projects;

\q
```

### 4. Testar Novamente

Após a atualização, os posts devem ser gerados com sucesso!

## Comando Completo (Após CI/CD)

```bash
ssh root@157.230.32.101 << 'EOF'
echo "🔄 Atualizando PostPro..."
docker service update --image ghcr.io/moi-kalebbe/postpro:latest --force postpro_postpro_worker
docker service update --image ghcr.io/moi-kalebbe/postpro:latest --force postpro_postpro_web
sleep 30

echo "🗄️ Atualizando projeto no banco..."
docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db -c \
"UPDATE projects SET research_model = 'perplexity/sonar' WHERE research_model LIKE '%llama-3.1-sonar%';"

echo "✅ Atualização concluída!"
docker service logs --tail 20 postpro_postpro_worker
EOF
```

**Tudo pronto para funcionar! 🎉**
