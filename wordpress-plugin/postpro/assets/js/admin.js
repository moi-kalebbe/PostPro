/**
 * PostPro WordPress Plugin - Admin JavaScript
 */

(function ($) {
    'use strict';

    $(document).ready(function () {
        console.log('PostPro Admin JS v2.3.0 loaded');
        initTestConnection();
        initCopyButtons();
        initSyncProfile();
        initEditorialPlan();
        initKeywordsForm();
    });

    // Test Connection
    function initTestConnection() {
        $('#postpro-test-connection').on('click', function (e) {
            e.preventDefault();
            console.log('Test Connection clicked');
            var $btn = $(this);
            var $result = $('#postpro-connection-result');

            $btn.prop('disabled', true).text('Testando...');
            $result.hide();

            $.ajax({
                url: postproAdmin.ajaxUrl,
                type: 'POST',
                data: {
                    action: 'postpro_test_connection',
                    nonce: postproAdmin.nonce
                },
                success: function (response) {
                    if (response.success) {
                        $result.removeClass('error').addClass('success');
                        var html = '<strong>✓ ' + response.data.message + '</strong>';
                        if (response.data.project) {
                            html += '<br>Projeto: ' + response.data.project.name;
                        }
                        if (response.data.agency) {
                            html += '<br>Agência: ' + response.data.agency.name;
                        }
                        $result.html(html).show();
                    } else {
                        $result.removeClass('success').addClass('error');
                        $result.html('<strong>✗ Erro:</strong> ' + response.data).show();
                    }
                },
                error: function () {
                    $result.removeClass('success').addClass('error');
                    $result.html('<strong>✗ Erro de conexão</strong>').show();
                },
                complete: function () {
                    $btn.prop('disabled', false).text('Testar Conexão');
                }
            });
        });
    }

    // Copy Buttons
    function initCopyButtons() {
        $('.postpro-copy-btn').on('click', function () {
            var $btn = $(this);
            var text = $btn.data('copy');

            navigator.clipboard.writeText(text).then(function () {
                var originalText = $btn.text();
                $btn.text('Copiado!');
                setTimeout(function () {
                    $btn.text(originalText);
                }, 2000);
            });
        });
    }

    // Sync Profile
    function initSyncProfile() {
        $('#postpro-sync-profile').on('click', function (e) {
            e.preventDefault();
            console.log('Sync Profile clicked');
            var $btn = $(this);
            var $result = $('#postpro-sync-result');

            $btn.prop('disabled', true).html('<span class="dashicons dashicons-update" style="animation: spin 2s linear infinite;"></span> Sincronizando...');
            $result.hide();

            $.ajax({
                url: postproAdmin.ajaxUrl,
                type: 'POST',
                data: {
                    action: 'postpro_sync_profile',
                    nonce: postproAdmin.nonce
                },
                success: function (response) {
                    if (response.success) {
                        $result.removeClass('error').addClass('success')
                            .html('<strong>✓ Sincronização iniciada!</strong> O processo ocorrerá em segundo plano.').show();
                    } else {
                        $result.removeClass('success').addClass('error')
                            .html('<strong>✗ Erro:</strong> ' + (response.data || 'Falha desconhecida')).show();
                    }
                },
                error: function () {
                    $result.removeClass('success').addClass('error')
                        .html('<strong>✗ Erro de conexão</strong>').show();
                },
                complete: function () {
                    $btn.prop('disabled', false).html('<span class="dashicons dashicons-update" style="vertical-align: text-bottom;"></span> Sincronizar Perfil do Site');
                }
            });
        });
    }

    // Editorial Plan
    function initEditorialPlan() {
        var $container = $('#postpro-plan-content');
        if (!$container.length) return;

        loadEditorialPlan();

        $('#postpro-refresh-plan').on('click', function () {
            loadEditorialPlan();
        });
    }

    function loadEditorialPlan() {
        var $loading = $('#postpro-plan-loading');
        var $content = $('#postpro-plan-content');
        var $empty = $('#postpro-plan-empty');
        var $error = $('#postpro-plan-error');
        var $items = $('#postpro-plan-items');
        var $meta = $('#postpro-plan-meta');

        $loading.show();
        $content.hide();
        $empty.hide();
        $error.hide();

        $.ajax({
            url: postproAdmin.ajaxUrl,
            type: 'POST', // POST to keep consistent with others, though GET logic in PHP
            data: {
                action: 'postpro_get_plan',
                nonce: postproAdmin.nonce
            },
            success: function (response) {
                if (response.success) {
                    var plan = response.data.plan;
                    // Treat 'rejected' or 'failed' as no plan so user can regenerate
                    var showPlan = response.data.has_plan &&
                        plan.status !== 'rejected' &&
                        plan.status !== 'failed';

                    if (showPlan) {
                        var items = response.data.items;

                        // ACTION BUTTONS HEADER
                        var $actionsContainer = $('#postpro-plan-actions');
                        if ($actionsContainer.length === 0) {
                            $content.before('<div id="postpro-plan-actions" style="margin-bottom: 15px;"></div>');
                            $actionsContainer = $('#postpro-plan-actions');
                        }

                        // Check if we have pending items to show global actions
                        var hasPending = items.some(function (i) { return i.status === 'pending'; });

                        var actionsHtml = '';
                        actionsHtml += '<button type="button" id="postpro-refresh-plan" class="button button-secondary">Atualizar Lista</button> ';

                        if (hasPending) {
                            actionsHtml += '<button type="button" id="postpro-approve-all" class="button button-primary">Aprovar Tudo</button> ';
                            actionsHtml += '<button type="button" id="postpro-reject-plan" class="button button-link-delete" style="color: #a00; text-decoration: none;">Reprovar e Regenerar</button>';
                        }
                        $actionsContainer.html(actionsHtml);

                        // Re-bind Refresh in this scope
                        $('#postpro-refresh-plan').off('click').on('click', function () {
                            loadEditorialPlan();
                        });

                        // Bind Global Actions
                        $('#postpro-approve-all').off('click').on('click', handleApproveAll);
                        $('#postpro-reject-plan').off('click').on('click', handleRejectPlan);

                        // Render Meta
                        var metaHtml = '<strong>Status:</strong> ' + plan.status_label +
                            ' | <strong>Início:</strong> ' + formatDate(plan.start_date);
                        $meta.html(metaHtml);

                        // Render Items
                        var html = '';
                        items.forEach(function (item) {
                            var statusClass = 'status-' + item.status.toLowerCase();
                            var scheduledDate = item.scheduled_date ? formatDate(item.scheduled_date) : '-';
                            var isPending = item.status === 'pending';

                            html += '<tr data-id="' + item.id + '">';
                            html += '<td>Dia ' + item.day + '</td>';

                            // Editable Title Cell
                            html += '<td class="column-title">';
                            html += '<div class="display-mode">';
                            html += '<strong>' + (item.title || item.keyword) + '</strong><br><small>Foco: ' + item.keyword + '</small>';
                            html += '</div>';
                            if (isPending) {
                                html += '<div class="edit-mode" style="display:none;">';
                                html += '<input type="text" class="edit-title regular-text" value="' + (item.title || '') + '" placeholder="Título">';
                                html += '<input type="text" class="edit-keyword regular-text" value="' + item.keyword + '" placeholder="Palavra-chave">';
                                html += '<div style="margin-top: 5px;">';
                                html += '<button type="button" class="button button-small save-item-btn">Salvar</button> ';
                                html += '<button type="button" class="button button-small cancel-item-btn">Cancelar</button>';
                                html += '</div>';
                                html += '</div>';
                            }
                            html += '</td>';

                            html += '<td><span class="postpro-badge ' + statusClass + '">' + item.status_label + '</span></td>';
                            html += '<td>' + scheduledDate + '</td>';

                            html += '<td>';
                            if (item.post_id) {
                                html += '<a href="post.php?post=' + item.post_id + '&action=edit" class="button button-small" target="_blank">Ver Post</a>';
                            } else if (isPending) {
                                html += '<button type="button" class="button button-small approve-item-btn" data-id="' + item.id + '">Aprovar</button> ';
                                html += '<button type="button" class="button button-small edit-item-btn">Editar</button>';
                            }
                            html += '</td>';
                            html += '</tr>';
                        });

                        $items.html(html);
                        $content.show();

                        // Bind Item Actions
                        $('.approve-item-btn').on('click', handleApproveItem);
                        $('.edit-item-btn').on('click', function () {
                            var $row = $(this).closest('tr');
                            $row.find('.display-mode').hide();
                            $row.find('.edit-mode').show();
                            $(this).hide();
                            $row.find('.approve-item-btn').hide();
                        });

                        $('.cancel-item-btn').on('click', function () {
                            var $row = $(this).closest('tr');
                            $row.find('.edit-mode').hide();
                            $row.find('.display-mode').show();
                            $row.find('.edit-item-btn').show();
                            $row.find('.approve-item-btn').show();
                        });

                        $('.save-item-btn').on('click', handleUpdateItem);

                    } else {
                        $empty.show();
                    }
                } else {
                    $error.html('Erro ao carregar plano: ' + (response.data || 'Desconhecido')).show();
                }
            },
            error: function () {
                $error.html('Erro de conexão ao carregar plano').show();
            },
            complete: function () {
                $loading.hide();
            }
        });
    }

    // =========================================================================
    // Action Handlers
    // =========================================================================

    function handleApproveItem() {
        var $btn = $(this);
        var id = $btn.data('id');

        $btn.prop('disabled', true).text('...');

        $.ajax({
            url: postproAdmin.ajaxUrl,
            type: 'POST',
            data: {
                action: 'postpro_approve_item',
                nonce: postproAdmin.nonce,
                item_id: id
            },
            success: function (response) {
                if (response.success) {
                    // Update UI immediately for "perceptual speed"
                    var $row = $btn.closest('tr');
                    $row.find('.postpro-badge').removeClass('status-pending').addClass('status-scheduled').text('Scheduled');
                    $btn.parent().html('<em>Processando...</em>');
                } else {
                    alert('Erro: ' + (response.data || 'Falha ao aprovar'));
                    $btn.prop('disabled', false).text('Aprovar');
                }
            },
            error: function () {
                alert('Erro de conexão');
                $btn.prop('disabled', false).text('Aprovar');
            }
        });
    }

    function handleUpdateItem() {
        var $btn = $(this);
        var $row = $btn.closest('tr');
        var id = $row.data('id');

        var title = $row.find('.edit-title').val();
        var keyword = $row.find('.edit-keyword').val();

        $btn.prop('disabled', true).text('Saved...');

        $.ajax({
            url: postproAdmin.ajaxUrl,
            type: 'POST',
            data: {
                action: 'postpro_update_item',
                nonce: postproAdmin.nonce,
                item_id: id,
                title: title,
                keyword_focus: keyword
            },
            success: function (response) {
                if (response.success) {
                    // Update display mode
                    var displayHtml = '<strong>' + (title || keyword) + '</strong><br><small>Foco: ' + keyword + '</small>';
                    $row.find('.display-mode').html(displayHtml);

                    // Reset UI
                    $row.find('.edit-mode').hide();
                    $row.find('.display-mode').show();
                    $row.find('.edit-item-btn').show();
                    $row.find('.approve-item-btn').show();
                } else {
                    alert('Erro ao salvar: ' + response.data);
                }
            },
            complete: function () {
                $btn.prop('disabled', false).text('Salvar');
            }
        });
    }

    function handleApproveAll() {
        if (!confirm('Tem certeza que deseja aprovar todos os itens pendentes?')) return;

        var $btn = $('#postpro-approve-all');
        $btn.prop('disabled', true).text('Aprovando...');

        $.ajax({
            url: postproAdmin.ajaxUrl,
            type: 'POST',
            data: {
                action: 'postpro_approve_all',
                nonce: postproAdmin.nonce
            },
            success: function (response) {
                if (response.success) {
                    loadEditorialPlan(); // Refresh list
                } else {
                    alert('Erro: ' + response.data);
                    $btn.prop('disabled', false).text('Aprovar Tudo');
                }
            }
        });
    }

    function handleRejectPlan() {
        if (!confirm('ATENÇÃO: Isso irá descartar o plano atual e gerar novas ideias.\n\nOs tópicos atuais serão evitados no futuro.\n\nDeseja continuar?')) return;

        var $btn = $('#postpro-reject-plan');
        $btn.prop('disabled', true).text('Regenerando...');
        $('#postpro-plan-content').css('opacity', '0.5');

        $.ajax({
            url: postproAdmin.ajaxUrl,
            type: 'POST',
            data: {
                action: 'postpro_reject_plan',
                nonce: postproAdmin.nonce
            },
            success: function (response) {
                if (response.success) {
                    // Poll for new plan status or simply refresh
                    // For now, reload plan which might show "No items" until generation finishes
                    // Better to show a message "Generating new plan..."
                    $('#postpro-plan-content').html('<div class="notice notice-info inline"><p><strong>Gerando novo plano editorial...</strong><br>Isso pode levar alguns minutos. <a href="#" id="postpro-refresh-generated">Atualizar</a></p></div>');
                    $('#postpro-refresh-generated').on('click', function (e) {
                        e.preventDefault();
                        loadEditorialPlan();
                    });
                } else {
                    alert('Erro: ' + response.data);
                    $btn.prop('disabled', false).text('Reprovar e Regenerar');
                    $('#postpro-plan-content').css('opacity', '1');
                }
            }
        });
    }

    // Keywords Form Handler
    function initKeywordsForm() {
        var $forms = $('#postpro-keywords-form, #postpro-keywords-form-settings');

        $forms.on('submit', function (e) {
            e.preventDefault();

            var $form = $(this);
            var isSettings = $form.attr('id') === 'postpro-keywords-form-settings';
            var $btn = isSettings ? $('#postpro-save-keywords-settings') : $('#postpro-save-keywords');
            var $result = isSettings ? $('#postpro-keywords-result-settings') : $('#postpro-keywords-result');

            var keywordsValues = $form.find('input[name="keywords[]"]').map(function () {
                return $(this).val().trim();
            }).get().filter(function (val) {
                return val !== '';
            });

            if (keywordsValues.length < 5) {
                alert('Por favor, preencha pelo menos 5 palavras-chave.');
                return;
            }

            $btn.prop('disabled', true).text('Processando...');
            $result.hide();

            var data = {
                action: 'postpro_save_keywords',
                nonce: postproAdmin.nonce,
                keywords: keywordsValues
            };

            $.ajax({
                url: postproAdmin.ajaxUrl,
                type: 'POST',
                data: data,
                success: function (response) {
                    if (response.success) {
                        $result.removeClass('error').addClass('success')
                            .html('<strong>✓ Sucesso!</strong> Plano Editorial sendo gerado. Redirecionando...').show();

                        setTimeout(function () {
                            window.location.href = 'admin.php?page=postpro-editorial';
                        }, 2000);
                    } else {
                        $result.removeClass('success').addClass('error')
                            .html('<strong>✗ Erro:</strong> ' + (response.data || 'Erro desconhecido')).show();
                        $btn.prop('disabled', false).text('Salvar e Gerar Plano Editorial');
                    }
                },
                error: function () {
                    $result.removeClass('success').addClass('error')
                        .html('<strong>✗ Erro de conexão</strong>').show();
                    $btn.prop('disabled', false).text('Salvar e Gerar Plano Editorial');
                }
            });
        });
    }

    function formatDate(dateString) {
        if (!dateString) return '';
        var date = new Date(dateString);
        // Fix timezone offset issue manually or just use substring
        // Simple fix: append T00:00:00 if missing time to ensure local date interpretation
        if (dateString.indexOf('T') === -1) dateString += 'T12:00:00';
        date = new Date(dateString);
        return date.toLocaleDateString('pt-BR');
    }

})(jQuery);
