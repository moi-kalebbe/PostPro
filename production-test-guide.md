# 🧪 Guia de Teste em Produção - PostPro

## 📋 Status do Banco de Dados

**✅ Verificado**: Não há posts do blog "dicas beach tennis" no sistema.
**✅ Pronto para teste**: Banco de dados limpo e preparado.

---

## 🔌 Comandos SSH para Monitoramento

### 1. Conectar ao Servidor

```bash
ssh root@157.230.32.101
```

### 2. Monitorar Logs do Worker (Criação de Posts)

```bash
# Ver logs em tempo real do worker
docker service logs -f postpro_postpro_worker

# Ver últimas 100 linhas
docker service logs --tail 100 postpro_postpro_worker

# Ver logs com timestamp
docker service logs -f --timestamps postpro_postpro_worker

# Filtrar apenas erros
docker service logs -f postpro_postpro_worker 2>&1 | grep -i error
```

### 3. Monitorar Logs da Web/API (Backend)

```bash
# Ver logs em tempo real da web
docker service logs -f postpro_postpro_web

# Ver últimas 100 linhas
docker service logs --tail 100 postpro_postpro_web

# Ver logs com timestamp
docker service logs -f --timestamps postpro_postpro_web
```

### 4. Verificar Status dos Serviços

```bash
# Ver status de todos os serviços PostPro
docker service ls | grep postpro

# Ver detalhes do worker
docker service ps postpro_postpro_worker

# Ver detalhes da web
docker service ps postpro_postpro_web

# Ver detalhes do Redis
docker service ps postpro_postpro_redis

# Ver detalhes do DB
docker service ps postpro_postpro_db
```

### 5. Monitorar Banco de Dados PostgreSQL

```bash
# Conectar ao PostgreSQL
docker exec -it $(docker ps -q -f name=postpro_db) psql -U postpro -d postpro

# Dentro do PostgreSQL, verificar posts em tempo real:
SELECT id, title, status, created_at 
FROM posts 
ORDER BY created_at DESC 
LIMIT 10;

# Verificar batch jobs:
SELECT id, status, total_keywords, processed_count, created_at 
FROM batch_jobs 
ORDER BY created_at DESC 
LIMIT 5;

# Sair do PostgreSQL
\q
```

---

## 🎯 Passo a Passo do Teste

### Preparação (Antes de Instalar o Plugin)

1. **Verificar serviços rodando:**
   ```bash
   ssh root@157.230.32.101
   docker service ls
   ```

2. **Iniciar monitoramento em múltiplas janelas do terminal:**
   - **Terminal 1**: `docker service logs -f postpro_worker`
   - **Terminal 2**: `docker service logs -f postpro_api`
   - **Terminal 3**: Manter aberto para comandos ad-hoc

### Durante a Instalação do Plugin

3. **No WordPress:**
   - Instalar o plugin PostPro
   - Ativar o plugin
   - Ir para configurações do plugin

4. **Configurar o plugin:**
   - **API URL**: `https://postpro.nuvemchat.com`
   - **License Key**: _(copiar da dashboard do PostPro)_

5. **Nos terminais SSH, observe:**
   - Requisições de sincronização do site
   - Autenticação da chave de licença
   - Criação do projeto no banco

### Durante o Teste de Criação de Posts

6. **No WordPress:**
   - Adicionar keywords do nicho "Beach Tennis" (5-10 palavras)
   - Ou fazer upload de CSV com keywords
   - Clicar em "Gerar Plano Editorial"

7. **Nos logs do Worker, você verá:**
   ```bash
   # Terminal com: docker service logs -f postpro_postpro_worker
   
   [INFO] Starting batch job: <batch-id>
   [INFO] Processing keyword 1/X: "como jogar beach tennis"
   [INFO] ResearchAgent: Starting research...
   [INFO] StrategyAgent: Creating content strategy...
   [INFO] ArticleAgent: Writing article...
   [INFO] ImageAgent: Generating featured image...
   [INFO] Post created successfully: <post-id>
   [INFO] Publishing to WordPress...
   [INFO] Post published: <wordpress-post-id>
   ```

8. **Comandos úteis durante o teste:**
   ```bash
   # Ver quantos posts foram criados
   docker exec -it $(docker ps -q -f name=postpro_db) psql -U postpro -d postpro -c \
   "SELECT COUNT(*) FROM posts WHERE status='published';"
   
   # Ver últimos 5 posts criados
   docker exec -it $(docker ps -q -f name=postpro_db) psql -U postpro -d postpro -c \
   "SELECT title, status, wordpress_post_id, created_at FROM posts ORDER BY created_at DESC LIMIT 5;"
   
   # Ver status do batch job
   docker exec -it $(docker ps -q -f name=postpro_db) psql -U postpro -d postpro -c \
   "SELECT id, status, processed_count, total_keywords, error_message FROM batch_jobs ORDER BY created_at DESC LIMIT 1;"
   ```

---

## 🐛 Troubleshooting

### Se os posts não estiverem sendo criados:

1. **Verificar se o worker está rodando:**
   ```bash
   docker service ps postpro_postpro_worker
   ```

2. **Reiniciar o worker se necessário:**
   ```bash
   docker service update --force postpro_postpro_worker
   ```

3. **Verificar variáveis de ambiente:**
   ```bash
   docker service inspect postpro_postpro_worker --pretty
   ```

4. **Verificar logs do Redis:**
   ```bash
   docker service logs -f postpro_postpro_redis
   ```

### Se houver erros de autenticação:

1. **Verificar chave de licença no banco:**
   ```bash
   docker exec -it $(docker ps -q -f name=postpro_db) psql -U postpro -d postpro -c \
   "SELECT id, site_name, license_key FROM projects ORDER BY created_at DESC LIMIT 1;"
   ```

2. **Regenerar chave de licença se necessário** (via dashboard Django)

### Se precisar limpar tudo e recomeçar:

```bash
# Conectar ao PostgreSQL
docker exec -it $(docker ps -q -f name=postpro_db) psql -U postpro -d postpro

# Limpar posts
DELETE FROM posts;

# Limpar batch jobs
DELETE FROM batch_jobs;

# Limpar projeto específico (substitua <project-id>)
DELETE FROM projects WHERE id='<project-id>';

\q
```

---

## 📊 Métricas a Observar

Durante o teste, monitore:

- ✅ **Tempo de geração**: Cada post leva ~2-3 minutos
- ✅ **Taxa de sucesso**: Posts criados vs. erros
- ✅ **Custos**: Verificar na dashboard "Uso & Custos"
- ✅ **Qualidade**: Revisar posts no WordPress
- ✅ **Imagens**: Verificar se imagens foram geradas
- ✅ **SEO**: Verificar meta description, title, etc.

---

## 🎉 Checklist de Validação

- [ ] Worker recebeu o batch job
- [ ] ResearchAgent executou pesquisa
- [ ] StrategyAgent criou estratégia de conteúdo
- [ ] ArticleAgent gerou o artigo completo
- [ ] ImageAgent criou a imagem destacada
- [ ] Post foi publicado no WordPress
- [ ] Imagem aparece corretamente no WordPress
- [ ] Meta tags SEO estão corretas
- [ ] Custos foram registrados na dashboard
- [ ] ActivityLog registrou todas as ações

---

## 📞 Próximos Passos

Depois do teste bem-sucedido:

1. ✅ Validar qualidade do conteúdo
2. ✅ Ajustar configurações de tom/estilo se necessário
3. ✅ Testar outros nichos
4. ✅ Escalar para múltiplos posts em batch
5. ✅ Monitorar custos e performance

**Tudo pronto para o teste! 🚀**
