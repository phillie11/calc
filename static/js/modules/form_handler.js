/**
 * form_handler.js
 * Module for handling form interactions in the GT7 Tuning application
 */

export class FormHandler {
    /**
     * Initialize the form handler
     * @param {string} formId - ID of the form element
     * @param {Object} options - Configuration options
     */
    constructor(formId, options = {}) {
        this.form = document.getElementById(formId);
        if (!this.form) {
            throw new Error(`Form with ID "${formId}" not found`);
        }
        
        this.options = {
            resetConfirmation: true,
            validateOnChange: true,
            validateOnBlur: true,
            customValidators: {},
            onSubmit: null,
            onReset: null,
            ...options
        };
        
        // Track original field values for reset
        this.originalValues = {};
        this.fieldValidators = {};
        this.warnings = [];
        
        // Store initial values for reset
        this.storeInitialValues();
        
        // Set up event listeners
        this.setupEventListeners();
    }
    
    /**
     * Store initial field values for reset
     */
    storeInitialValues() {
        // Get all form inputs, selects, and textareas
        const fields = this.form.querySelectorAll('input, select, textarea');
        
        fields.forEach(field => {
            const name = field.name;
            if (!name) return;
            
            if (field.type === 'checkbox' || field.type === 'radio') {
                this.originalValues[name] = field.checked;
            } else if (field.tagName === 'SELECT' && field.multiple) {
                // Multiple select
                this.originalValues[name] = Array.from(field.selectedOptions)
                    .map(option => option.value);
            } else {
                this.originalValues[name] = field.value;
            }
            
            // Store dataset attributes that start with 'default'
            for (const key in field.dataset) {
                if (key.startsWith('default')) {
                    const dataKey = `data-${key}`;
                    this.originalValues[`${name}_${dataKey}`] = field.dataset[key];
                }
            }
        });
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Handle form submission
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
        
        // Handle form reset
        const resetBtn = this.form.querySelector('button[type="reset"]');
        if (resetBtn) {
            resetBtn.addEventListener('click', this.handleReset.bind(this));
        }
        
        // Set up validation on change and blur if enabled
        if (this.options.validateOnChange || this.options.validateOnBlur) {
            const fields = this.form.querySelectorAll('input, select, textarea');
            
            fields.forEach(field => {
                if (this.options.validateOnChange) {
                    field.addEventListener('change', () => this.validateField(field));
                }
                
                if (this.options.validateOnBlur) {
                    field.addEventListener('blur', () => this.validateField(field));
                }
            });
        }
    }
    
    /**
     * Handle form submission
     * @param {Event} event - The submit event
     */
    handleSubmit(event) {
        // Validate the form
        const isValid = this.validate();
        
        // If not valid, prevent submission
        if (!isValid) {
            event.preventDefault();
            return;
        }
        
        // If we have an onSubmit callback, call it
        if (typeof this.options.onSubmit === 'function') {
            const formData = this.getFormData();
            const result = this.options.onSubmit(formData, event);
            
            // If the callback returns false, prevent submission
            if (result === false) {
                event.preventDefault();
            }
        }
    }
    
    /**
     * Handle form reset
     * @param {Event} event - The reset event
     */
    handleReset(event) {
        // Prevent the default reset behavior
        event.preventDefault();
        
        // Show confirmation if enabled
        if (this.options.resetConfirmation) {
            if (!confirm('Are you sure you want to reset all form values?')) {
                return;
            }
        }
        
        // Reset the form to original values
        this.resetForm();
        
        // If we have an onReset callback, call it
        if (typeof this.options.onReset === 'function') {
            this.options.onReset(event);
        }
        
        // Clear any validation messages
        this.clearValidationMessages();
    }
    
    /**
     * Reset the form to original values
     */
    resetForm() {
        // Get all form inputs, selects, and textareas
        const fields = this.form.querySelectorAll('input, select, textarea');
        
        fields.forEach(field => {
            const name = field.name;
            if (!name || !(name in this.originalValues)) return;
            
            const originalValue = this.originalValues[name];
            
            if (field.type === 'checkbox' || field.type === 'radio') {
                field.checked = originalValue;
            } else if (field.tagName === 'SELECT' && field.multiple) {
                // Multiple select
                for (const option of field.options) {
                    option.selected = originalValue.includes(option.value);
                }
            } else {
                field.value = originalValue;
            }
            
            // Restore dataset attributes that start with 'default'
            for (const key in field.dataset) {
                if (key.startsWith('default')) {
                    const dataKey = `${name}_data-${key}`;
                    if (dataKey in this.originalValues) {
                        field.dataset[key] = this.originalValues[dataKey];
                    }
                }
            }
            
            // Trigger change event to update any dependent fields
            field.dispatchEvent(new Event('change', { bubbles: true }));
        });
    }
    
    /**
     * Validate the entire form
     * @returns {boolean} - Whether the form is valid
     */
    validate() {
        // Clear previous validation messages
        this.clearValidationMessages();
        
        // Get all form inputs, selects, and textareas
        const fields = this.form.querySelectorAll('input, select, textarea');
        
        // Track whether the form is valid
        let isValid = true;
        
        // Validate each field
        fields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });
        
        // Custom form-level validation
        if (typeof this.options.customValidators.form === 'function') {
            const formData = this.getFormData();
            const formErrors = this.options.customValidators.form(formData);
            
            if (formErrors && Object.keys(formErrors).length > 0) {
                // Handle form-level errors
                for (const [fieldName, error] of Object.entries(formErrors)) {
                    const field = this.form.querySelector(`[name="${fieldName}"]`);
                    
                    if (field) {
                        this.showValidationError(field, error);
                    } else {
                        // Form-level error with no associated field
                        this.showFormError(error);
                    }
                    
                    isValid = false;
                }
            }
        }
        
        return isValid;
    }
    
    /**
     * Validate a specific field
     * @param {HTMLElement} field - The field to validate
     * @returns {boolean} - Whether the field is valid
     */
    validateField(field) {
        // Skip fields without a name
        if (!field.name) return true;
        
        // Clear previous validation messages for this field
        this.clearValidationMessage(field);
        
        // Skip disabled fields
        if (field.disabled) return true;
        
        // Skip fields that don't have validation
        if (!field.required && !field.pattern && !field.min && !field.max && 
            !field.minLength && !field.maxLength && !field.step) {
            // Check if we have a custom validator for this field
            if (typeof this.options.customValidators[field.name] !== 'function') {
                return true;
            }
        }
        
        // Get field value
        let value = field.value;
        if (field.type === 'checkbox') {
            value = field.checked;
        } else if (field.type === 'radio') {
            // For radio buttons, find the checked one in the group
            const radioGroup = this.form.querySelectorAll(`input[name="${field.name}"]`);
            const checkedRadio = Array.from(radioGroup).find(radio => radio.checked);
            value = checkedRadio ? checkedRadio.value : '';
        }
        
        // Skip empty optional fields
        if (!field.required && (value === '' || value === null || value === undefined)) {
            return true;
        }
        
        // Custom validation for the field
        if (typeof this.options.customValidators[field.name] === 'function') {
            const error = this.options.customValidators[field.name](value, field);
            
            if (error) {
                this.showValidationError(field, error);
                return false;
            }
        }
        
        // HTML5 validation
        if (!field.checkValidity()) {
            // Get validation message from the field
            let errorMessage = field.validationMessage;
            
            // If no validation message, generate one based on the validation constraint
            if (!errorMessage) {
                if (field.validity.valueMissing) {
                    errorMessage = 'This field is required';
                } else if (field.validity.typeMismatch) {
                    errorMessage = `Please enter a valid ${field.type}`;
                } else if (field.validity.patternMismatch) {
                    errorMessage = `Please match the requested format`;
                } else if (field.validity.tooLong) {
                    errorMessage = `Please shorten this text to ${field.maxLength} characters or less`;
                } else if (field.validity.tooShort) {
                    errorMessage = `Please lengthen this text to ${field.minLength} characters or more`;
                } else if (field.validity.rangeUnderflow) {
                    errorMessage = `Value must be ${field.min} or higher`;
                } else if (field.validity.rangeOverflow) {
                    errorMessage = `Value must be ${field.max} or lower`;
                } else if (field.validity.stepMismatch) {
                    errorMessage = `Please enter a valid value (step: ${field.step})`;
                } else {
                    errorMessage = 'Invalid value';
                }
            }
            
            this.showValidationError(field, errorMessage);
            return false;
        }
        
        return true;
    }
    
    /**
     * Show a validation error for a field
     * @param {HTMLElement} field - The field with the error
     * @param {string} message - The error message
     */
    showValidationError(field, message) {
        // Add error styling to the field
        field.classList.add('is-invalid');
        
        // Create or update the feedback element
        let feedback = field.nextElementSibling;
        if (!feedback || !feedback.classList.contains('invalid-feedback')) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.insertBefore(feedback, field.nextSibling);
        }
        
        feedback.textContent = message;
    }
    
    /**
     * Show a form-level error
     * @param {string} message - The error message
     */
    showFormError(message) {
        // Look for an existing form-error element
        let errorContainer = this.form.querySelector('.form-error');
        
        // Create one if it doesn't exist
        if (!errorContainer) {
            errorContainer = document.createElement('div');
            errorContainer.className = 'alert alert-danger form-error mt-3';
            this.form.prepend(errorContainer);
        }
        
        errorContainer.textContent = message;
    }
    
    /**
     * Show a warning for a field
     * @param {string} fieldName - The field name
     * @param {string} message - The warning message
     */
    addWarning(fieldName, message) {
        this.warnings.push({ fieldName, message });
        
        // Find the field
        const field = this.form.querySelector(`[name="${fieldName}"]`);
        if (!field) return;
        
        // Add warning styling to the field
        field.classList.add('is-warning');
        
        // Create or update the feedback element
        let feedback = field.nextElementSibling;
        if (!feedback || !feedback.classList.contains('warning-feedback')) {
            feedback = document.createElement('div');
            feedback.className = 'warning-feedback text-warning small';
            field.parentNode.insertBefore(feedback, field.nextSibling);
        }
        
        feedback.textContent = message;
    }
    
    /**
     * Clear all validation messages
     */
    clearValidationMessages() {
        // Remove validation classes
        const invalidFields = this.form.querySelectorAll('.is-invalid');
        invalidFields.forEach(field => {
            field.classList.remove('is-invalid');
        });
        
        // Remove validation messages
        const feedbacks = this.form.querySelectorAll('.invalid-feedback');
        feedbacks.forEach(feedback => {
            feedback.remove();
        });
        
        // Remove form errors
        const formErrors = this.form.querySelectorAll('.form-error');
        formErrors.forEach(error => {
            error.remove();
        });
        
        // Clear warnings
        this.clearWarnings();
    }
    
    /**
     * Clear validation message for a specific field
     * @param {HTMLElement} field - The field to clear
     */
    clearValidationMessage(field) {
        // Remove validation class
        field.classList.remove('is-invalid');
        
        // Find and remove the feedback element
        const feedback = field.nextElementSibling;
        if (feedback && feedback.classList.contains('invalid-feedback')) {
            feedback.remove();
        }
    }
    
    /**
     * Clear all warnings
     */
    clearWarnings() {
        this.warnings = [];
        
        // Remove warning classes
        const warningFields = this.form.querySelectorAll('.is-warning');
        warningFields.forEach(field => {
            field.classList.remove('is-warning');
        });
        
        // Remove warning messages
        const feedbacks = this.form.querySelectorAll('.warning-feedback');
        feedbacks.forEach(feedback => {
            feedback.remove();
        });
    }
    
    /**
     * Get all form data as an object
     * @returns {Object} - Form data object
     */
    getFormData() {
        const formData = new FormData(this.form);
        const data = {};
        
        for (const [name, value] of formData.entries()) {
            // Handle arrays (multiple select or checkboxes with same name)
            if (name.endsWith('[]')) {
                const baseName = name.slice(0, -2);
                if (!data[baseName]) {
                    data[baseName] = [];
                }
                data[baseName].push(value);
            } else {
                data[name] = value;
            }
        }
        
        return data;
    }
    
    /**
     * Add a custom field validator
     * @param {string} fieldName - The field name
     * @param {function} validator - The validator function
     */
    addValidator(fieldName, validator) {
        if (typeof validator !== 'function') {
            throw new Error('Validator must be a function');
        }
        
        this.options.customValidators[fieldName] = validator;
    }
    
    /**
     * Add a form-level validator
     * @param {function} validator - The validator function
     */
    addFormValidator(validator) {
        if (typeof validator !== 'function') {
            throw new Error('Validator must be a function');
        }
        
        this.options.customValidators.form = validator;
    }
}