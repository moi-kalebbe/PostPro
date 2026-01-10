# 🧹 Script de Limpeza do Banco de Dados PostPro

## ⚠️ ATENÇÃO: Use com cuidado! Isso apagará dados permanentemente.

## 🎯 Limpar TODOS os posts

```bash
ssh root@157.230.32.101

docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db << 'EOF'
-- Limpar posts
DELETE FROM posts;

-- Limpar artifacts dos posts
DELETE FROM post_artifacts;

-- Limpar batch jobs
DELETE FROM batch_jobs;

-- Limpar idempotency keys
DELETE FROM idempotency_keys;

-- Verificar limpeza
SELECT 
  (SELECT COUNT(*) FROM posts) as posts,
  (SELECT COUNT(*) FROM post_artifacts) as artifacts,
  (SELECT COUNT(*) FROM batch_jobs) as batches,
  (SELECT COUNT(*) FROM idempotency_keys) as keys;
EOF
```

## 🎯 Limpar posts de um projeto específico

```bash
ssh root@157.230.32.101

# Primeiro, descubra o ID do projeto
docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db -c \
"SELECT id, site_name, wordpress_url FROM projects ORDER BY created_at DESC;"

# Copie o ID do projeto e substitua em <PROJECT_ID> abaixo
docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db << 'EOF'
-- Substitua <PROJECT_ID> pelo ID real
DELETE FROM posts WHERE project_id = '<PROJECT_ID>';
DELETE FROM batch_jobs WHERE project_id = '<PROJECT_ID>';
EOF
```

## 🎯 Limpar apenas posts de um batch específico

```bash
ssh root@157.230.32.101

# Primeiro, veja os batch jobs
docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db -c \
"SELECT id, status, total_keywords, processed_count, created_at FROM batch_jobs ORDER BY created_at DESC LIMIT 10;"

# Copie o ID do batch e substitua em <BATCH_ID> abaixo
docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db -c \
"DELETE FROM posts WHERE batch_job_id = '<BATCH_ID>';"
```

## 🎯 Limpar posts com status específico

```bash
ssh root@157.230.32.101

# Limpar apenas posts com falha (failed)
docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db -c \
"DELETE FROM posts WHERE status = 'failed';"

# Limpar posts pendentes de revisão
docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db -c \
"DELETE FROM posts WHERE status = 'pending_review';"

# Limpar posts em geração
docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db -c \
"DELETE FROM posts WHERE status = 'generating';"
```

## 🎯 Limpar projeto completo (WordPress desconectado)

```bash
ssh root@157.230.32.101

docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db << 'EOF'
-- Substitua <PROJECT_ID> pelo ID real
BEGIN;

DELETE FROM posts WHERE project_id = '<PROJECT_ID>';
DELETE FROM batch_jobs WHERE project_id = '<PROJECT_ID>';
DELETE FROM project_content_settings WHERE project_id = '<PROJECT_ID>';
DELETE FROM activity_logs WHERE project_id = '<PROJECT_ID>';
DELETE FROM projects WHERE id = '<PROJECT_ID>';

COMMIT;
EOF
```

## 📊 Verificar contagens atuais

```bash
ssh root@157.230.32.101

docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db << 'EOF'
SELECT 
  'Posts' as tabela,
  status,
  COUNT(*) as quantidade
FROM posts
GROUP BY status
UNION ALL
SELECT 
  'Batch Jobs' as tabela,
  status,
  COUNT(*) as quantidade
FROM batch_jobs
GROUP BY status
ORDER BY tabela, status;
EOF
```

## 🔄 Reset completo (CUIDADO!)

```bash
ssh root@157.230.32.101

docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db << 'EOF'
-- ATENÇÃO: Isso apaga TUDO exceto usuários e agências!
BEGIN;

DELETE FROM activity_logs;
DELETE FROM idempotency_keys;
DELETE FROM post_artifacts;
DELETE FROM posts;
DELETE FROM batch_jobs;
DELETE FROM project_content_settings;
DELETE FROM projects;

COMMIT;

-- Verificar
SELECT 
  (SELECT COUNT(*) FROM projects) as projetos,
  (SELECT COUNT(*) FROM posts) as posts,
  (SELECT COUNT(*) FROM batch_jobs) as batches;
EOF
```
