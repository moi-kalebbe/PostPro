#!/usr/bin/env python
"""
Script to rewrite posts_list.html with unified Posts + RSS tabs.
Following django-templates.md workflow to ensure correct syntax.

Key rules:
- All Django tags on single lines
- Spaces around == operators
- Use Design System classes
"""

import os

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'templates', 'automation', 'posts_list.html'
)

TEMPLATE_CONTENT = r'''{% extends 'base.html' %}
{% load static %}

{% block title %}Posts - PostPro{% endblock %}

{% block sidebar %}
{% include 'components/sidebar.html' %}
{% endblock %}

{% block content %}
<div class="container">
    <div class="page-header">
        <h1 class="page-title">Conteúdo</h1>
    </div>

    <!-- Tabs Navigation -->
    <div class="card mb-4">
        <div class="card-body" style="padding: 0.5rem 1rem;">
            <div class="flex gap-2 flex-wrap" style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">
                <a href="?tab=posts" class="btn {% if active_tab == 'posts' %}btn-primary{% else %}btn-ghost{% endif %} btn-sm">
                    📝 Posts Gerados
                </a>
                <a href="?tab=rss" class="btn {% if active_tab == 'rss' %}btn-primary{% else %}btn-ghost{% endif %} btn-sm">
                    📰 Fila RSS
                </a>
                <a href="?tab=stats" class="btn {% if active_tab == 'stats' %}btn-primary{% else %}btn-ghost{% endif %} btn-sm">
                    📊 Estatísticas
                </a>
            </div>
        </div>
    </div>

    <!-- Tab: Posts -->
    {% if active_tab == 'posts' %}
    <div class="card mb-6">
        <div class="card-body">
            <form method="get" class="flex gap-4 items-end flex-wrap">
                <input type="hidden" name="tab" value="posts">
                <div class="form-group mb-0" style="min-width: 200px;">
                    <label class="form-label">Projeto</label>
                    <select name="project" class="form-select" onchange="this.form.submit()">
                        <option value="">Todos projetos</option>
                        {% for proj in projects %}
                        <option value="{{ proj.id }}"{% if proj.is_selected %} selected{% endif %}>{{ proj.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group mb-0" style="min-width: 150px;">
                    <label class="form-label">Status</label>
                    <select name="status" class="form-select" onchange="this.form.submit()">
                        <option value="">Todos status</option>
                        {% for value, label in status_choices %}
                        <option value="{{ value }}"{% if status_filter == value %} selected{% endif %}>{{ label }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group mb-0 flex-1" style="min-width: 200px;">
                    <label class="form-label">Buscar</label>
                    <input type="text" name="search" class="form-input" value="{{ search }}" placeholder="Keyword ou título...">
                </div>
            </form>
        </div>
    </div>

    <div class="card">
        <div class="card-header bulk-actions-bar" id="bulk-actions-bar" style="display: none;">
            <div class="flex items-center gap-4">
                <span id="selected-count">0 selecionados</span>
                <button type="button" class="btn btn-primary btn-sm" onclick="bulkPublish()">
                    Publicar selecionados
                </button>
                <button type="button" class="btn btn-error btn-sm" onclick="confirmBulkDelete()">
                    Excluir selecionados
                </button>
                <button type="button" class="btn btn-ghost btn-sm" onclick="clearSelection()">
                    Limpar seleção
                </button>
            </div>
        </div>
        <div class="table-container">
            <table class="table">
                <thead>
                    <tr>
                        <th style="width: 40px;">
                            <input type="checkbox" id="select-all-checkbox" onchange="toggleSelectAll(this)">
                        </th>
                        <th>Keyword</th>
                        <th>Projeto</th>
                        <th>Status</th>
                        <th>Custo</th>
                        <th>Data</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    {% for post in posts %}
                    <tr data-post-id="{{ post.id }}">
                        <td>
                            <input type="checkbox" class="post-checkbox" value="{{ post.id }}" onchange="updateBulkBar()">
                        </td>
                        <td class="font-bold">{{ post.keyword|truncatewords:5 }}</td>
                        <td><span class="badge badge-primary">{{ post.project.name }}</span></td>
                        <td><span class="badge {% if post.status == 'published' %}badge-success{% elif post.status == 'failed' %}badge-error{% else %}badge-warning{% endif %}">{{ post.get_status_display }}</span></td>
                        <td>${{ post.total_cost|floatformat:4 }}</td>
                        <td class="text-muted">{{ post.created_at|date:"d/m H:i" }}</td>
                        <td>
                            <div class="flex gap-1">
                                <button class="btn btn-ghost btn-sm" onclick="openPostModal('{{ post.id }}')" title="Preview">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                                </button>
                                {% if post.status == 'pending_review' or post.status == 'approved' %}
                                <button class="btn btn-ghost btn-sm" onclick="publishPost('{{ post.id }}')" title="Publicar">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 16 12 12 8 16"></polyline><line x1="12" y1="12" x2="12" y2="21"></line><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"></path></svg>
                                </button>
                                {% endif %}
                                {% if post.wordpress_edit_url %}
                                <a href="{{ post.wordpress_edit_url }}" target="_blank" class="btn btn-ghost btn-sm" title="Editar no WP">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                                </a>
                                {% endif %}
                                <button class="btn btn-ghost btn-sm text-error" onclick="openDeleteModal('{{ post.id }}', '{{ post.keyword|truncatewords:3 }}')" title="Excluir">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                                </button>
                            </div>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="7" class="text-center text-muted py-8">Nenhum post encontrado.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        {% if posts.has_other_pages %}
        <div class="card-footer">
            <div class="flex justify-center gap-2">
                {% if posts.has_previous %}
                <a href="?tab=posts&page={{ posts.previous_page_number }}&project={{ project_filter }}&status={{ status_filter }}&search={{ search }}" class="btn btn-ghost btn-sm">&laquo; Anterior</a>
                {% endif %}
                <span class="btn btn-ghost btn-sm">Página {{ posts.number }} de {{ posts.paginator.num_pages }}</span>
                {% if posts.has_next %}
                <a href="?tab=posts&page={{ posts.next_page_number }}&project={{ project_filter }}&status={{ status_filter }}&search={{ search }}" class="btn btn-ghost btn-sm">Próxima &raquo;</a>
                {% endif %}
            </div>
        </div>
        {% endif %}
    </div>
    {% endif %}

    <!-- Tab: RSS -->
    {% if active_tab == 'rss' %}
    <div class="grid-3 mb-6 gap-4">
        <div class="card p-4">
            <div class="text-sm text-muted uppercase font-bold">Total de Feeds</div>
            <div class="text-3xl font-bold mt-2">{{ total_feeds }}</div>
            <div class="text-sm text-success mt-1">{{ active_feeds }} ativos</div>
        </div>
        <div class="card p-4">
            <div class="text-sm text-muted uppercase font-bold">Processados Hoje</div>
            <div class="text-3xl font-bold mt-2">{{ processed_today }}</div>
            <div class="text-sm text-muted mt-1">Notícias convertidas</div>
        </div>
        <div class="card p-4">
            <div class="text-sm text-muted uppercase font-bold">Última Atividade</div>
            <div class="text-xl font-bold mt-2">{% if recent_items %}{{ recent_items.0.created_at|date:"H:i" }}{% else %}-{% endif %}</div>
            <div class="text-sm text-muted mt-1 truncate">{% if recent_items %}{{ recent_items.0.project.name }}{% else %}Sem atividades{% endif %}</div>
        </div>
    </div>

    <div class="grid gap-6" style="grid-template-columns: 2fr 1fr;">
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">Fluxo de Notícias Recentes</h3>
            </div>
            <div class="table-container">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Data</th>
                            <th>Projeto</th>
                            <th>Título / Fonte</th>
                            <th>Status</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in recent_items %}
                        <tr>
                            <td class="text-muted whitespace-nowrap">{{ item.created_at|date:"d/m H:i" }}</td>
                            <td>
                                <a href="{% url 'projects:detail' item.project.id %}" class="badge badge-primary">{{ item.project.name }}</a>
                            </td>
                            <td>
                                <div class="font-bold truncate" style="max-width: 300px;" title="{{ item.source_title }}">
                                    <a href="{{ item.source_url }}" target="_blank" rel="noopener" class="hover:underline">{{ item.source_title|truncatewords:10 }}</a>
                                </div>
                            </td>
                            <td>
                                <span class="badge {% if item.status == 'PROCESSED' %}badge-success{% elif item.status == 'FAILED' %}badge-error{% elif item.status == 'PROCESSING' %}badge-warning{% else %}badge-info{% endif %}">{{ item.get_status_display }}</span>
                            </td>
                            <td>
                                {% if item.post %}
                                <a href="{% url 'automation:posts_list' %}?tab=posts&search={{ item.post.keyword|urlencode }}" class="btn btn-ghost btn-sm">Ver Post</a>
                                {% else %}
                                <span class="text-muted text-sm">-</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% empty %}
                        <tr>
                            <td colspan="5" class="text-center text-muted py-8">Nenhuma notícia processada recentemente.</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">Status dos Feeds</h3>
            </div>
            <div class="card-body p-0">
                <ul class="divide-y" style="max-height: 400px; overflow-y: auto;">
                    {% for feed in feeds %}
                    <li class="p-3 flex justify-between items-center">
                        <div class="overflow-hidden pr-2">
                            <div class="font-bold text-sm truncate" title="{{ feed.name|default:feed.feed_url }}">{{ feed.name|default:feed.feed_url|truncatechars:30 }}</div>
                            <div class="text-xs text-muted">
                                <a href="{% url 'projects:detail' feed.project.id %}" class="hover:underline">{{ feed.project.name }}</a>
                            </div>
                        </div>
                        <div class="text-right whitespace-nowrap">
                            <div class="text-xs font-bold {% if feed.is_active %}text-success{% else %}text-muted{% endif %}">{% if feed.is_active %}● Ativo{% else %}○ Inativo{% endif %}</div>
                            <div class="text-xs text-muted">{{ feed.last_checked_at|date:"H:i"|default:"-" }}</div>
                        </div>
                    </li>
                    {% empty %}
                    <li class="p-4 text-center text-muted text-sm">Nenhum feed cadastrado.</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- Tab: Stats -->
    {% if active_tab == 'stats' %}
    <div class="grid-3 mb-6 gap-4">
        <div class="card p-6 text-center">
            <div class="text-4xl font-bold text-primary">{{ total_posts }}</div>
            <div class="text-muted mt-2">Posts Totais</div>
        </div>
        <div class="card p-6 text-center">
            <div class="text-4xl font-bold text-success">{{ published_posts }}</div>
            <div class="text-muted mt-2">Publicados</div>
        </div>
        <div class="card p-6 text-center">
            <div class="text-4xl font-bold text-info">{{ total_feeds }}</div>
            <div class="text-muted mt-2">Feeds RSS</div>
        </div>
    </div>
    <div class="card">
        <div class="card-body text-center text-muted py-8">
            <p>Mais estatísticas em breve...</p>
        </div>
    </div>
    {% endif %}
</div>

<!-- Delete Modal -->
<div id="deleteModal" class="modal-backdrop">
    <div class="modal">
        <div class="modal-header">
            <h3 class="modal-title">Confirmar Exclusão</h3>
        </div>
        <div class="modal-body">
            <p>Deseja realmente excluir o post <strong id="deletePostKeyword"></strong>?</p>
            <p class="text-muted text-sm mt-2">Esta ação não pode ser desfeita.</p>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-ghost" onclick="closeDeleteModal()">Cancelar</button>
            <button type="button" class="btn btn-error" onclick="confirmDelete()">Excluir</button>
        </div>
    </div>
</div>

<!-- Post Preview Modal -->
<div id="postModal" class="modal-backdrop">
    <div class="modal" style="max-width: 800px;">
        <div class="modal-header">
            <h3 class="modal-title">Preview do Post</h3>
            <button type="button" class="btn btn-ghost btn-sm" onclick="closePostModal()">&times;</button>
        </div>
        <div class="modal-body" id="postModalContent">
            <div class="text-center py-8">
                <div class="loading-spinner"></div>
                <p class="text-muted mt-4">Carregando...</p>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    let deletePostId = null;
    let deleteWpId = null;

    function toggleSelectAll(checkbox) {
        const checkboxes = document.querySelectorAll('.post-checkbox');
        checkboxes.forEach(cb => cb.checked = checkbox.checked);
        updateBulkBar();
    }

    function updateBulkBar() {
        const checkedBoxes = document.querySelectorAll('.post-checkbox:checked');
        const bar = document.getElementById('bulk-actions-bar');
        const countSpan = document.getElementById('selected-count');
        if (checkedBoxes.length > 0) {
            bar.style.display = 'block';
            countSpan.textContent = checkedBoxes.length + ' selecionado(s)';
        } else {
            bar.style.display = 'none';
        }
    }

    function clearSelection() {
        document.querySelectorAll('.post-checkbox').forEach(cb => cb.checked = false);
        document.getElementById('select-all-checkbox').checked = false;
        updateBulkBar();
    }

    function getSelectedPostIds() {
        return Array.from(document.querySelectorAll('.post-checkbox:checked')).map(cb => cb.value);
    }

    function bulkPublish() {
        const ids = getSelectedPostIds();
        if (ids.length === 0) return;
        if (!confirm('Publicar ' + ids.length + ' posts selecionados?')) return;
        ids.forEach(id => publishPost(id));
        clearSelection();
    }

    function confirmBulkDelete() {
        const ids = getSelectedPostIds();
        if (ids.length === 0) return;
        if (!confirm('Excluir ' + ids.length + ' posts selecionados? Esta ação não pode ser desfeita.')) return;
        ids.forEach(id => deletePost(id));
        setTimeout(() => location.reload(), 1000);
    }

    function openDeleteModal(postId, keyword, wpId) {
        deletePostId = postId;
        deleteWpId = wpId;
        document.getElementById('deletePostKeyword').textContent = keyword;
        document.getElementById('deleteModal').classList.add('active');
    }

    function closeDeleteModal() {
        document.getElementById('deleteModal').classList.remove('active');
        deletePostId = null;
        deleteWpId = null;
    }

    function confirmDelete() {
        if (!deletePostId) return;
        deletePost(deletePostId);
        closeDeleteModal();
        setTimeout(() => location.reload(), 500);
    }

    function deletePost(postId) {
        fetch('/automation/posts/' + postId + '/delete/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/json'
            }
        });
    }

    function publishPost(postId) {
        fetch('/automation/posts/' + postId + '/publish/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/json'
            }
        }).then(response => response.json()).then(data => {
            if (data.success) {
                alert('Post enviado para publicação!');
                location.reload();
            } else {
                alert('Erro: ' + (data.error || 'Falha ao publicar'));
            }
        });
    }

    function openPostModal(postId) {
        document.getElementById('postModal').classList.add('active');
        document.getElementById('postModalContent').innerHTML = '<div class="text-center py-8"><p>Carregando...</p></div>';
        fetch('/automation/posts/' + postId + '/').then(r => r.text()).then(html => {
            document.getElementById('postModalContent').innerHTML = html;
        });
    }

    function closePostModal() {
        document.getElementById('postModal').classList.remove('active');
    }

    // Close modals on backdrop click
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
        backdrop.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
            }
        });
    });
</script>
{% endblock %}
'''

def main():
    with open(TEMPLATE_PATH, 'w', encoding='utf-8') as f:
        f.write(TEMPLATE_CONTENT)
    print(f'OK - Template rewritten: {TEMPLATE_PATH}')

if __name__ == '__main__':
    main()
