// Create a new file: static/js/reset-handler.js

document.addEventListener('DOMContentLoaded', function() {
    // Find the reset button in the modal
    const resetBtn = document.getElementById('confirmResetBtn');
    if (!resetBtn) {
        console.log('Reset button not found');
        return;
    }

    resetBtn.addEventListener('click', function() {
        console.log('Reset button clicked');
        
        // Create and submit a form programmatically
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/spring-calculator/reset-all-data/';
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        // Add redirect URL
        const redirectInput = document.createElement('input');
        redirectInput.type = 'hidden';
        redirectInput.name = 'redirect_url';
        redirectInput.value = window.location.pathname;
        form.appendChild(redirectInput);
        
        // Add the form to the document and submit it
        document.body.appendChild(form);
        form.submit();
    });
});