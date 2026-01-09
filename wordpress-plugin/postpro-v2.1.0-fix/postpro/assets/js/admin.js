/**
 * PostPro WordPress Plugin - Admin JavaScript
 */

(function ($) {
    'use strict';

    $(document).ready(function () {
        initTestConnection();
        initUploadForm();
        initCopyButtons();
        initSyncProfile();
        initEditorialPlan();
        initKeywordsForm();
    });

    // Test Connection
    function initTestConnection() {
        $('#postpro-test-connection').on('click', function () {
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

    // Upload Form
    function initUploadForm() {
        $('#postpro-upload-form').on('submit', function (e) {
            e.preventDefault();

            var $form = $(this);
            var $btn = $form.find('#postpro-submit-upload');
            var $progress = $('#postpro-upload-progress');
            var $result = $('#postpro-upload-result');

            var formData = new FormData(this);
            formData.append('action', 'postpro_upload_csv');
            formData.append('nonce', postproAdmin.nonce);

            $btn.prop('disabled', true).text('Enviando...');
            $progress.show();
            $result.hide();

            $.ajax({
                url: postproAdmin.ajaxUrl,
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function (response) {
                    if (response.success) {
                        var batchId = response.data.batch_id;
                        pollBatchStatus(batchId);
                    } else {
                        showError(response.data);
                    }
                },
                error: function () {
                    showError('Erro ao enviar arquivo');
                },
                complete: function () {
                    $btn.prop('disabled', false).text('Iniciar Processamento');
                }
            });
        });
    }

    // Poll Batch Status
    function pollBatchStatus(batchId) {
        var $progress = $('#postpro-upload-progress');
        var $progressBar = $progress.find('.postpro-progress-fill');
        var $progressText = $progress.find('.postpro-progress-text');
        var $result = $('#postpro-upload-result');

        $.ajax({
            url: postproAdmin.apiBase + '/batch/' + batchId + '/status',
            type: 'GET',
            headers: {
                'X-License-Key': $('[name="postpro_license_key"]').val() || ''
            },
            success: function (data) {
                $progressBar.css('width', data.progress + '%');
                $progressText.text(data.processed_rows + ' / ' + data.total_rows + ' keywords');

                if (data.status === 'completed') {
                    $progress.hide();

                    if (data.is_dry_run && data.simulation_report) {
                        showSimulationResult(data.simulation_report);
                    } else {
                        showSuccess('Processamento concluído! ' + data.processed_rows + ' posts gerados.');
                    }
                } else if (data.status === 'failed') {
                    $progress.hide();
                    showError(data.error || 'Processamento falhou');
                } else {
                    setTimeout(function () {
                        pollBatchStatus(batchId);
                    }, 2000);
                }
            },
            error: function () {
                setTimeout(function () {
                    pollBatchStatus(batchId);
                }, 3000);
            }
        });
    }

    function showSimulationResult(report) {
        var html = '<div class="postpro-simulation-results">';
        html += '<h4>Resultado da Simulação</h4>';
        html += '<div class="postpro-simulation-grid">';
        html += '<div class="postpro-simulation-item"><div class="value">' + report.total_posts + '</div><div class="label">Posts</div></div>';
        html += '<div class="postpro-simulation-item"><div class="value">' + formatNumber(report.total_tokens) + '</div><div class="label">Tokens</div></div>';
        html += '<div class="postpro-simulation-item"><div class="value">$' + parseFloat(report.total_cost).toFixed(4) + '</div><div class="label">Custo Est.</div></div>';
        html += '</div>';
        html += '</div>';

        $('#postpro-upload-result').removeClass('error').addClass('success').html(html).show();
    }

    function showSuccess(message) {
        $('#postpro-upload-result').removeClass('error').addClass('success').html('<strong>✓ ' + message + '</strong>').show();
    }

    function showError(message) {
        $('#postpro-upload-result').removeClass('success').addClass('error').html('<strong>✗ ' + message + '</strong>').show();
    }

    function formatNumber(n) {
        return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
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
        $('#postpro-sync-profile').on('click', function () {
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
                    if (response.data.has_plan) {
                        var plan = response.data.plan;
                        var items = response.data.items;

                        // Render Meta
                        var metaHtml = '<strong>Status:</strong> ' + plan.status_label +
                            ' | <strong>Início:</strong> ' + formatDate(plan.start_date);
                        $meta.html(metaHtml);

                        // Render Items
                        var html = '';
                        items.forEach(function (item) {
                            var statusClass = 'status-' + item.status.toLowerCase();
                            var scheduledDate = item.scheduled_date ? formatDate(item.scheduled_date) : '-';

                            html += '<tr>';
                            html += '<td>Dia ' + item.day + '</td>';
                            html += '<td><strong>' + (item.title || item.keyword) + '</strong><br><small>Foco: ' + item.keyword + '</small></td>';
                            html += '<td><span class="postpro-badge ' + statusClass + '">' + item.status_label + '</span></td>';
                            html += '<td>' + scheduledDate + '</td>';
                            html += '<td>';
                            if (item.post_id) {
                                html += '<a href="post.php?post=' + item.post_id + '&action=edit" class="button button-small" target="_blank">Ver Post</a>';
                            }
                            html += '</td>';
                            html += '</tr>';
                        });

                        $items.html(html);
                        $content.show();
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

    // Keywords Form Handler
    function initKeywordsForm() {
        $('#postpro-keywords-form').on('submit', function (e) {
            e.preventDefault();

            var $form = $(this);
            var $btn = $form.find('#postpro-save-keywords');
            var $result = $('#postpro-keywords-result');

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
        return date.toLocaleDateString('pt-BR');
    }

})(jQuery);
