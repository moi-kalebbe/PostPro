
import os

TEMPLATE_PATH = r'c:\Users\olx\OneDrive\Desktop\PROJETOS 2026\PostPro\templates\projects\detail.html'

CONTENT = r'''{% extends 'base.html' %}
{% load static %}

{% block title %}{{ project.name }} - PostPro{% endblock %}

{% block sidebar %}
{% include 'components/sidebar.html' %}
{% endblock %}

{% block content %}
<div class="container">
    <div class="page-header">
        <div>
            <h1 class="page-title">{{ project.name }}</h1>
            <a href="{{ project.wordpress_url }}" target="_blank" class="text-muted flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                </svg>
                {{ project.wordpress_url|truncatechars:40 }}
            </a>
        </div>
        <div class="flex gap-2">
            <a href="{% url 'projects:edit' project.id %}" class="btn btn-secondary">Editar Projeto</a>
        </div>
    </div>

    <!-- Stats -->
    <div class="stats-grid mb-6">
        <div class="card">
            <div class="card-body stat-card">
                <span class="stat-label">Total de Posts</span>
                <span class="stat-value">{{ stats.total_posts }}</span>
            </div>
        </div>
        <div class="card">
            <div class="card-body stat-card">
                <span class="stat-label">Publicados</span>
                <span class="stat-value text-success">{{ stats.published }}</span>
            </div>
        </div>
        <div class="card">
            <div class="card-body stat-card">
                <span class="stat-label">Agendados</span>
                <span class="stat-value text-warning">{{ stats.pending }}</span>
            </div>
        </div>
        <div class="card">
            <div class="card-body stat-card">
                <span class="stat-label">Custo Total</span>
                <span class="stat-value text-primary">${{ stats.total_cost|floatformat:4 }}</span>
            </div>
        </div>
    </div>

    <!-- License Key Card (single column now) -->
    <div class="card mb-6">
        <div class="card-header">
            <h3 class="card-title">🔑 License Key</h3>
        </div>
        <div class="card-body">
            <p class="form-help mb-3">Use esta chave no plugin WordPress.</p>
            <div class="flex items-center gap-3">
                <code class="code-preview flex-1"
                    style="font-size: 0.75rem; word-break: break-all;">{{ project.license_key }}</code>
                <button class="btn btn-secondary btn-sm"
                    onclick="copyToClipboard('{{ project.license_key }}', this)">Copiar</button>
            </div>
        </div>
    </div>

    <!-- RSS Feed Settings -->
    <div class="card mb-6">
        <div class="card-header flex justify-between items-center">
            <div>
                <h3 class="card-title">📰 RSS Feed - Notícias Automáticas</h3>
                <p class="text-sm text-muted">Gerencie múltiplos feeds e configurações.</p>
            </div>
            <div>
                {% if rss_settings and rss_settings.is_active %}
                <span class="badge badge-success">Ativo</span>
                {% else %}
                <span class="badge badge-gray">Inativo</span>
                {% endif %}
            </div>
        </div>

        <div class="card-body">
            <!-- Global Settings Form -->
            <form method="POST" action="{% url 'projects:rss_settings' project.id %}"
                class="mb-6 p-4 bg-gray-50 rounded-lg border">
                {% csrf_token %}
                <h4 class="text-sm font-bold uppercase text-muted mb-4">Configurações Globais (Aplicam a todos os feeds)
                </h4>

                <div class="grid-2 gap-4">
                    <div class="form-group">
                        <label class="form-label">Intervalo de Verificação</label>
                        <select name="check_interval_minutes" class="form-input">
                            <option value="30" {% if rss_settings.check_interval_minutes == 30 %}selected{% endif %}>30 minutos</option>
                            <option value="60" {% if rss_settings.check_interval_minutes == 60 or not rss_settings %}selected{% endif %}>1 hora</option>
                            <option value="120" {% if rss_settings.check_interval_minutes == 120 %}selected{% endif %}>2 horas</option>
                            <option value="360" {% if rss_settings.check_interval_minutes == 360 %}selected{% endif %}>6 horas</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Máximo de Posts/Dia (Total)</label>
                        <select name="max_posts_per_day" class="form-input">
                            <option value="3" {% if rss_settings.max_posts_per_day == 3 %}selected{% endif %}>3 posts</option>
                            <option value="5" {% if rss_settings.max_posts_per_day == 5 or not rss_settings %}selected{% endif %}>5 posts</option>
                            <option value="10" {% if rss_settings.max_posts_per_day == 10 %}selected{% endif %}>10 posts</option>
                            <option value="20" {% if rss_settings.max_posts_per_day == 20 %}selected{% endif %}>20 posts</option>
                        </select>
                    </div>
                </div>

                <div class="grid-2 gap-4">
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" name="is_active" class="checkbox" {% if rss_settings.is_active %}checked{% endif %}>
                            <span>Ativar monitoramento global</span>
                        </label>
                    </div>
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" name="auto_publish" class="checkbox" {% if rss_settings.auto_publish %}checked{% endif %}>
                            <span>Publicar automaticamente</span>
                        </label>
                    </div>
                </div>

                <div class="form-group">
                    <label class="checkbox-label">
                        <input type="checkbox" name="download_images" class="checkbox" {% if rss_settings.download_images or not rss_settings %}checked{% endif %}>
                        <span>Baixar imagens do feed (recomendado)</span>
                    </label>
                </div>

                <div class="form-group">
                    <label class="checkbox-label">
                        <input type="checkbox" name="include_source_attribution" class="checkbox" {% if rss_settings.include_source_attribution or not rss_settings %}checked{% endif %}>
                        <span>Incluir atribuição à fonte original</span>
                    </label>
                </div>

                <div class="mt-2">
                    <button type="submit" class="btn btn-sm btn-primary">💾 Salvar Configurações</button>
                </div>
            </form>

            <!-- Feeds List -->
            <div class="flex justify-between items-center mb-4">
                <h4 class="text-md font-bold">Feeds Monitorados</h4>
                <button type="button" class="btn btn-sm btn-primary" onclick="openRSSFeedModal()">
                    <span class="mr-1">➕</span> Adicionar Feed
                </button>
            </div>

            {% if feeds %}
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Nome / URL</th>
                            <th>Status</th>
                            <th>Última Verificação</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for feed in feeds %}
                        <tr>
                            <td>
                                <div class="font-bold">{{ feed.name|default:'Sem nome' }}</div>
                                <div class="text-xs text-muted truncate max-w-xs" title="{{ feed.feed_url }}">{{ feed.feed_url }}</div>
                            </td>
                            <td>
                                {% if feed.is_active %}
                                <span class="badge badge-success badge-sm">Ativo</span>
                                {% else %}
                                <span class="badge badge-gray badge-sm">Inativo</span>
                                {% endif %}
                            </td>
                            <td>
                                {% if feed.last_checked_at %}{{ feed.last_checked_at|date:"d/m H:i" }}{% else %}-{% endif %}
                            </td>
                            <td>
                                <form method="POST" action="{% url 'projects:rss_feed_delete' project.id feed.id %}"
                                    onsubmit="return confirm('Tem certeza que deseja remover este feed?');"
                                    style="display:inline;">
                                    {% csrf_token %}
                                    <button type="submit" class="text-error font-bold px-2"
                                        title="Remover">🗑️</button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <div class="text-center p-6 border border-dashed rounded bg-gray-50">
                <p class="text-muted">Nenhum feed RSS configurado ainda.</p>
                <div class="mt-2">
                    <button type="button" class="btn btn-ghost" onclick="openRSSFeedModal()">Adicionar o primeiro feed</button>
                </div>
            </div>
            {% endif %}

            {% if rss_settings and rss_settings.last_checked_at %}
            <p class="text-muted text-sm mt-4 text-right">
                Última verificação global: {{ rss_settings.last_checked_at|date:"d/m/Y H:i" }} |
                Processados hoje: {{ rss_settings.items_processed_today }}/{{ rss_settings.max_posts_per_day }}
            </p>
            {% endif %}
        </div>
    </div>

    <!-- Add Feed Modal (Standardized) -->
    <div id="addFeedModal" class="modal-backdrop">
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title">Adicionar Novo Feed RSS</h3>
                <button type="button" class="modal-close" onclick="closeRSSFeedModal()">&times;</button>
            </div>
            <form method="POST" action="{% url 'projects:rss_feed_create' project.id %}">
                {% csrf_token %}
                <div class="modal-body">
                    <div class="form-group">
                        <label class="form-label">URL do Feed (XML)</label>
                        <input type="url" name="feed_url" class="form-input" required placeholder="https://exemplo.com/feed.xml">
                        <p class="form-help">Certifique-se que é um link direto para o arquivo RSS/XML.</p>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Nome (Opcional)</label>
                        <input type="text" name="name" class="form-input" placeholder="Ex: G1 Tecnologia">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-ghost" onclick="closeRSSFeedModal()">Cancelar</button>
                    <button type="submit" class="btn btn-primary">Adicionar Feed</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        function openRSSFeedModal() {
            const modal = document.getElementById('addFeedModal');
            if (modal) modal.classList.add('active');
        }

        function closeRSSFeedModal() {
            const modal = document.getElementById('addFeedModal');
            if (modal) modal.classList.remove('active');
        }

        // Close modal if clicked outside
        window.addEventListener('click', function (event) {
            var modal = document.getElementById('addFeedModal');
            if (event.target == modal) {
                closeRSSFeedModal();
            }
        });
    </script>

    <!-- RSS Items Pending (if any) -->
    {% if rss_items %}
    <div class="card mb-6">
        <div class="card-header">
            <h3 class="card-title">📋 Itens RSS Pendentes</h3>
            <span class="badge badge-info">{{ rss_items.count }}</span>
        </div>
        <div class="table-container">
            <table class="table">
                <thead>
                    <tr>
                        <th>Título</th>
                        <th>Status</th>
                        <th>Data</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in rss_items %}
                    <tr>
                        <td>
                            <a href="{{ item.source_url }}" target="_blank" class="flex items-center gap-1">
                                {{ item.source_title|truncatewords:10 }}
                                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24"
                                    fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                    <polyline points="15 3 21 3 21 9"></polyline>
                                    <line x1="10" y1="14" x2="21" y2="3"></line>
                                </svg>
                            </a>
                        </td>
                        <td>
                            {% if item.status == 'pending' %}
                            <span class="badge badge-warning">Pendente</span>
                            {% elif item.status == 'processing' %}
                            <span class="badge badge-info">Processando</span>
                            {% elif item.status == 'completed' %}
                            <span class="badge badge-success">Concluído</span>
                            {% elif item.status == 'failed' %}
                            <span class="badge badge-error" title="{{ item.error_message }}">Erro</span>
                            {% else %}
                            <span class="badge badge-gray">{{ item.status }}</span>
                            {% endif %}
                        </td>
                        <td class="text-muted">{{ item.created_at|date:"d/m H:i" }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}

    <!-- Plano Editorial -->
    <div class="card mt-6">
        <div class="card-header">
            <h3 class="card-title">📅 Plano Editorial (30 dias)</h3>
            <div class="flex items-center gap-2">
                {% if editorial_plan %}
                <span
                    class="badge badge-{% if editorial_plan.status == 'active' %}success{% elif editorial_plan.status == 'pending_approval' %}warning{% else %}info{% endif %}">
                    {{ editorial_plan.get_status_display }}
                </span>
                {% endif %}
                {% if editorial_items %}
                <button type="button" class="btn btn-error btn-sm" onclick="confirmDeleteAllItems()">
                    🗑️ Excluir Todos
                </button>
                {% endif %}
            </div>
        </div>

        <!-- Bulk Actions Bar (hidden by default) -->
        <div id="bulk-actions-bar" class="card-body border-b"
            style="display: none; background: var(--surface-elevated);">
            <div class="flex items-center justify-between">
                <span id="selected-count" class="text-sm font-medium">0 itens selecionados</span>
                <div class="flex gap-2">
                    <button type="button" class="btn btn-error btn-sm" onclick="bulkDeleteItems()">
                        🗑️ Excluir Selecionados
                    </button>
                    <button type="button" class="btn btn-ghost btn-sm" onclick="clearSelection()">
                        Cancelar
                    </button>
                </div>
            </div>
        </div>

        <div class="table-container">
            <table class="table">
                <thead>
                    <tr>
                        <th style="width: 40px;">
                            <input type="checkbox" id="select-all" class="checkbox" onchange="toggleSelectAll(this)">
                        </th>
                        <th>Dia</th>
                        <th>Título</th>
                        <th>Keyword</th>
                        <th>Status</th>
                        <th>Data</th>
                        <th style="width: 60px;">Ações</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in editorial_items %}
                    <tr data-item-id="{{ item.id }}">
                        <td>
                            <input type="checkbox" class="checkbox item-checkbox" value="{{ item.id }}"
                                onchange="updateBulkBar()">
                        </td>
                        <td><strong>{{ item.day_index }}</strong></td>
                        <td>{{ item.title|truncatewords:8 }}</td>
                        <td><span class="badge badge-gray">{{ item.keyword_focus }}</span></td>
                        <td>
                            {% if item.status == 'completed' %}
                            <span class="badge badge-success">{{ item.get_status_display }}</span>
                            {% elif item.status == 'generating' %}
                            <span class="badge badge-info">{{ item.get_status_display }}</span>
                            {% elif item.status == 'failed' %}
                            <span class="badge badge-error">{{ item.get_status_display }}</span>
                            {% else %}
                            <span class="badge badge-warning">{{ item.get_status_display }}</span>
                            {% endif %}
                        </td>
                        <td class="text-muted">{{ item.scheduled_date|date:"d/m/Y" }}</td>
                        <td>
                            <button type="button" class="btn btn-ghost btn-sm text-error"
                                onclick="confirmDeleteItem('{{ item.id }}', '{{ item.title|escapejs }}')"
                                title="Excluir">
                                🗑️
                            </button>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="7" class="text-center text-muted p-6">
                            {% if editorial_plan and editorial_plan.status == 'generating' %}
                            <div class="flex flex-col items-center gap-2">
                                <div class="spinner"></div>
                                <p><strong>Gerando plano editorial...</strong></p>
                                <p class="text-sm">Isso pode levar alguns minutos. A IA está pesquisando tendências e
                                    criando títulos otimizados.</p>
                                <button class="btn btn-secondary btn-sm mt-2" onclick="location.reload()">🔄
                                    Atualizar</button>
                            </div>
                            {% else %}
                            Nenhum plano editorial ativo. Configure as palavras-chave no plugin WordPress para gerar um
                            plano.
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Posts Recentes -->
    <div class="card mt-6">
        <div class="card-header">
            <h3 class="card-title">📝 Posts Recentes</h3>
            <a href="{% url 'automation:posts_list' %}?project={{ project.id }}" class="btn btn-ghost btn-sm">Ver
                todos</a>
        </div>
        <div class="table-container">
            <table class="table">
                <thead>
                    <tr>
                        <th>Título</th>
                        <th>Status</th>
                        <th>Custo</th>
                        <th>Data</th>
                    </tr>
                </thead>
                <tbody>
                    {% for post in recent_posts %}
                    <tr>
                        <td><strong>{{ post.title|truncatewords:6|default:post.keyword }}</strong></td>
                        <td>
                            {% if post.status == 'published' %}
                            <span class="badge badge-success">{{ post.get_status_display }}</span>
                            {% elif post.status == 'pending_review' %}
                            <span class="badge badge-warning">{{ post.get_status_display }}</span>
                            {% elif post.status == 'failed' %}
                            <span class="badge badge-error">{{ post.get_status_display }}</span>
                            {% else %}
                            <span class="badge badge-info">{{ post.get_status_display }}</span>
                            {% endif %}
                        </td>
                        <td>${{ post.total_cost|floatformat:4 }}</td>
                        <td class="text-muted">{{ post.created_at|date:"d/m H:i" }}</td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="4" class="text-center text-muted p-6">Nenhum post gerado ainda</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Delete Confirmation Modal (Using Standard Design System) -->
<div id="delete-modal" class="modal-backdrop">
    <div class="modal">
        <div class="modal-header">
            <h3 class="modal-title">⚠️ Confirmar Exclusão</h3>
            <button class="modal-close" onclick="closeDeleteModal()">&times;</button>
        </div>
        <div class="modal-body">
            <p id="delete-modal-message">Tem certeza que deseja excluir este item?</p>
            <div class="form-group mt-4">
                <label class="checkbox-label">
                    <input type="checkbox" id="delete-from-wp" class="checkbox">
                    <span>Também excluir do WordPress (se publicado)</span>
                </label>
            </div>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-ghost" onclick="closeDeleteModal()">Cancelar</button>
            <button type="button" class="btn btn-error" id="confirm-delete-btn">Excluir</button>
        </div>
    </div>
</div>

<script>
    // API URLs - built manually to avoid Django template issues with UUID placeholders
    const PROJECT_ID = '{{ project.id }}';
    const DELETE_ITEM_URL_BASE = `/projects/${PROJECT_ID}/editorial-item/`;
    const BULK_DELETE_URL = `/projects/${PROJECT_ID}/editorial-items/bulk-delete/`;
    const CSRF_TOKEN = '{{ csrf_token }}';

    // Selection State
    let selectedItems = new Set();
    let deleteCallback = null;

    function toggleSelectAll(checkbox) {
        const checkboxes = document.querySelectorAll('.item-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = checkbox.checked;
            if (checkbox.checked) {
                selectedItems.add(cb.value);
            } else {
                selectedItems.delete(cb.value);
            }
        });
        updateBulkBar();
    }

    function updateBulkBar() {
        const checkboxes = document.querySelectorAll('.item-checkbox:checked');
        selectedItems = new Set([...checkboxes].map(cb => cb.value));
        const bar = document.getElementById('bulk-actions-bar');
        const count = document.getElementById('selected-count');

        if (selectedItems.size > 0) {
            bar.style.display = 'block';
            count.textContent = `${selectedItems.size} item(ns) selecionado(s)`;
        } else {
            bar.style.display = 'none';
        }

        // Update select-all checkbox
        const allCheckboxes = document.querySelectorAll('.item-checkbox');
        const selectAll = document.getElementById('select-all');
        if (allCheckboxes.length > 0) {
            selectAll.checked = checkboxes.length === allCheckboxes.length;
            selectAll.indeterminate = checkboxes.length > 0 && checkboxes.length < allCheckboxes.length;
        }
    }

    function clearSelection() {
        selectedItems.clear();
        document.querySelectorAll('.item-checkbox').forEach(cb => cb.checked = false);
        document.getElementById('select-all').checked = false;
        updateBulkBar();
    }

    function openDeleteModal(message, callback) {
        const modal = document.getElementById('delete-modal');
        document.getElementById('delete-modal-message').textContent = message;
        document.getElementById('delete-from-wp').checked = false;
        deleteCallback = callback;

        // Use new design system class
        modal.classList.add('active');
    }

    function closeDeleteModal() {
        const modal = document.getElementById('delete-modal');
        modal.classList.remove('active');
        deleteCallback = null;
    }

    document.getElementById('confirm-delete-btn').addEventListener('click', function () {
        if (deleteCallback) {
            const deleteFromWp = document.getElementById('delete-from-wp').checked;
            deleteCallback(deleteFromWp);
        }
        closeDeleteModal();
    });

    function confirmDeleteItem(itemId, title) {
        openDeleteModal(
            `Tem certeza que deseja excluir "${title}"?`,
            function (deleteFromWp) {
                deleteItem(itemId, deleteFromWp);
            }
        );
    }

    // Delete Item
    async function deleteItem(itemId, deleteFromWp) {
        try {
            const response = await fetch(`${DELETE_ITEM_URL_BASE}${itemId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': CSRF_TOKEN,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ delete_from_wp: deleteFromWp })
            });

            if (response.ok) {
                // Remove row
                const row = document.querySelector(`tr[data-item-id="${itemId}"]`);
                if (row) row.remove();

                // Check if empty
                if (document.querySelectorAll('tbody tr').length === 0) {
                    location.reload();
                } else {
                    updateBulkBar(); // Update selection count
                }
            } else {
                alert('Erro ao excluir item. Tente novamente.');
            }
        } catch (error) {
            console.error('Delete error:', error);
            alert('Erro de conexão ao excluir item.');
        }
    }

    // Bulk Delete
    function bulkDeleteItems() {
        if (selectedItems.size === 0) return;

        openDeleteModal(
            `Tem certeza que deseja excluir ${selectedItems.size} itens selecionados?`,
            function (deleteFromWp) {
                performBulkDelete(deleteFromWp);
            }
        );
    }

    async function performBulkDelete(deleteFromWp) {
        try {
            const response = await fetch(BULK_DELETE_URL, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': CSRF_TOKEN,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    item_ids: Array.from(selectedItems),
                    delete_from_wp: deleteFromWp
                })
            });

            if (response.ok) {
                location.reload();
            } else {
                alert('Erro ao excluir itens em massa. Tente novamente.');
            }
        } catch (error) {
            console.error('Bulk delete error:', error);
            alert('Erro de conexão ao excluir itens.');
        }
    }

    function confirmDeleteAllItems() {
        if (!confirm('ATENÇÃO: Isso excluirá TODOS os itens do plano editorial atual. Esta ação não pode ser desfeita.\n\nDeseja continuar?')) {
            return;
        }

        const deleteUrl = `/projects/${PROJECT_ID}/editorial-items/delete-all/`;
    }
</script>
{% endblock %}'''

with open(TEMPLATE_PATH, 'w', encoding='utf-8') as f:
    f.write(CONTENT)

print(f"Sucesso! Arquivo {TEMPLATE_PATH} reescrito conforme Design System.")
