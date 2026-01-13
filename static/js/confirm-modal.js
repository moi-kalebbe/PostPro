/**
 * Confirm Modal System
 * Substituição customizada para confirm() nativo do navegador
 * 
 * Uso:
 * const confirmed = await window.confirmAction({
 *   title: 'Confirmar Ação',
 *   message: 'Tem certeza que deseja continuar?',
 *   confirmText: 'Sim, continuar',
 *   cancelText: 'Cancelar',
 *   type: 'danger' // 'danger', 'warning', 'info'
 * });
 * 
 * if (confirmed) {
 *   // Executar ação
 * }
 */

(function () {
    'use strict';

    let currentModal = null;

    // Ícones para cada tipo de modal
    const modalIcons = {
        danger: '⚠',
        warning: '⚠',
        info: 'ℹ'
    };

    /**
     * Exibir modal de confirmação
     * @param {Object} options - Opções do modal
     * @returns {Promise<boolean>} - true se confirmado, false se cancelado
     */
    function confirmAction(options = {}) {
        return new Promise((resolve) => {
            // Prevenir múltiplos modais simultâneos
            if (currentModal) {
                console.warn('Já existe um modal de confirmação aberto.');
                resolve(false);
                return;
            }

            // Opções padrão
            const config = {
                title: options.title || 'Confirmar Ação',
                message: options.message || 'Tem certeza que deseja continuar?',
                confirmText: options.confirmText || 'Confirmar',
                cancelText: options.cancelText || 'Cancelar',
                type: options.type || 'warning' // 'danger', 'warning', 'info'
            };

            const icon = modalIcons[config.type] || modalIcons.warning;

            // Criar backdrop
            const backdrop = document.createElement('div');
            backdrop.className = 'confirm-modal-backdrop';

            // Criar modal
            const modal = document.createElement('div');
            modal.className = `confirm-modal ${config.type}`;

            modal.innerHTML = `
        <div class="confirm-modal-header">
          <div class="confirm-modal-icon">${icon}</div>
          <h3 class="confirm-modal-title">${escapeHtml(config.title)}</h3>
        </div>
        <div class="confirm-modal-body">
          <p class="confirm-modal-message">${escapeHtml(config.message)}</p>
        </div>
        <div class="confirm-modal-footer">
          <button class="btn btn-cancel" data-action="cancel">${escapeHtml(config.cancelText)}</button>
          <button class="btn btn-primary btn-confirm" data-action="confirm">${escapeHtml(config.confirmText)}</button>
        </div>
      `;

            backdrop.appendChild(modal);
            document.body.appendChild(backdrop);

            currentModal = backdrop;

            // Função para fechar modal
            function closeModal(confirmed) {
                backdrop.classList.remove('active');

                // Remover após animação
                setTimeout(() => {
                    if (backdrop.parentNode) {
                        backdrop.parentNode.removeChild(backdrop);
                    }
                    currentModal = null;
                    resolve(confirmed);
                }, 300); // Duração da animação
            }

            // Event listeners
            const cancelBtn = modal.querySelector('[data-action="cancel"]');
            const confirmBtn = modal.querySelector('[data-action="confirm"]');

            cancelBtn.addEventListener('click', () => closeModal(false));
            confirmBtn.addEventListener('click', () => closeModal(true));

            // Clicar no backdrop para cancelar
            backdrop.addEventListener('click', (e) => {
                if (e.target === backdrop) {
                    closeModal(false);
                }
            });

            // ESC para cancelar
            function handleEscape(e) {
                if (e.key === 'Escape') {
                    closeModal(false);
                    document.removeEventListener('keydown', handleEscape);
                }
            }

            document.addEventListener('keydown', handleEscape);

            // Enter para confirmar (quando botão de confirmar está focado)
            confirmBtn.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    closeModal(true);
                }
            });

            // Ativar modal com animação
            requestAnimationFrame(() => {
                backdrop.classList.add('active');
                // Focar no botão de cancelar por padrão (mais seguro)
                cancelBtn.focus();
            });
        });
    }

    /**
     * Escapar HTML para prevenir XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Métodos de conveniência para tipos específicos
     */
    function confirmDanger(title, message, confirmText = 'Sim, excluir') {
        return confirmAction({
            title,
            message,
            confirmText,
            cancelText: 'Cancelar',
            type: 'danger'
        });
    }

    function confirmWarning(title, message, confirmText = 'Sim, continuar') {
        return confirmAction({
            title,
            message,
            confirmText,
            cancelText: 'Cancelar',
            type: 'warning'
        });
    }

    function confirmInfo(title, message, confirmText = 'Confirmar') {
        return confirmAction({
            title,
            message,
            confirmText,
            cancelText: 'Cancelar',
            type: 'info'
        });
    }

    // Expor API globalmente
    window.confirmAction = confirmAction;
    window.confirmDanger = confirmDanger;
    window.confirmWarning = confirmWarning;
    window.confirmInfo = confirmInfo;

})();
