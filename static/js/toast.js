/**
 * Toast Notification System
 * Substituição customizada para alert() nativo do navegador
 * 
 * Uso:
 * window.showToast('Mensagem de sucesso!', 'success', 3000);
 * window.showToast('Erro ao processar', 'error', 5000);
 * window.showToast('Atenção necessária', 'warning', 4000);
 * window.showToast('Informação geral', 'info', 3000);
 */

(function() {
  'use strict';

  // Criar container de toasts se não existir
  function ensureToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  // Ícones para cada tipo de toast
  const toastIcons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  };

  /**
   * Exibir um toast
   * @param {string} message - Mensagem a ser exibida
   * @param {string} type - Tipo: 'success', 'error', 'warning', 'info'
   * @param {number} duration - Duração em ms (padrão: 5000)
   */
  function showToast(message, type = 'info', duration = 5000) {
    const container = ensureToastContainer();
    
    // Criar elemento do toast
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = toastIcons[type] || toastIcons.info;
    
    toast.innerHTML = `
      <div class="toast-icon">${icon}</div>
      <div class="toast-content">
        <p class="toast-message">${escapeHtml(message)}</p>
      </div>
      <button class="toast-close" aria-label="Fechar">×</button>
      <div class="toast-progress" style="animation-duration: ${duration}ms;"></div>
    `;
    
    // Adicionar ao container
    container.appendChild(toast);
    
    // Botão de fechar
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => removeToast(toast));
    
    // Auto-remover após duração
    const timeoutId = setTimeout(() => {
      removeToast(toast);
    }, duration);
    
    // Permitir que o usuário pause o auto-dismiss ao passar o mouse
    toast.addEventListener('mouseenter', () => {
      clearTimeout(timeoutId);
      const progress = toast.querySelector('.toast-progress');
      if (progress) {
        progress.style.animationPlayState = 'paused';
      }
    });
    
    toast.addEventListener('mouseleave', () => {
      const timeoutId = setTimeout(() => {
        removeToast(toast);
      }, 1000); // Dar 1 segundo extra após o mouse sair
    });
    
    return toast;
  }

  /**
   * Remover um toast com animação
   */
  function removeToast(toast) {
    toast.classList.add('removing');
    
    // Remover após animação
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300); // Duração da animação slideOutRight
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
   * Limpar todos os toasts
   */
  function clearAllToasts() {
    const container = document.getElementById('toast-container');
    if (container) {
      const toasts = container.querySelectorAll('.toast');
      toasts.forEach(removeToast);
    }
  }

  // Expor API globalmente
  window.showToast = showToast;
  window.clearAllToasts = clearAllToasts;

  // Métodos de conveniência
  window.showSuccessToast = (msg, duration) => showToast(msg, 'success', duration);
  window.showErrorToast = (msg, duration) => showToast(msg, 'error', duration);
  window.showWarningToast = (msg, duration) => showToast(msg, 'warning', duration);
  window.showInfoToast = (msg, duration) => showToast(msg, 'info', duration);

})();
