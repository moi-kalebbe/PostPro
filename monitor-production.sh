#!/bin/bash

# 🎯 PostPro - Script de Monitoramento de Produção
# Execute este script para monitorar os logs em tempo real

echo "🚀 PostPro - Iniciando monitoramento de logs..."
echo ""
echo "Escolha uma opção:"
echo ""
echo "1) Ver logs do Worker (criação de posts)"
echo "2) Ver logs da Web (API/Backend)"
echo "3) Ver logs do Redis"
echo "4) Ver logs do PostgreSQL"
echo "5) Ver status de todos os serviços"
echo "6) Reiniciar Worker"
echo "7) Ver últimos 5 posts criados"
echo "8) Ver batch jobs pendentes"
echo "9) Monitoramento completo (múltiplas janelas)"
echo "0) Sair"
echo ""
read -p "Digite a opção: " option

case $option in
  1)
    echo "📊 Monitorando Worker..."
    docker service logs -f --timestamps postpro_postpro_worker
    ;;
  2)
    echo "🌐 Monitorando Web..."
    docker service logs -f --timestamps postpro_postpro_web
    ;;
  3)
    echo "🔴 Monitorando Redis..."
    docker service logs -f --timestamps postpro_postpro_redis
    ;;
  4)
    echo "🗄️ Monitorando PostgreSQL..."
    docker service logs -f --timestamps postpro_postpro_db
    ;;
  5)
    echo "📋 Status dos Serviços PostPro:"
    docker service ls | grep postpro
    echo ""
    echo "Worker:"
    docker service ps postpro_postpro_worker
    echo ""
    echo "Web:"
    docker service ps postpro_postpro_web
    ;;
  6)
    echo "🔄 Reiniciando Worker..."
    docker service update --force postpro_postpro_worker
    echo "✅ Worker reiniciado!"
    ;;
  7)
    echo "📝 Últimos 5 posts criados:"
    docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db -c \
    "SELECT title, status, wordpress_post_id, created_at FROM posts ORDER BY created_at DESC LIMIT 5;"
    ;;
  8)
    echo "⏳ Batch jobs pendentes:"
    docker exec -it $(docker ps -q -f name=postpro_db) psql -U postgres -d postpro_db -c \
    "SELECT id, status, processed_count, total_keywords, created_at FROM batch_jobs WHERE status IN ('pending', 'processing') ORDER BY created_at DESC;"
    ;;
  9)
    echo "🖥️ Para monitoramento completo, abra 3 terminais e execute:"
    echo ""
    echo "Terminal 1:"
    echo "  docker service logs -f postpro_postpro_worker"
    echo ""
    echo "Terminal 2:"
    echo "  docker service logs -f postpro_postpro_web"
    echo ""
    echo "Terminal 3:"
    echo "  watch -n 5 'docker service ls | grep postpro'"
    ;;
  0)
    echo "👋 Até logo!"
    exit 0
    ;;
  *)
    echo "❌ Opção inválida!"
    exit 1
    ;;
esac
