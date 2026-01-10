"""
Script para corrigir o template detail.html do projeto.
Seguindo workflow django-templates.md para evitar corrupção.
CORRIGIDO: Usa UUID válido + abordagem manual para URL dinâmica.
"""

content = r'''{% extends 'base.html' %}
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

    <!-- Plano Editorial -->
    <div class="card mt-6">
        <div class="card-header">
            <h3 class="card-title">📅 Plano Editorial (30 dias)</h3>
            <div class="flex items-center gap-2">
                {% if editorial_plan %}
                <span class="badge badge-{% if editorial_plan.status == 'active' %}success{% elif editorial_plan.status == 'pending_approval' %}warning{% else %}info{% endif %}">{{ editorial_plan.get_status_display }}</span>
                {% endif %}
                {% if editorial_items %}
                <button type="button" class="btn btn-error btn-sm" onclick="confirmDeleteAllItems()">
                    🗑️ Excluir Todos
                </button>
                {% endif %}
            </div>
        </div>
        
        <!-- Bulk Actions Bar (hidden by default) -->
        <div id="bulk-actions-bar" class="card-body border-b" style="display: none; background: var(--surface-elevated);">
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
                            <input type="checkbox" class="checkbox item-checkbox" value="{{ item.id }}" onchange="updateBulkBar()">
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
                            <button type="button" class="btn btn-ghost btn-sm text-error" onclick="confirmDeleteItem('{{ item.id }}', '{{ item.title|escapejs }}')" title="Excluir">
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
                            Nenhum plano editorial ativo. Configure as palavras-chave no plugin WordPress para gerar um plano.
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

<!-- Delete Confirmation Modal -->
<div id="delete-modal" class="modal" style="display: none;">
    <div class="modal-overlay" onclick="closeDeleteModal()"></div>
    <div class="modal-content">
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
    document.getElementById('delete-modal-message').textContent = message;
    document.getElementById('delete-modal').style.display = 'flex';
    document.getElementById('delete-from-wp').checked = false;
    deleteCallback = callback;
}

function closeDeleteModal() {
    document.getElementById('delete-modal').style.display = 'none';
    deleteCallback = null;
}

document.getElementById('confirm-delete-btn').addEventListener('click', function() {
    if (deleteCallback) {
        const deleteFromWp = document.getElementById('delete-from-wp').checked;
        deleteCallback(deleteFromWp);
    }
    closeDeleteModal();
});

function confirmDeleteItem(itemId, title) {
    openDeleteModal(
        `Tem certeza que deseja excluir "${title}"?`,
        function(deleteFromWp) {
            deleteItem(itemId, deleteFromWp);
        }
    );
}

function confirmDeleteAllItems() {
    const count = document.querySelectorAll('.item-checkbox').length;
    openDeleteModal(
        `Tem certeza que deseja excluir TODOS os ${count} itens do plano editorial?`,
        function(deleteFromWp) {
            deleteAllItems(deleteFromWp);
        }
    );
}

function bulkDeleteItems() {
    if (selectedItems.size === 0) return;
    
    openDeleteModal(
        `Tem certeza que deseja excluir ${selectedItems.size} item(ns) selecionado(s)?`,
        function(deleteFromWp) {
            deleteBulkItems([...selectedItems], deleteFromWp);
        }
    );
}

async function deleteItem(itemId, deleteFromWp) {
    try {
        const response = await fetch(`${DELETE_ITEM_URL_BASE}${itemId}/delete/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ delete_from_wordpress: deleteFromWp })
        });
        
        const data = await response.json();
        if (data.success) {
            document.querySelector(`tr[data-item-id="${itemId}"]`).remove();
            showToast('Item excluído com sucesso', 'success');
        } else {
            showToast(data.message || 'Erro ao excluir', 'error');
        }
    } catch (error) {
        showToast('Erro ao excluir item', 'error');
        console.error(error);
    }
}

async function deleteBulkItems(itemIds, deleteFromWp) {
    try {
        const response = await fetch(BULK_DELETE_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ item_ids: itemIds, delete_from_wordpress: deleteFromWp })
        });
        
        const data = await response.json();
        if (data.success) {
            itemIds.forEach(id => {
                const row = document.querySelector(`tr[data-item-id="${id}"]`);
                if (row) row.remove();
            });
            clearSelection();
            showToast(`${data.deleted_count} item(ns) excluído(s)`, 'success');
        } else {
            showToast(data.message || 'Erro ao excluir', 'error');
        }
    } catch (error) {
        showToast('Erro ao excluir itens', 'error');
        console.error(error);
    }
}

async function deleteAllItems(deleteFromWp) {
    const allIds = [...document.querySelectorAll('.item-checkbox')].map(cb => cb.value);
    await deleteBulkItems(allIds, deleteFromWp);
}

function showToast(message, type) {
    // Simple toast implementation
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = 'position: fixed; bottom: 20px; right: 20px; padding: 12px 24px; border-radius: 8px; z-index: 9999; animation: slideIn 0.3s ease;';
    toast.style.background = type === 'success' ? 'var(--success)' : 'var(--error)';
    toast.style.color = 'white';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function copyToClipboard(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
        const original = btn.textContent;
        btn.textContent = 'Copiado!';
        setTimeout(() => btn.textContent = original, 2000);
    });
}
</script>
{% endblock %}
'''

import os

template_path = r'c:\Users\olx\OneDrive\Desktop\PROJETOS 2026\PostPro\templates\projects\detail.html'

with open(template_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Template atualizado: {template_path}')
print('Verificando sintaxe...')

# Verificar padrões problemáticos
errors = []
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    # Check for operators without spaces
    import re
    if re.search(r'{% if .*[^ ]==[^ ].* %}', line):
        errors.append(f'Linha {i}: Operador == sem espaços')
    if re.search(r'{% if .*[^ ]!=[^ ].* %}', line):
        errors.append(f'Linha {i}: Operador != sem espaços')

if errors:
    print('ERROS ENCONTRADOS:')
    for e in errors:
        print(f'  - {e}')
else:
    print('OK - Nenhum erro de sintaxe detectado')
