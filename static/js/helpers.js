/**
 * VenueHunt Helper Functions
 * Common JavaScript functions used across the application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    enableFormValidation();
    
    // Enable tooltips
    enableTooltips();
    
    // Enable dismissible alerts
    setupDismissibleAlerts();
    
    // Handle back-to-top button
    setupBackToTopButton();
    
    // Handle image preview on upload
    setupImagePreview();
    
    // Confirm dangerous actions
    setupConfirmActions();
});

/**
 * Enable Bootstrap form validation
 */
function enableFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Enable Bootstrap tooltips
 */
function enableTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

/**
 * Setup dismissible alerts with auto-dismiss
 */
function setupDismissibleAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.persistent)');
    
    alerts.forEach(alert => {
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });
}

/**
 * Create and handle back-to-top button
 */
function setupBackToTopButton() {
    // Create the button if it doesn't exist
    if (!document.querySelector('.back-to-top-btn')) {
        const button = document.createElement('button');
        button.classList.add('back-to-top-btn');
        button.innerHTML = '<i class="fas fa-chevron-up"></i>';
        document.body.appendChild(button);
        
        // Show/hide based on scroll position
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                button.classList.add('visible');
            } else {
                button.classList.remove('visible');
            }
        });
        
        // Scroll to top when clicked
        button.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
}

/**
 * Handle image preview on upload
 */
function setupImagePreview() {
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    
    imageInputs.forEach(input => {
        const previewId = input.dataset.preview;
        if (previewId) {
            const previewElement = document.getElementById(previewId);
            
            if (previewElement) {
                input.addEventListener('change', function() {
                    if (input.files && input.files[0]) {
                        const reader = new FileReader();
                        
                        reader.onload = function(e) {
                            previewElement.src = e.target.result;
                        };
                        
                        reader.readAsDataURL(input.files[0]);
                    }
                });
            }
        }
    });
}

/**
 * Setup confirmation for dangerous actions
 */
function setupConfirmActions() {
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.dataset.confirm || 'Are you sure you want to proceed?';
            
            if (!confirm(message)) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    });
}

/**
 * Format currency
 * @param {number} amount - The amount to format
 * @param {string} currency - The currency code (default: INR)
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount, currency = 'INR') {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * Format date
 * @param {string|Date} date - The date to format
 * @param {string} format - The format to use (default: 'long')
 * @returns {string} Formatted date string
 */
function formatDate(date, format = 'long') {
    const dateObj = date instanceof Date ? date : new Date(date);
    
    const options = {
        long: { year: 'numeric', month: 'long', day: 'numeric' },
        short: { year: 'numeric', month: 'short', day: 'numeric' },
        time: { hour: '2-digit', minute: '2-digit' }
    };
    
    return dateObj.toLocaleDateString('en-IN', options[format] || options.long);
}

/**
 * Truncate text with ellipsis
 * @param {string} text - The text to truncate
 * @param {number} length - Maximum length
 * @returns {string} Truncated text
 */
function truncateText(text, length = 100) {
    if (text.length <= length) return text;
    return text.substring(0, length) + '...';
}

/**
 * Debounce function for search inputs
 * @param {Function} func - The function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait = 300) {
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
