# 🚀 Aplicar Migrations em Produção

## Situação Atual
Uma migration pendente foi detectada no worker: `0004_alter_editorialplan_status.py`

Esta migration precisa ser aplicada para garantir que o campo `status` do `EditorialPlan` tenha todas as opções corretas.

## 📋 Passos para Aplicar

### 1. Aguardar CI/CD Build
Após o push para `main`, o GitHub Actions irá:
- ✅ Fazer build da nova imagem Docker
- ✅ Publicar em `ghcr.io/moi-kalebbe/postpro:latest`

**Tempo estimado**: ~2-3 minutos

### 2. Atualizar Worker em Produção

```bash
ssh root@157.230.32.101

# Atualizar a imagem do worker (força pull da nova versão)
docker service update --image ghcr.io/moi-kalebbe/postpro:latest --force postpro_postpro_worker

# Verificar se está atualizando
docker service ps postpro_postpro_worker

# Aguardar o worker reiniciar (30-60 segundos)
```

### 3. Verificar Logs Após Atualização

```bash
# Ver logs recentes do worker
docker service logs --tail 50 postpro_postpro_worker

# Você deve ver:
# ✅ "Operations to perform: Apply all migrations..."
# ✅ "Running migrations: Applying automation.0004_alter_editorialplan_status... OK"
# ✅ Sem mais avisos sobre migrations pendentes
```

### 4. Atualizar Web/API (Opcional mas Recomendado)

```bash
# Atualizar também o serviço web
docker service update --image ghcr.io/moi-kalebbe/postpro:latest --force postpro_postpro_web

# Verificar
docker service ps postpro_postpro_web
```

## 🔍 Monitoramento Durante Atualização

```bash
# Terminal 1: Ver logs do worker
docker service logs -f postpro_postpro_worker

# Terminal 2: Ver status
watch -n 2 'docker service ps postpro_postpro_worker'
```

## ⚡ Comando Rápido (Após CI/CD Completar)

```bash
ssh root@157.230.32.101 << 'EOF'
echo "🔄 Atualizando PostPro Worker..."
docker service update --image ghcr.io/moi-kalebbe/postpro:latest --force postpro_postpro_worker
echo "🌐 Atualizando PostPro Web..."
docker service update --image ghcr.io/moi-kalebbe/postpro:latest --force postpro_postpro_web
echo "✅ Serviços atualizados! Aguardando reinicialização..."
sleep 30
echo "📊 Status dos serviços:"
docker service ls | grep postpro
echo ""
echo "📝 Últimas linhas do log do worker:"
docker service logs --tail 20 postpro_postpro_worker
EOF
```

## ✅ Verificação Final

Após a atualização, confirme que:
- [ ] Worker reiniciou sem erros
- [ ] Não há mais warnings sobre migrations pendentes
- [ ] Tarefas continuam sendo processadas normalmente

**Pronto! 🎉**
