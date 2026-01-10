/**
 * PostPro Main JavaScript
 */

// Theme Toggle
// Theme Toggle
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateLogo(savedTheme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const newTheme = current === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Update Logo
    updateLogo(newTheme);

    // Update Cookie for backend
    document.cookie = `theme=${newTheme};path=/;max-age=31536000`; // 1 year
}

function updateLogo(theme) {
    const logos = document.querySelectorAll('.brand-logo');

    logos.forEach(logo => {
        // Theme Light -> Logo Light (Dark Color)
        // Theme Dark -> Logo Dark (Light Color)
        const newSrc = theme === 'light' ? logo.dataset.logoLight : logo.dataset.logoDark;

        console.log(`Updating logo [${logo.id || 'class'}] to theme ${theme}:`, newSrc);

        if (newSrc && newSrc !== 'None' && newSrc !== '') {
            logo.src = newSrc;
        }
    });
}

// Initialize on load
document.addEventListener('DOMContentLoaded', initTheme);

// Mobile Sidebar Toggle
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('open');
}

// Modal Functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Close modal on backdrop click
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('modal-backdrop')) {
        e.target.classList.remove('active');
        document.body.style.overflow = '';
    }
});

// Close modal on Escape key
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        const activeModal = document.querySelector('.modal-backdrop.active');
        if (activeModal) {
            activeModal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
});

// File Upload
function initFileUpload() {
    const fileUploads = document.querySelectorAll('.file-upload');

    fileUploads.forEach(upload => {
        const input = upload.querySelector('input[type="file"]');

        upload.addEventListener('click', () => input.click());

        upload.addEventListener('dragover', (e) => {
            e.preventDefault();
            upload.classList.add('drag-over');
        });

        upload.addEventListener('dragleave', () => {
            upload.classList.remove('drag-over');
        });

        upload.addEventListener('drop', (e) => {
            e.preventDefault();
            upload.classList.remove('drag-over');

            if (e.dataTransfer.files.length) {
                input.files = e.dataTransfer.files;
                input.dispatchEvent(new Event('change'));
            }
        });

        input.addEventListener('change', () => {
            if (input.files.length) {
                const fileName = input.files[0].name;
                const textEl = upload.querySelector('.file-upload-text');
                if (textEl) {
                    textEl.textContent = fileName;
                }
                upload.classList.add('has-file');
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', initFileUpload);

// Artifact Accordion
function toggleArtifact(element) {
    const artifact = element.closest('.artifact');
    artifact.classList.toggle('open');
}

// Copy to Clipboard
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        setTimeout(() => {
            button.textContent = originalText;
        }, 2000);
    });
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.cssText = 'margin-bottom: 0.5rem; animation: slideIn 0.3s ease;';
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = 'position: fixed; top: 1rem; right: 1rem; z-index: 1100; width: 320px;';
    document.body.appendChild(container);
    return container;
}

// Confirm Dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// AJAX Helper
async function apiRequest(url, options = {}) {
    const defaults = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('postpro_csrftoken'),
        },
    };

    const config = {
        ...defaults,
        ...options,
        headers: { ...defaults.headers, ...options.headers },
    };

    try {
        const response = await fetch(url, config);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || data.message || 'Request failed');
        }

        return data;
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
}

// Get CSRF Token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Poll for Batch Status
function pollBatchStatus(batchId, callback, interval = 2000) {
    const poll = async () => {
        try {
            const data = await apiRequest(`/automation/batches/${batchId}/status/`);
            callback(data);

            if (data.status === 'processing') {
                setTimeout(poll, interval);
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    };

    poll();
}

// Format Currency
function formatCurrency(value, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 4,
    }).format(value);
}

// Format Number
function formatNumber(value) {
    return new Intl.NumberFormat().format(value);
}

// Debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize Search with Debounce
function initSearch() {
    const searchInputs = document.querySelectorAll('[data-search]');

    searchInputs.forEach(input => {
        const form = input.closest('form');

        input.addEventListener('input', debounce(() => {
            if (form) {
                form.submit();
            }
        }, 500));
    });
}

document.addEventListener('DOMContentLoaded', initSearch);
