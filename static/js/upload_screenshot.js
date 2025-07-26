/**
 * upload_screenshot.js
 * Handles file uploads and previews for screenshots
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const form = document.getElementById('screenshotForm');
    const processBtn = document.getElementById('processBtn');
    const processSpinner = document.getElementById('processSpinner');
    
    // Setup file upload areas
    setupFileUpload('suspensionScreenshot', 'suspensionDropArea', 'suspensionPreview');
    setupFileUpload('powerScreenshot', 'powerDropArea', 'powerPreview');
    setupFileUpload('transmissionScreenshot', 'transmissionDropArea', 'transmissionPreview');
    
    // Handle form submission
    if (form) {
        form.addEventListener('submit', function(e) {
            // Check if at least one file and vehicle is selected
            const vehicle = document.getElementById('vehicle').value;
            const suspensionFile = document.getElementById('suspensionScreenshot').files[0];
            const powerFile = document.getElementById('powerScreenshot').files[0];
            const transmissionFile = document.getElementById('transmissionScreenshot').files[0];
            
            if (!vehicle) {
                e.preventDefault();
                alert('Please select a vehicle before proceeding.');
                return;
            }
            
            if (!suspensionFile && !powerFile && !transmissionFile) {
                e.preventDefault();
                alert('Please upload at least one screenshot.');
                return;
            }
            
            // Show loading spinner
            if (processBtn && processSpinner) {
                processBtn.disabled = true;
                processSpinner.classList.remove('d-none');
                processBtn.textContent = ' Processing...';
                processBtn.prepend(processSpinner);
            }
        });
    }
    
    // Setup remove preview buttons
    document.querySelectorAll('.remove-preview').forEach(button => {
        button.addEventListener('click', function() {
            const previewDiv = this.closest('[id$="Preview"]');
            const inputId = previewDiv.id.replace('Preview', 'Screenshot');
            const input = document.getElementById(inputId);
            
            if (input) {
                input.value = '';
            }
            
            previewDiv.classList.add('d-none');
            previewDiv.querySelector('img').src = '';
        });
    });
});

/**
 * Set up drag and drop file upload for a specific input
 * @param {string} inputId - ID of the file input
 * @param {string} dropAreaId - ID of the drop area
 * @param {string} previewId - ID of the preview container
 */
function setupFileUpload(inputId, dropAreaId, previewId) {
    const fileInput = document.getElementById(inputId);
    const dropArea = document.getElementById(dropAreaId);
    const previewContainer = document.getElementById(previewId);
    
    if (!fileInput || !dropArea || !previewContainer) {
        return;
    }
    
    // Handle click on drop area
    dropArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Handle drag events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Handle drop area highlighting
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, function() {
            dropArea.classList.add('highlight');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, function() {
            dropArea.classList.remove('highlight');
        }, false);
    });
    
    // Handle dropped files
    dropArea.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            handleFiles(files[0]);
        }
    }, false);
    
    // Handle files selected via file input
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            handleFiles(this.files[0]);
        }
    });
    
    // Process the uploaded file
    function handleFiles(file) {
        // Validate file type
        if (!file.type.match('image.*')) {
            alert('Please upload an image file (PNG, JPG, etc.)');
            return;
        }
        
        // Display preview
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = previewContainer.querySelector('img');
            img.src = e.target.result;
            previewContainer.classList.remove('d-none');
        };
        reader.readAsDataURL(file);
    }
}