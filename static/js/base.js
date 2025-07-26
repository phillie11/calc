/**
 * base.js
 * Provides common functionality across all pages
 */

document.addEventListener('DOMContentLoaded', function() {
    // Setup bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

document.addEventListener('DOMContentLoaded', function() {
    // Setup bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });


    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-danger)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-danger)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Handle dark/light theme toggle if present
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('light-theme');
            
            // Store theme preference
            const currentTheme = document.body.classList.contains('light-theme') ? 'light' : 'dark';
            localStorage.setItem('theme', currentTheme);
        });
        
        // Check for saved theme preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'light') {
            document.body.classList.add('light-theme');
        }
    }
    
    // Format number inputs to display appropriate decimal places
    document.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('change', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                const step = parseFloat(this.step) || 1;
                let decimalPlaces = 0;
                
                // Determine decimal places from step
                if (step < 1) {
                    const stepStr = step.toString();
                    decimalPlaces = stepStr.includes('.') ? 
                        stepStr.split('.')[1].length : 0;
                }
                
                // Update with formatted value
                if (decimalPlaces > 0) {
                    this.value = value.toFixed(decimalPlaces);
                }
            }
        });
    });
});

/**
 * Create a notification toast
 * @param {string} title - The toast title
 * @param {string} message - The toast message
 * @param {string} type - The type of toast ('success', 'info', 'warning', 'error')
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showToast(title, message, type = 'info', duration = 3000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="${duration}">
            <div class="toast-header bg-${getBootstrapType(type)} text-white">
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body bg-dark text-light">
                ${message}
            </div>
        </div>
    `;
    
    // Add toast to container
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Show the toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Remove toast after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

/**
 * Convert notification type to Bootstrap class
 * @param {string} type - The notification type
 * @returns {string} - Bootstrap class name
 */
function getBootstrapType(type) {
    switch (type.toLowerCase()) {
        case 'success':
            return 'success';
        case 'info':
            return 'info';
        case 'warning':
            return 'warning';
        case 'error':
            return 'danger';
        default:
            return 'primary';
    }
}

/**
 * Format a number with appropriate decimal places
 * @param {number} value - The number to format
 * @param {number} decimals - Number of decimal places 
 * @returns {string} - Formatted number
 */
function formatNumber(value, decimals = 2) {
    return Number(value).toFixed(decimals);
}
function debugCSRF() {
    // Check if CSRF token is available
    const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    
    if (!csrfTokenElement) {
        console.error('CSRF token not found in page!');
        return false;
    } else {
        console.log('CSRF token found:', csrfTokenElement.value.substring(0, 6) + '...');
        return true;
    }
}

// Call this function when the page loads
document.addEventListener('DOMContentLoaded', function() {
    debugCSRF();
});