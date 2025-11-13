/**
 * Neighbourhood Safety Application - Main JavaScript
 * Contains core functionality, utilities, and global event handlers
 */

// Global application state
const App = {
    initialized: false,
    currentUser: null,
    config: {
        apiTimeout: 30000,
        refreshInterval: 300000, // 5 minutes
        sessionWarning: 3600000, // 1 hour
        animationDuration: 300
    }
};

// Utility functions
const Utils = {
    /**
     * Format date for display
     */
    formatDate(dateString, format = 'relative') {
        if (!dateString) return '';

        const date = new Date(dateString);
        const now = new Date();

        if (format === 'relative') {
            const diff = now - date;

            if (diff < 60000) { // Less than 1 minute
                return 'Just now';
            } else if (diff < 3600000) { // Less than 1 hour
                const minutes = Math.floor(diff / 60000);
                return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
            } else if (diff < 86400000) { // Less than 1 day
                const hours = Math.floor(diff / 3600000);
                return `${hours} hour${hours > 1 ? 's' : ''} ago`;
            } else if (diff < 604800000) { // Less than 1 week
                const days = Math.floor(diff / 86400000);
                return `${days} day${days > 1 ? 's' : ''} ago`;
            } else {
                return date.toLocaleDateString();
            }
        } else if (format === 'short') {
            return date.toLocaleDateString();
        } else if (format === 'long') {
            return date.toLocaleDateString() + ' at ' + date.toLocaleTimeString();
        }

        return date.toLocaleDateString();
    },

    /**
     * Format phone number for display
     */
    formatPhoneNumber(phone) {
        if (!phone) return '';

        // Remove all non-digit characters
        const cleaned = phone.replace(/\D/g, '');

        // Format based on length
        if (cleaned.length === 10) {
            return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
        } else if (cleaned.length > 10) {
            // Handle country code
            if (cleaned.length === 11 && cleaned.startsWith('1')) {
                return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
            }
            return phone; // Return original if can't format
        }

        return phone;
    },

    /**
     * Validate email format
     */
    isValidEmail(email) {
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailPattern.test(email);
    },

    /**
     * Validate phone number format
     */
    isValidPhone(phone) {
        if (!phone) return true; // Optional field
        const phonePattern = /^[\d\s\-\+\(\)]+$/;
        return phonePattern.test(phone) && phone.replace(/\D/g, '').length >= 10;
    },

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Generate random ID
     */
    generateId() {
        return Math.random().toString(36).substr(2, 9);
    },

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            if (navigator.clipboard) {
                await navigator.clipboard.writeText(text);
                return true;
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                const result = document.execCommand('copy');
                document.body.removeChild(textArea);
                return result;
            }
        } catch (err) {
            console.error('Failed to copy text: ', err);
            return false;
        }
    },

    /**
     * Get CSRF token from meta tag or form
     */
    getCsrfToken() {
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        }

        const formInput = document.querySelector('input[name="csrf_token"]');
        if (formInput) {
            return formInput.value;
        }

        return null;
    }
};

// API utilities
const API = {
    /**
     * Make API request with error handling
     */
    async request(url, options = {}) {
        const config = {
            timeout: App.config.apiTimeout,
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            ...options
        };

        // Add CSRF token if available
        const csrfToken = Utils.getCsrfToken();
        if (csrfToken) {
            config.headers['X-CSRFToken'] = csrfToken;
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), config.timeout);
        config.signal = controller.signal;

        try {
            const response = await fetch(url, config);
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            clearTimeout(timeoutId);

            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }

            throw error;
        }
    },

    /**
     * GET request
     */
    async get(url, options = {}) {
        return this.request(url, { method: 'GET', ...options });
    },

    /**
     * POST request
     */
    async post(url, data = {}, options = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data),
            ...options
        });
    },

    /**
     * PUT request
     */
    async put(url, data = {}, options = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data),
            ...options
        });
    },

    /**
     * DELETE request
     */
    async delete(url, options = {}) {
        return this.request(url, { method: 'DELETE', ...options });
    }
};

// UI utilities
const UI = {
    /**
     * Show flash message
     */
    showFlash(message, type = 'info', duration = 5000) {
        const flashContainer = document.querySelector('.flash-messages');
        if (!flashContainer) {
            console.warn('Flash container not found');
            return;
        }

        const flashId = 'flash-' + Utils.generateId();
        const flashElement = document.createElement('div');
        flashElement.className = `flash-message flash-${type}`;
        flashElement.id = flashId;

        const iconMap = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };

        flashElement.innerHTML = `
            <div class="flash-content">
                <i class="fas fa-${iconMap[type] || 'info-circle'}"></i>
                <span>${message}</span>
                <button class="flash-close" onclick="UI.closeFlash('${flashId}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        flashContainer.appendChild(flashElement);

        // Auto-close after duration
        if (duration > 0) {
            setTimeout(() => this.closeFlash(flashId), duration);
        }

        return flashId;
    },

    /**
     * Close flash message
     */
    closeFlash(flashId) {
        const flashElement = document.getElementById(flashId);
        if (flashElement) {
            flashElement.style.animation = 'slideOutRight 0.3s ease forwards';
            setTimeout(() => {
                if (flashElement.parentNode) {
                    flashElement.parentNode.removeChild(flashElement);
                }
            }, 300);
        }
    },

    /**
     * Show modal
     */
    showModal(modalId, options = {}) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.warn(`Modal with id "${modalId}" not found`);
            return;
        }

        const modalContainer = modal.closest('.modal-container');
        if (modalContainer) {
            modalContainer.classList.add('show');

            // Set focus to first input
            const firstInput = modal.querySelector('input, textarea, select, button');
            if (firstInput && options.autoFocus !== false) {
                setTimeout(() => firstInput.focus(), 100);
            }

            // Add event listeners
            this.addModalEventListeners(modalContainer, options);

            return modalContainer;
        }
    },

    /**
     * Hide modal
     */
    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.warn(`Modal with id "${modalId}" not found`);
            return;
        }

        const modalContainer = modal.closest('.modal-container');
        if (modalContainer) {
            modalContainer.classList.remove('show');
            this.removeModalEventListeners(modalContainer);
        }
    },

    /**
     * Add modal event listeners
     */
    addModalEventListeners(modalContainer, options) {
        const closeOnEscape = (e) => {
            if (e.key === 'Escape') {
                this.hideModal(modalContainer.querySelector('.modal').id);
            }
        };

        const closeOnOverlay = (e) => {
            if (e.target === modalContainer || e.target.classList.contains('modal-overlay')) {
                this.hideModal(modalContainer.querySelector('.modal').id);
            }
        };

        modalContainer.addEventListener('keydown', closeOnEscape);
        modalContainer.addEventListener('click', closeOnOverlay);

        // Store listeners for removal
        modalContainer._modalListeners = {
            closeOnEscape,
            closeOnOverlay
        };
    },

    /**
     * Remove modal event listeners
     */
    removeModalEventListeners(modalContainer) {
        if (modalContainer._modalListeners) {
            modalContainer.removeEventListener('keydown', modalContainer._modalListeners.closeOnEscape);
            modalContainer.removeEventListener('click', modalContainer._modalListeners.closeOnOverlay);
            delete modalContainer._modalListeners;
        }
    },

    /**
     * Show loading overlay
     */
    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'flex';
            const messageElement = overlay.querySelector('p');
            if (messageElement) {
                messageElement.textContent = message;
            }
        }
    },

    /**
     * Hide loading overlay
     */
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    },

    /**
     * Animate number value
     */
    animateValue(elementId, start, end, duration = 1000) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                element.textContent = end.toLocaleString();
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current).toLocaleString();
            }
        }, 16);
    },

    /**
     * Smooth scroll to element
     */
    scrollToElement(elementId, offset = 0) {
        const element = document.getElementById(elementId);
        if (element) {
            const top = element.offsetTop - offset;
            window.scrollTo({
                top: top,
                behavior: 'smooth'
            });
        }
    },

    /**
     * Enable/disable button
     */
    setButtonState(buttonId, loading = false, text = null) {
        const button = document.getElementById(buttonId);
        if (!button) return;

        if (loading) {
            button.disabled = true;
            button.classList.add('loading');
            if (text) {
                button.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${text}`;
            }
        } else {
            button.disabled = false;
            button.classList.remove('loading');
            if (text) {
                button.innerHTML = text;
            }
        }
    }
};

// Form utilities
const Form = {
    /**
     * Validate form field
     */
    validateField(field, rules = {}) {
        const value = field.value.trim();
        const errors = [];

        // Required validation
        if (rules.required && !value) {
            errors.push('This field is required');
        }

        // Email validation
        if (rules.email && value && !Utils.isValidEmail(value)) {
            errors.push('Please enter a valid email address');
        }

        // Phone validation
        if (rules.phone && value && !Utils.isValidPhone(value)) {
            errors.push('Please enter a valid phone number');
        }

        // Min length validation
        if (rules.minLength && value.length < rules.minLength) {
            errors.push(`Must be at least ${rules.minLength} characters long`);
        }

        // Max length validation
        if (rules.maxLength && value.length > rules.maxLength) {
            errors.push(`Must be less than ${rules.maxLength} characters long`);
        }

        // Pattern validation
        if (rules.pattern && value && !rules.pattern.test(value)) {
            errors.push(rules.message || 'Invalid format');
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    },

    /**
     * Show field error
     */
    showFieldError(fieldId, message) {
        const field = document.getElementById(fieldId);
        const errorElement = document.getElementById(`${fieldId}-error`);

        if (field) {
            field.classList.add('error');
        }
        if (errorElement) {
            errorElement.textContent = message;
        }
    },

    /**
     * Clear field errors
     */
    clearFieldErrors(formId) {
        const form = document.getElementById(formId);
        if (!form) return;

        form.querySelectorAll('.form-input, .form-select, .form-textarea').forEach(input => {
            input.classList.remove('error');
        });

        form.querySelectorAll('.error-message').forEach(error => {
            error.textContent = '';
        });
    },

    /**
     * Serialize form data
     */
    serialize(formId) {
        const form = document.getElementById(formId);
        if (!form) return {};

        const formData = new FormData(form);
        const data = {};

        for (let [key, value] of formData.entries()) {
            // Handle checkboxes
            if (form.querySelector(`input[name="${key}"][type="checkbox"]`)) {
                data[key] = form.querySelector(`input[name="${key}"]:checked`) !== null;
            } else {
                data[key] = value.trim();
            }
        }

        return data;
    },

    /**
     * Reset form
     */
    reset(formId) {
        const form = document.getElementById(formId);
        if (form) {
            form.reset();
            this.clearFieldErrors(formId);
        }
    }
};

// Mobile menu functionality
const MobileMenu = {
    init() {
        const toggle = document.getElementById('mobile-menu-toggle');
        const menu = document.querySelector('.nav-menu');

        if (toggle && menu) {
            toggle.addEventListener('click', () => {
                menu.classList.toggle('active');
                toggle.classList.toggle('active');
            });

            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!toggle.contains(e.target) && !menu.contains(e.target)) {
                    menu.classList.remove('active');
                    toggle.classList.remove('active');
                }
            });

            // Close menu on window resize
            window.addEventListener('resize', () => {
                if (window.innerWidth > 768) {
                    menu.classList.remove('active');
                    toggle.classList.remove('active');
                }
            });
        }
    }
};

// Session management
const Session = {
    timeoutId: null,
    warningTimeoutId: null,

    init() {
        this.resetTimeout();
        this.setupEventListeners();
    },

    setupEventListeners() {
        // Reset timeout on user activity
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
        events.forEach(event => {
            document.addEventListener(event, () => this.resetTimeout(), true);
        });
    },

    resetTimeout() {
        clearTimeout(this.timeoutId);
        clearTimeout(this.warningTimeoutId);

        // Show warning 1 hour before timeout
        this.warningTimeoutId = setTimeout(() => {
            this.showWarning();
        }, App.config.sessionWarning);

        // Set actual timeout
        this.timeoutId = setTimeout(() => {
            this.handleTimeout();
        }, App.config.refreshInterval);
    },

    showWarning() {
        const confirmed = confirm('Your session will expire in 1 hour. Would you like to extend it?');
        if (confirmed) {
            this.extendSession();
        }
    },

    async extendSession() {
        try {
            const response = await API.get('/auth/extend-session');
            if (response.success) {
                UI.showFlash('Session extended successfully', 'success');
                this.resetTimeout();
            } else {
                UI.showFlash('Failed to extend session', 'error');
            }
        } catch (error) {
            console.error('Error extending session:', error);
            UI.showFlash('Error extending session', 'error');
        }
    },

    handleTimeout() {
        UI.showFlash('Your session has expired. Please log in again.', 'warning');
        setTimeout(() => {
            window.location.href = '/auth/login';
        }, 2000);
    }
};

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    // Initialize modules
    MobileMenu.init();
    Session.init();

    // Set global functions for template access
    window.showFlash = UI.showFlash.bind(UI);
    window.closeFlash = UI.closeFlash.bind(UI);
    window.showModal = UI.showModal.bind(UI);
    window.hideModal = UI.hideModal.bind(UI);
    window.showLoading = UI.showLoading.bind(UI);
    window.hideLoading = UI.hideLoading.bind(UI);

    // Mark app as initialized
    App.initialized = true;

    // Show any server-side flash messages
    const serverFlashMessages = document.querySelectorAll('.flash-message');
    serverFlashMessages.forEach((flash, index) => {
        setTimeout(() => {
            UI.closeFlash(flash.id);
        }, 5000 + (index * 1000)); // Stagger the removal
    });

    console.log('Neighbourhood Safety Application initialized');
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, pause any ongoing operations
        console.log('Page hidden - pausing operations');
    } else {
        // Page is visible again, resume operations
        console.log('Page visible - resuming operations');
        Session.resetTimeout();
    }
});

// Handle online/offline status
window.addEventListener('online', () => {
    UI.showFlash('Connection restored', 'success');
});

window.addEventListener('offline', () => {
    UI.showFlash('Connection lost. Some features may not be available.', 'warning');
});

// Error handling
window.addEventListener('error', (event) => {
    console.error('JavaScript error:', event.error);
    // Don't show user-facing errors for every JS error to avoid spam
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    // Show a generic error for unhandled promise rejections
    if (event.reason && event.reason.message) {
        UI.showFlash('An unexpected error occurred. Please try again.', 'error');
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        App,
        Utils,
        API,
        UI,
        Form,
        MobileMenu,
        Session
    };
}