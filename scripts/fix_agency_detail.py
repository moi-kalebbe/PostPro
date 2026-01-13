import os

FILE_PATH = os.path.join('templates', 'admin_panel', 'agency_detail.html')

CONTENT = """{% extends 'base.html' %}
{% load static %}

{% block title %}{{ agency.name }} - PostPro Admin{% endblock %}

{% block sidebar %}
{% include 'components/sidebar_admin.html' %}
{% endblock %}

{% block content %}
<div class="container">
    <div class="page-header">
        <div>
            <h1 class="page-title">{{ agency.name }}</h1>
            <p class="text-muted">{{ agency.slug }}</p>
        </div>
        <div class="flex gap-2">
            {% if agency.subscription_status == 'active' %}
            <form method="post" action="{% url 'admin_panel:agency_action' agency.id %}" onsubmit="return confirmAgencyAction(event, 'Suspender esta agência?', 'warning')">
                {% csrf_token %}
                <input type="hidden" name="action" value="suspend">
                <button type="submit" class="btn btn-secondary">
                    Suspender
                </button>
            </form>
            {% else %}
            <form method="post" action="{% url 'admin_panel:agency_action' agency.id %}">
                {% csrf_token %}
                <input type="hidden" name="action" value="activate">
                <button type="submit" class="btn btn-success">
                    Ativar
                </button>
            </form>
            {% endif %}
        </div>
    </div>

    <!-- Stats -->
    <div class="stats-grid mb-6">
        <div class="card">
            <div class="card-body stat-card">
                <span class="stat-label">Plano</span>
                <span class="stat-value text-sm">{{ agency.get_plan_display }}</span>
            </div>
        </div>
        <div class="card">
            <div class="card-body stat-card">
                <span class="stat-label">Status</span>
                <span
                    class="stat-value text-sm {% if agency.subscription_status == 'active' %}text-success{% else %}text-warning{% endif %}">
                    {{ agency.get_subscription_status_display }}
                </span>
            </div>
        </div>
        <div class="card">
            <div class="card-body stat-card">
                <span class="stat-label">Projetos</span>
                <span class="stat-value">{{ agency.projects_count }}</span>
            </div>
        </div>
        <div class="card">
            <div class="card-body stat-card">
                <span class="stat-label">Posts Este Mês</span>
                <span class="stat-value">{{ agency.current_month_posts }}</span>
            </div>
        </div>
    </div>

    <div class="grid-responsive-2">
        <!-- Agency Info -->
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">Informações</h3>
            </div>
            <div class="card-body">
                <div class="grid-responsive-2 gap-4">
                    <div>
                        <span class="text-sm text-muted">Limite de Projetos</span>
                        <div class="font-medium">{{ agency.max_projects }}</div>
                    </div>
                    <div>
                        <span class="text-sm text-muted">Limite Posts/Mês</span>
                        <div class="font-medium">{{ agency.monthly_posts_limit }}</div>
                    </div>
                    <div>
                        <span class="text-sm text-muted">Modelo de Texto</span>
                        <div class="font-medium">{{ agency.default_text_model }}</div>
                    </div>
                    <div>
                        <span class="text-sm text-muted">Modelo de Imagem</span>
                        <div class="font-medium">{{ agency.default_image_model }}</div>
                    </div>
                    <div>
                        <span class="text-sm text-muted">Criada em</span>
                        <div class="font-medium">{{ agency.created_at|date:"d/m/Y H:i" }}</div>
                    </div>
                    <div>
                        <span class="text-sm text-muted">API Key</span>
                        <div class="font-medium">{% if agency.openrouter_api_key_encrypted %}✓ Configurada{% else %}✗
                            Não configurada{% endif %}</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Quick Actions -->
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">Ações Rápidas</h3>
            </div>
            <div class="card-body">
                <div class="flex flex-col gap-2">
                    <!-- RESET MONTHLY POSTS -->
                    <form method="post" action="{% url 'admin_panel:agency_action' agency.id %}" onsubmit="return confirmAgencyAction(event, 'Resetar contador de posts deste mês?', 'warning', 'Resetar')">
                        {% csrf_token %}
                        <input type="hidden" name="action" value="reset_posts">
                        <button type="submit" class="btn btn-secondary" style="width: 100%;">
                            Resetar Posts do Mês
                        </button>
                    </form>

                    <!-- RESEND CREDENTIALS -->
                    <form method="post" action="{% url 'admin_panel:agency_action' agency.id %}" onsubmit="return confirmAgencyAction(event, 'Isso irá gerar uma NOVA SENHA e enviar ao cliente pelo WhatsApp. Continuar?', 'info', 'Enviar Credenciais')">
                        {% csrf_token %}
                        <input type="hidden" name="action" value="resend_credentials">
                        <button type="submit" class="btn btn-outline-info" style="width: 100%;">
                            Reenviar Acesso (WhatsApp)
                        </button>
                    </form>

                    <!-- EDIT -->
                    <a href="/django-admin/agencies/agency/{{ agency.id }}/change/" class="btn btn-ghost"
                        style="width: 100%;">
                        Editar no Django Admin
                    </a>

                    <!-- DELETE (DANGER ZONE) -->
                    <div style="margin-top: 1rem; border-top: 1px solid #fee2e2; padding-top: 1rem;">
                        <form method="post" action="{% url 'admin_panel:agency_action' agency.id %}" onsubmit="return confirmAgencyAction(event, 'ATENÇÃO: Isso excluirá permanentemente a agência, seus projetos e usuários. Esta ação não pode ser desfeita.', 'danger', 'EXCLUIR AGÊNCIA')">
                            {% csrf_token %}
                            <input type="hidden" name="action" value="delete">
                            <button type="submit" class="btn btn-error" style="width: 100%;">
                                Excluir Agência
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Members -->
    <div class="card mt-6">
        <div class="card-header">
            <h3 class="card-title">Membros</h3>
        </div>
        <div class="table-container">
            <table class="table">
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Data</th>
                    </tr>
                </thead>
                <tbody>
                    {% for member in members %}
                    <tr>
                        <td><strong>{{ member.first_name }} {{ member.last_name }}</strong></td>
                        <td>{{ member.email }}</td>
                        <td>
                            <span class="badge badge-gray">{{ member.get_role_display }}</span>
                        </td>
                        <td class="text-muted">{{ member.date_joined|date:"d/m/Y" }}</td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="4" class="text-center text-muted p-6">Nenhum membro</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Projects -->
    <div class="card mt-6">
        <div class="card-header">
            <h3 class="card-title">Projetos</h3>
        </div>
        <div class="table-container">
            <table class="table">
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>URL</th>
                        <th>Posts</th>
                        <th>Status</th>
                        <th>Criado em</th>
                    </tr>
                </thead>
                <tbody>
                    {% for project in projects %}
                    <tr>
                        <td><strong>{{ project.name }}</strong></td>
                        <td class="text-muted">{{ project.wordpress_url|truncatechars:30 }}</td>
                        <td>{{ project.total_posts_generated }}</td>
                        <td>
                            {% if project.is_active %}
                            <span class="badge badge-success">Ativo</span>
                            {% else %}
                            <span class="badge badge-gray">Inativo</span>
                            {% endif %}
                        </td>
                        <td class="text-muted">{{ project.created_at|date:"d/m/Y" }}</td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="5" class="text-center text-muted p-6">Nenhum projeto</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Activity Logs -->
    <div class="card mt-6">
        <div class="card-header">
            <h3 class="card-title">Atividades Recentes</h3>
        </div>
        <div class="table-container">
            <table class="table">
                <thead>
                    <tr>
                        <th>Ação</th>
                        <th>Usuário</th>
                        <th>Entidade</th>
                        <th>Data</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in activity_logs %}
                    <tr>
                        <td><strong>{{ log.action }}</strong></td>
                        <td>{{ log.actor_user.email|default:'-' }}</td>
                        <td>{{ log.entity_type }}</td>
                        <td class="text-muted">{{ log.created_at|date:"d/m H:i" }}</td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="4" class="text-center text-muted p-6">Nenhuma atividade</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
    async function confirmAgencyAction(event, message, type = 'warning', confirmBtnText = 'Confirmar') {
        event.preventDefault();
        const form = event.target;
        
        const confirmed = await window.confirmAction({
            title: 'Confirmação Necessária',
            message: message,
            type: type,
            confirmText: confirmBtnText,
            confirmClass: type === 'danger' ? 'btn-error' : (type === 'info' ? 'btn-primary' : 'btn-warning')
        });

        if (confirmed) {
            form.submit();
        }
        return false;
    }
</script>
{% endblock %}
"""

def fix_file():
    print(f"📄 Reescrevendo {FILE_PATH} com versão migrada para Design System...")
    try:
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(CONTENT)
        print("✅ Arquivo reescrito com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao escrever arquivo: {e}")
        return False

if __name__ == "__main__":
    fix_file()
