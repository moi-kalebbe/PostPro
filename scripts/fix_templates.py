
import os

# 1. Fix leads.html with Design System classes AND Sidebar
leads_path = r'c:\Users\olx\OneDrive\Desktop\PROJETOS 2026\PostPro\templates\agencies\landing\leads.html'

leads_content = """{% extends 'base.html' %}
{% load static %}

{% block title %}Leads - {{ request.user.agency.get_display_name }}{% endblock %}

{% block sidebar %}
{% include 'components/sidebar.html' %}
{% endblock %}

{% block content %}
<div class="container">
    <div class="page-header">
        <div class="page-header-content">
            <h1>Leads Capturados</h1>
            <p class="page-subtitle">{{ stats.total }} leads no total</p>
        </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid-responsive-3 mb-6">
        <div class="stat-card">
            <div class="stat-value">{{ stats.new }}</div>
            <div class="stat-label">Novos</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ stats.contacted }}</div>
            <div class="stat-label">Contatados</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ stats.converted }}</div>
            <div class="stat-label">Convertidos</div>
        </div>
    </div>

    <!-- Filter -->
    <div class="filter-bar mb-6">
        <div class="form-group mb-0">
            <label class="form-label">Filtrar por status:</label>
            <select id="status-filter" class="form-select" onchange="filterLeads(this.value)">
                <option value="">Todos</option>
                {% for value, label in status_choices %}
                <option value="{{ value }}" {% if status_filter == value %}selected{% endif %}>{{ label }}</option>
                {% endfor %}
            </select>
        </div>
    </div>

    <!-- Leads Table -->
    <div class="card">
        <div class="table-wrapper">
            <table class="table">
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>Email</th>
                        <th>Telefone</th>
                        <th>Plano</th>
                        <th>Status</th>
                        <th>Data</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    {% for lead in leads %}
                    <tr data-lead-id="{{ lead.id }}">
                        <td>
                            <strong>{{ lead.name }}</strong>
                            {% if lead.company_name %}
                            <br><small class="text-muted">{{ lead.company_name }}</small>
                            {% endif %}
                        </td>
                        <td>
                            <a href="mailto:{{ lead.email }}">{{ lead.email }}</a>
                        </td>
                        <td>
                            {% if lead.phone %}
                            <a href="https://wa.me/{{ lead.phone }}" target="_blank" class="text-success">
                                {{ lead.phone }}
                            </a>
                            {% else %}
                            <span class="text-muted">-</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if lead.plan %}
                            <span class="badge badge-info">{{ lead.plan.name }}</span>
                            {% else %}
                            <span class="text-muted">Não selecionado</span>
                            {% endif %}
                        </td>
                        <td>
                            <select class="form-select text-sm p-1" data-lead-id="{{ lead.id }}"
                                style="height: auto; width: auto;"
                                onchange="updateLeadStatus('{{ lead.id }}', this.value)">
                                {% for value, label in status_choices %}
                                <option value="{{ value }}" {% if lead.status == value %}selected{% endif %}>{{ label }}</option>
                                {% endfor %}
                            </select>
                        </td>
                        <td>
                            <span title="{{ lead.created_at|date:'d/m/Y H:i' }}">
                                {{ lead.created_at|date:"d/m/Y" }}
                            </span>
                        </td>
                        <td>
                            <button type="button" class="btn btn-secondary btn-sm"
                                onclick="showLeadDetails('{{ lead.id }}')">
                                <i class="icon-eye"></i>
                            </button>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="7" class="text-center text-muted p-6">
                            Nenhum lead capturado ainda.
                            {% if not request.user.agency.landing_page.is_published %}
                            <br><a href="{% url 'dashboard:landing_config' %}">Publique sua landing page</a> para começar a
                            capturar leads.
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Lead Details Modal -->
<div id="lead-modal" class="modal-backdrop">
    <div class="modal">
        <div class="modal-header">
            <h3 class="modal-title">Detalhes do Lead</h3>
            <button type="button" class="modal-close" onclick="closeLeadModal()">&times;</button>
        </div>
        <div class="modal-body" id="lead-modal-body">
            <!-- Content loaded dynamically -->
        </div>
    </div>
</div>

<script>
    function filterLeads(status) {
        const url = new URL(window.location.href);
        if (status) {
            url.searchParams.set('status', status);
        } else {
            url.searchParams.delete('status');
        }
        window.location.href = url.toString();
    }

    async function updateLeadStatus(leadId, newStatus) {
        try {
            const response = await fetch(`/dashboard/leads/${leadId}/status/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': '{{ csrf_token }}'
                },
                body: JSON.stringify({ status: newStatus })
            });

            const data = await response.json();
            if (!data.success) {
                alert('Erro ao atualizar: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Erro ao atualizar o lead.');
        }
    }

    function showLeadDetails(leadId) {
        // Find lead row and extract info
        const row = document.querySelector(`tr[data-lead-id="${leadId}"]`);
        if (!row) return;

        const name = row.querySelector('td:first-child strong').textContent;
        const email = row.querySelector('td:nth-child(2) a').textContent;
        const phone = row.querySelector('td:nth-child(3)').textContent.trim();
        const plan = row.querySelector('td:nth-child(4)').textContent.trim();
        const date = row.querySelector('td:nth-child(6)').textContent.trim();

        document.getElementById('lead-modal-body').innerHTML = `
        <div class="grid gap-2">
            <p><strong>Nome:</strong> ${name}</p>
            <p><strong>Email:</strong> ${email}</p>
            <p><strong>Telefone:</strong> ${phone || '-'}</p>
            <p><strong>Plano:</strong> ${plan}</p>
            <p><strong>Data:</strong> ${date}</p>
        </div>
    `;

        const modalBackdrop = document.getElementById('lead-modal');
        modalBackdrop.classList.add('active');
        modalBackdrop.style.visibility = 'visible';
        modalBackdrop.style.opacity = '1';
    }

    function closeLeadModal() {
        const modalBackdrop = document.getElementById('lead-modal');
        modalBackdrop.classList.remove('active');
        setTimeout(() => {
            if (!modalBackdrop.classList.contains('active')) {
                modalBackdrop.style.visibility = 'hidden';
                modalBackdrop.style.opacity = '0';
            }
        }, 300);
    }
</script>
{% endblock %}
"""

with open(leads_path, 'w', encoding='utf-8') as f:
    f.write(leads_content)
    print("Fixed leads.html")

# 2. Fix config.html with Design System classes AND Sidebar
config_path = r'c:\Users\olx\OneDrive\Desktop\PROJETOS 2026\PostPro\templates\agencies\landing\config.html'

config_content = """{% extends 'base.html' %}
{% load static %}

{% block title %}Landing Page - {{ request.user.agency.get_display_name }}{% endblock %}

{% block sidebar %}
{% include 'components/sidebar.html' %}
{% endblock %}

{% block content %}
<div class="container">
    <div class="page-header">
        <div class="page-header-content">
            <h1>Landing Page</h1>
            <p class="page-subtitle">Configure sua página pública de captação de leads</p>
        </div>
        <div class="page-actions btn-group-responsive">
            {% if landing_page.is_published %}
            <a href="{{ public_url }}" target="_blank" class="btn btn-secondary">
                <i class="icon-external-link"></i> Ver Página
            </a>
            {% endif %}
            <button type="button" id="btn-generate-ai" class="btn btn-primary">
                <i class="icon-sparkles"></i> Gerar com IA
            </button>
        </div>
    </div>

    <form method="post">
        {% csrf_token %}

        <div class="form-row items-start">
            <!-- Left Column: Content (Flex 2) -->
            <div class="flex-col gap-4" style="flex: 2; min-width: 0;">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Conteúdo Principal</h3>
                    </div>
                    <div class="card-body">
                        <div class="form-group">
                            <label for="hero_title" class="form-label">Título Hero</label>
                            <input type="text" id="hero_title" name="hero_title" value="{{ landing_page.hero_title }}"
                                class="form-input" maxlength="200"
                                placeholder="Transforme seu blog em uma máquina de vendas">
                            <span class="form-help">Título principal que aparece no topo da página</span>
                        </div>

                        <div class="form-group">
                            <label for="hero_subtitle" class="form-label">Subtítulo Hero</label>
                            <textarea id="hero_subtitle" name="hero_subtitle" class="form-textarea" rows="3"
                                placeholder="Geramos conteúdo otimizado para SEO de forma 100% automática...">{{ landing_page.hero_subtitle }}</textarea>
                            <span class="form-help">Descrição curta abaixo do título</span>
                        </div>

                        <div class="form-group">
                            <label for="about_section" class="form-label">Seção Sobre</label>
                            <textarea id="about_section" name="about_section" class="form-textarea" rows="6"
                                placeholder="Conte um pouco sobre sua agência, valores e diferenciais...">{{ landing_page.about_section }}</textarea>
                            <span class="form-help">Texto completo da seção "Sobre"</span>
                        </div>

                        <div class="form-group">
                            <label for="cta_text" class="form-label">Texto do Botão CTA</label>
                            <input type="text" id="cta_text" name="cta_text"
                                value="{{ landing_page.cta_text|default:'Começar Agora' }}" class="form-input"
                                maxlength="100" placeholder="Começar Agora">
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">SEO</h3>
                    </div>
                    <div class="card-body">
                        <div class="form-group">
                            <label for="meta_title" class="form-label">Título SEO</label>
                            <input type="text" id="meta_title" name="meta_title" value="{{ landing_page.meta_title }}"
                                class="form-input" maxlength="60" placeholder="Nome da Agência | Automação de Conteúdo">
                            <span class="form-help">Máximo 60 caracteres</span>
                        </div>

                        <div class="form-group">
                            <label for="meta_description" class="form-label">Descrição SEO</label>
                            <textarea id="meta_description" name="meta_description" class="form-textarea" rows="2"
                                maxlength="160"
                                placeholder="Gere artigos otimizados para SEO automaticamente...">{{ landing_page.meta_description }}</textarea>
                            <span class="form-help">Máximo 160 caracteres</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Column: Settings (Flex 1) -->
            <div class="flex-col gap-4" style="flex: 1; min-width: 0;">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Contato</h3>
                    </div>
                    <div class="card-body">
                        <div class="form-group">
                            <label for="whatsapp_number" class="form-label">WhatsApp</label>
                            <input type="text" id="whatsapp_number" name="whatsapp_number" class="form-input"
                                value="{{ landing_page.whatsapp_number }}" placeholder="5511999999999">
                            <span class="form-help">Número com DDD e código do país</span>
                        </div>

                        <div class="form-group">
                            <label for="email_contact" class="form-label">Email</label>
                            <input type="email" id="email_contact" name="email_contact" class="form-input"
                                value="{{ landing_page.email_contact }}" placeholder="contato@suaagencia.com.br">
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Publicação</h3>
                    </div>
                    <div class="card-body">
                        <div class="form-group flex items-center gap-2">
                            <input type="checkbox" name="is_published" id="is_published" class="form-checkbox" {% if landing_page.is_published %}checked{% endif %}>
                            <label for="is_published" class="form-label mb-0" style="cursor: pointer;">Publicar landing
                                page</label>
                        </div>
                        <div class="text-sm text-muted">
                            Quando publicada, estará acessível em: <a href="/p/{{ request.user.agency.slug }}/"
                                target="_blank">/p/{{ request.user.agency.slug }}/</a>
                        </div>

                        {% if landing_page.ai_generated_at %}
                        <div class="alert alert-info mt-4 mb-0">
                            <i class="icon-sparkles"></i>
                            <span>Gerado por IA em {{ landing_page.ai_generated_at|date:"d/m/Y H:i" }}</span>
                        </div>
                        {% endif %}
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Planos Exibidos</h3>
                    </div>
                    <div class="card-body">
                        {% if plans %}
                        <ul class="flex-col gap-2" style="list-style: none; padding: 0; margin: 0;">
                            {% for plan in plans %}
                            <li class="flex items-center justify-between p-2"
                                style="border-bottom: 1px solid var(--border-color);">
                                <div>
                                    <strong class="text-sm">{{ plan.name }}</strong>
                                    <div class="text-xs text-muted">{{ plan.posts_per_month }} posts/mês</div>
                                </div>
                                {% if plan.is_highlighted %}<span class="badge badge-primary">Destaque</span>{% endif %}
                            </li>
                            {% endfor %}
                        </ul>
                        {% else %}
                        <p class="text-muted text-sm">Nenhum plano cadastrado. <a
                                href="{% url 'dashboard:plans_list' %}">Criar planos</a></p>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>

        <div class="form-actions mt-6 flex gap-2">
            <button type="submit" class="btn btn-primary btn-lg">
                <i class="icon-save"></i> Salvar Alterações
            </button>
            {% if landing_page.is_published %}
            <a href="{% url 'dashboard:landing_preview' %}" target="_blank" class="btn btn-secondary">
                <i class="icon-eye"></i> Preview
            </a>
            {% endif %}
        </div>
    </form>
</div>

<script>
    document.addEventListener('DOMContentLoaded', function () {
        const btnGenerateAI = document.getElementById('btn-generate-ai');

        btnGenerateAI.addEventListener('click', async function () {
            if (this.classList.contains('loading')) return;

            if (!confirm('Isso irá substituir o conteúdo atual pelos textos gerados por IA. Continuar?')) {
                return;
            }

            this.classList.add('loading');
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></span> Gerando...';

            try {
                const response = await fetch('{% url "dashboard:landing_generate_ai" %}', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': '{{ csrf_token }}'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    // Update form fields
                    document.getElementById('hero_title').value = data.data.hero_title;
                    document.getElementById('hero_subtitle').value = data.data.hero_subtitle;
                    document.getElementById('about_section').value = data.data.about_section;
                    document.getElementById('cta_text').value = data.data.cta_text;
                    document.getElementById('meta_title').value = data.data.meta_title;
                    document.getElementById('meta_description').value = data.data.meta_description;

                    alert('Conteúdo gerado com sucesso! Revise e salve.');
                } else {
                    alert('Erro: ' + data.error);
                }
            } catch (error) {
                alert('Erro ao gerar conteúdo. Tente novamente.');
                console.error(error);
            } finally {
                this.classList.remove('loading');
                this.innerHTML = originalText;
            }
        });
    });
</script>
{% endblock %}
"""

with open(config_path, 'w', encoding='utf-8') as f:
    f.write(config_content)
    print("Fixed config.html")
