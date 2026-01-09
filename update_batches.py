import os

target_file = r'c:\Users\olx\OneDrive\Desktop\PROJETOS 2026\PostPro\templates\automation\batches_list.html'
temp_file = r'c:\Users\olx\OneDrive\Desktop\PROJETOS 2026\PostPro\templates\automation\batches_list_v2.html'

content = """{% extends 'base.html' %}
{% load static %}

{% block title %}Jobs - PostPro{% endblock %}

{% block sidebar %}
{% include 'components/sidebar.html' %}
{% endblock %}

{% block content %}
<div class="container">
    <div class="page-header">
        <h1 class="page-title">Jobs</h1>
    </div>

    <div class="card">
        <!-- Bulk Actions Bar -->
        <div class="card-header bulk-actions-bar" id="bulk-actions-bar" style="display: none;">
            <div class="flex items-center gap-4">
                <span class="text-sm"><span id="selected-count">0</span> job(s) selecionado(s)</span>
                <button type="button" class="btn btn-error btn-sm" onclick="bulkDeleteBatches()">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                    Deletar selecionados
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
                        <th>Projeto</th>
                        <th>Arquivo</th>
                        <th>Status</th>
                        <th>Progresso</th>
                        <th class="hidden-mobile">Custo Est.</th>
                        <th class="hidden-mobile">Tipo</th>
                        <th>Data</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    {% for batch in batches %}
                    <tr data-batch-id="{{ batch.id }}">
                        <td>
                            <input type="checkbox" class="batch-checkbox" value="{{ batch.id }}"
                                onchange="updateBulkBar()">
                        </td>
                        <td><strong>{{ batch.project.name }}</strong></td>
                        <td>
                            <span class="text-sm">{{ batch.original_filename|truncatechars:20 }}</span>
                        </td>
                        <td>
                            <span class="badge badge-{% if batch.status == 'completed' %}success{% elif batch.status == 'processing' %}info{% elif batch.status == 'failed' %}error{% else %}gray{% endif %}">{{ batch.get_status_display }}</span>
                        </td>
                        <td>
                            {% if batch.status == 'processing' %}
                            <div class="flex items-center gap-2">
                                <div class="progress" style="width: 80px;">
                                    <div class="progress-bar" style="width: {{ batch.progress_percent }}%"></div>
                                </div>
                                <span class="text-xs">{{ batch.progress_percent }}%</span>
                            </div>
                            {% else %}
                            {{ batch.processed_rows }} / {{ batch.total_rows }}
                            {% endif %}
                        </td>
                        <td class="hidden-mobile">
                            {% if batch.estimated_cost %}
                            ${{ batch.estimated_cost|floatformat:4 }}
                            {% else %}
                            -
                            {% endif %}
                        </td>
                        <td class="hidden-mobile">
                            {% if batch.is_dry_run %}
                            <span class="badge badge-warning">Simulação</span>
                            {% else %}
                            <span class="badge badge-gray">Real</span>
                            {% endif %}
                        </td>
                        <td class="text-muted">{{ batch.created_at|date:"d/m H:i" }}</td>
                        <td>
                            <button class="btn btn-ghost btn-sm text-error"
                                onclick="openDeleteModal('{{ batch.id }}', '{{ batch.project.name|escapejs }}')"
                                title="Deletar">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
                                    fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="3 6 5 6 21 6"></polyline>
                                    <path
                                        d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2">
                                    </path>
                                </svg>
                            </button>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="9">
                            <div class="empty-state">
                                <h3 class="empty-state-title">Nenhum job encontrado</h3>
                                <p class="empty-state-text">Faça upload de um CSV em um projeto.</p>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        {% if batches.has_other_pages %}
        <div class="card-footer">
            <div class="flex justify-center gap-2">
                {% if batches.has_previous %}
                <a href="?page={{ batches.previous_page_number }}" class="btn btn-secondary btn-sm">Anterior</a>
                {% endif %}
                <span class="btn btn-ghost btn-sm">Página {{ batches.number }} de {{ batches.paginator.num_pages }}</span>
                {% if batches.has_next %}
                <a href="?page={{ batches.next_page_number }}" class="btn btn-secondary btn-sm">Próxima</a>
                {% endif %}
            </div>
        </div>
        {% endif %}
    </div>
</div>

{% block extra_js %}
<script>
    // ========== DELETE FUNCTIONALITY ==========

    let deleteBatchId = null;

    function openDeleteModal(batchId, projectName) {
        deleteBatchId = batchId;
        document.getElementById('delete-batch-name').textContent = projectName;
        openModal('delete-modal');
    }

    async function confirmDeleteBatch() {
        if (!deleteBatchId) return;

        try {
            const response = await fetch('/automation/batches/' + deleteBatchId + '/delete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('postpro_csrftoken'),
                },
            });
            const data = await response.json();

            closeModal('delete-modal');

            if (data.success) {
                showToast(data.message, 'success');
                // Remove row from table
                const row = document.querySelector(`tr[data-batch-id="${deleteBatchId}"]`);
                if (row) row.remove();
            } else {
                showToast(data.message || 'Erro ao deletar', 'error');
            }
        } catch (error) {
            showToast('Erro: ' + error.message, 'error');
        }

        deleteBatchId = null;
    }

    // ========== BULK SELECTION ==========

    function toggleSelectAll(checkbox) {
        const checkboxes = document.querySelectorAll('.batch-checkbox');
        checkboxes.forEach(cb => cb.checked = checkbox.checked);
        updateBulkBar();
    }

    function updateBulkBar() {
        const checkboxes = document.querySelectorAll('.batch-checkbox:checked');
        const count = checkboxes.length;
        const bar = document.getElementById('bulk-actions-bar');
        const countSpan = document.getElementById('selected-count');

        if (count > 0) {
            bar.style.display = 'block';
            countSpan.textContent = count;
        } else {
            bar.style.display = 'none';
        }
    }

    function clearSelection() {
        const checkboxes = document.querySelectorAll('.batch-checkbox');
        checkboxes.forEach(cb => cb.checked = false);
        document.getElementById('select-all-checkbox').checked = false;
        updateBulkBar();
    }

    function getSelectedBatchIds() {
        const checkboxes = document.querySelectorAll('.batch-checkbox:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    async function bulkDeleteBatches() {
        const batchIds = getSelectedBatchIds();
        if (batchIds.length === 0) {
            showToast('Nenhum job selecionado', 'warning');
            return;
        }

        // Open bulk delete modal
        document.getElementById('bulk-delete-count').textContent = batchIds.length;
        openModal('bulk-delete-modal');
    }

    async function confirmBulkDelete() {
        const batchIds = getSelectedBatchIds();

        try {
            const response = await fetch('/automation/batches/bulk-delete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('postpro_csrftoken'),
                },
                body: JSON.stringify({
                    batch_ids: batchIds
                }),
            });
            const data = await response.json();

            closeModal('bulk-delete-modal');

            if (data.success) {
                showToast(data.message, 'success');

                // Remove rows from table
                batchIds.forEach(id => {
                    const row = document.querySelector(`tr[data-batch-id="${id}"]`);
                    if (row) row.remove();
                });

                clearSelection();
            } else {
                showToast(data.message || 'Erro ao deletar', 'error');
            }
        } catch (error) {
            showToast('Erro: ' + error.message, 'error');
        }
    }
</script>

<!-- Delete Confirmation Modal -->
<div class="modal-backdrop" id="delete-modal">
    <div class="modal" style="max-width: 450px;">
        <div class="modal-header">
            <h3 class="modal-title">Confirmar Exclusão</h3>
            <button class="modal-close" onclick="closeModal('delete-modal')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        </div>
        <div class="modal-body">
            <p>Tem certeza que deseja deletar o job do projeto "<strong id="delete-batch-name"></strong>"?</p>
            <p class="text-sm text-muted mt-2">Isso não apagará os posts gerados, apenas o histórico da importação.</p>
        </div>
        <div class="modal-footer">
            <button class="btn btn-ghost" onclick="closeModal('delete-modal')">Cancelar</button>
            <button class="btn btn-error" onclick="confirmDeleteBatch()">Deletar</button>
        </div>
    </div>
</div>

<!-- Bulk Delete Confirmation Modal -->
<div class="modal-backdrop" id="bulk-delete-modal">
    <div class="modal" style="max-width: 450px;">
        <div class="modal-header">
            <h3 class="modal-title">Deletar em Massa</h3>
            <button class="modal-close" onclick="closeModal('bulk-delete-modal')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        </div>
        <div class="modal-body">
            <p>Tem certeza que deseja deletar <strong id="bulk-delete-count">0</strong> job(s)?</p>
            <p class="text-sm text-muted mt-2">Isso não apagará os posts gerados, apenas o histórico das importações.</p>
        </div>
        <div class="modal-footer">
            <button class="btn btn-ghost" onclick="closeModal('bulk-delete-modal')">Cancelar</button>
            <button class="btn btn-error" onclick="confirmBulkDelete()">Deletar Todos</button>
        </div>
    </div>
</div>
{% endblock %}

{% endblock %}
"""

# Write to temp file
with open(temp_file, 'w', encoding='utf-8') as f:
    f.write(content)

# Force replace
if os.path.exists(target_file):
    os.remove(target_file)

os.rename(temp_file, target_file)
print(f"File replaced successfully. New size: {os.path.getsize(target_file)}")
