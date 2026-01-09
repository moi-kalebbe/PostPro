# PostPro - Multi-tenant B2B2C SaaS para Automação de Conteúdo WordPress

Sistema completo para automação de criação de conteúdo usando IA com integração WordPress.

## 🚀 Features

- **Multi-tenant**: Suporte a múltiplas agências com isolamento de dados
- **AI Content Pipeline**: Pesquisa → Estratégia SEO → Redação → Imagem
- **BYOK (Bring Your Own Key)**: Agências usam suas próprias API keys do OpenRouter
- **Reprocessamento**: Regenere qualquer etapa do pipeline individualmente
- **Idempotência**: Prevenção de duplicatas em todas as operações
- **Dry-Run**: Simule custos antes de processar
- **WordPress Plugin**: Integração completa via webhook

## 📋 Requisitos

- Python 3.11+
- PostgreSQL (Supabase)
- Redis
- Node.js (para assets, opcional)

## 🛠️ Instalação Local

### 1. Clone o repositório

```bash
git clone https://github.com/your-org/postpro.git
cd postpro
```

### 2. Crie o ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com suas credenciais
```

**Variáveis obrigatórias:**
- `SECRET_KEY`: Chave secreta Django
- `DATABASE_URL`: URL do PostgreSQL (Supabase)
- `REDIS_URL`: URL do Redis
- `ENCRYPTION_KEY`: Chave Fernet para criptografia

### 5. Execute as migrações

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Execute o servidor

```bash
# Terminal 1 - Django
python manage.py runserver

# Terminal 2 - Celery Worker
celery -A config worker -l info

# Terminal 3 - Celery Beat (opcional)
celery -A config beat -l info
```

## 🔧 Configuração

### Supabase

1. Crie um projeto no Supabase
2. Copie a URL e as chaves para o `.env`
3. Crie o bucket `post-images` no Storage
4. Configure políticas de acesso público para imagens

### OpenRouter

1. Crie uma conta em [openrouter.ai](https://openrouter.ai)
2. Gere uma API key
3. Configure no painel da agência

### WordPress Plugin

1. Baixe o plugin ZIP em `/downloads/postpro-plugin.zip`
2. Instale no WordPress
3. Configure a License Key do projeto

## 📦 Estrutura do Projeto

```
postpro/
├── apps/
│   ├── accounts/       # Usuários e autenticação
│   ├── agencies/       # Agências (tenants)
│   ├── projects/       # Projetos WordPress
│   ├── automation/     # Posts, Batches, Artifacts
│   ├── ai_engine/      # Agentes de IA
│   └── webhooks/       # API endpoints
├── config/            # Configurações Django
├── services/          # Serviços externos
├── templates/         # Templates HTML
├── static/            # CSS, JS, assets
└── wordpress-plugin/  # Plugin WordPress
```

## 🔐 Segurança

- ✅ Fernet encryption para API keys e senhas
- ✅ Multi-tenancy com isolamento completo
- ✅ RBAC (super_admin, agency_owner, agency_member)
- ✅ CSRF protection em todas as views
- ✅ Rate limiting via middleware
- ✅ Idempotência para prevenção de duplicatas
- ✅ Audit logging de ações importantes

## 📊 API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/validate-license` | GET | Validar license key |
| `/api/v1/batch-upload` | POST | Upload de CSV |
| `/api/v1/batch/<id>/status` | GET | Status do batch |
| `/api/v1/posts/<id>` | GET | Detalhes do post |
| `/api/v1/posts/<id>/publish` | POST | Publicar post |
| `/api/v1/posts/<id>/regenerate` | POST | Regenerar etapa |

**Headers obrigatórios:**
- `X-License-Key`: License key do projeto

## 🚀 Deploy (Render.com)

1. Conecte o repositório ao Render
2. Configure as variáveis de ambiente
3. Deploy automático via `render.yaml`

```bash
# Ou via CLI
render deploy
```

## 📝 Licença

MIT License - veja [LICENSE](LICENSE)

## 🤝 Suporte

- Documentação: [docs.postpro.app](https://docs.postpro.app)
- Email: suporte@postpro.app


