/**
 * spring_calculator.js
 * Handles suspension calculations and form interactions for GT7 Tuning app
 */

import { FormHandler } from './modules/form_handler.js';

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form handler
    const formHandler = new FormHandler('springCalcForm', {
        validateOnChange: true,
        validateOnBlur: true,
        customValidators: {
            // Validate front weight distribution is within range
            front_weight_distribution: function(value, field) {
                const numValue = parseFloat(value);
                if (numValue < 25 || numValue > 75) {
                    return 'Weight distribution must be between 25% and 75%';
                }
                return null;
            },
            
            // Validate ride heights are reasonable
            front_ride_height: function(value, field) {
                const rearHeightField = document.getElementById('id_rear_ride_height');
                if (rearHeightField && rearHeightField.value) {
                    const frontHeight = parseInt(value);
                    const rearHeight = parseInt(rearHeightField.value);
                    const difference = Math.abs(frontHeight - rearHeight);
                    
                    if (difference > 100) {
                        return 'Front and rear ride height difference should not exceed 100mm';
                    }
                }
                return null;
            },
            
            rear_ride_height: function(value, field) {
                const frontHeightField = document.getElementById('id_front_ride_height');
                if (frontHeightField && frontHeightField.value) {
                    const rearHeight = parseInt(value);
                    const frontHeight = parseInt(frontHeightField.value);
                    const difference = Math.abs(frontHeight - rearHeight);
                    
                    if (difference > 100) {
                        return 'Front and rear ride height difference should not exceed 100mm';
                    }
                }
                return null;
            },
            
            // Validate G-force values are reasonable
            rotational_g_40mph: function(value, field) {
                const g75Field = document.getElementById('id_rotational_g_75mph');
                if (g75Field && g75Field.value) {
                    const g40 = parseFloat(value);
                    const g75 = parseFloat(g75Field.value);
                    
                    if (g40 > g75 && g40 > 1.0 && g75 > 1.0) {
                        formHandler.addWarning('rotational_g_40mph', 
                           'G-force at 40mph is higher than at 75mph, which is unusual');
                    }
                }
                return null;
            },
            
            rotational_g_75mph: function(value, field) {
                const g150Field = document.getElementById('id_rotational_g_150mph');
                if (g150Field && g150Field.value) {
                    const g75 = parseFloat(value);
                    const g150 = parseFloat(g150Field.value);
                    
                    if (g75 > g150 && g75 > 1.0 && g150 > 1.0) {
                        formHandler.addWarning('rotational_g_75mph', 
                           'G-force at 75mph is higher than at 150mph, which is unusual');
                    }
                }
                return null;
            }
        }
    });
    
    // Handle vehicle selection changes
    const vehicleField = document.getElementById('id_vehicle');
    if (vehicleField) {
        vehicleField.addEventListener('change', function() {
            fetchVehicleData(this.value);
        });
    }
    
    // Initialize save setup modal
    initSaveSetupModal();
    
    // Handle reset form button
    const resetFormBtn = document.getElementById('resetFormBtn');
    if (resetFormBtn) {
        resetFormBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to reset the form? All unsaved changes will be lost.')) {
                formHandler.resetForm();
            }
        });
    }
});

/**
 * Fetch vehicle data and populate form fields
 * @param {string} vehicleId - The selected vehicle ID
 */
function fetchVehicleData(vehicleId) {
    if (!vehicleId) return;
    
    // Show loading indicator
    document.getElementById('id_vehicle').classList.add('loading');
    
    // Send AJAX request to get vehicle data
    fetch(`/api/vehicle/${vehicleId}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading indicator
        document.getElementById('id_vehicle').classList.remove('loading');
        
        if (data.success) {
            // Populate form fields with vehicle data
            document.getElementById('id_vehicle_weight').value = data.vehicle.base_weight;
            document.getElementById('id_front_weight_distribution').value = data.vehicle.front_weight_distribution || 50;
            
            // Show success message
            showToast('Vehicle Data Loaded', `Data for ${data.vehicle.name} has been loaded.`, 'success');
        } else {
            // Show error message
            showToast('Error', data.message || 'Failed to load vehicle data', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('id_vehicle').classList.remove('loading');
        showToast('Error', 'An error occurred while fetching vehicle data', 'error');
    });
}

/**
 * Initialize save setup modal
 */
function initSaveSetupModal() {
    const saveSetupBtn = document.getElementById('saveSetupBtn');
    const confirmSaveBtn = document.getElementById('confirmSaveBtn');
    
    if (saveSetupBtn && confirmSaveBtn) {
        confirmSaveBtn.addEventListener('click', function() {
            // Get form values
            const setupName = document.getElementById('setupName').value;
            const setupNotes = document.getElementById('setupNotes').value;
            
            if (!setupName) {
                alert('Please enter a name for your setup');
                return;
            }
            
            // Show loading state
            confirmSaveBtn.disabled = true;
            confirmSaveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
            
            // Get calculation ID
            const calculationId = saveSetupBtn.dataset.calculationId;
            if (!calculationId) {
                alert('No calculation ID found. Please try again.');
                confirmSaveBtn.disabled = false;
                confirmSaveBtn.textContent = 'Save Setup';
                return;
            }
            
            // Create request data
            const data = {
                name: setupName,
                notes: setupNotes,
                spring_calculation_id: calculationId
            };
            
            // Send AJAX request
            fetch('/save-setup/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                // Reset button state
                confirmSaveBtn.disabled = false;
                confirmSaveBtn.textContent = 'Save Setup';
                
                if (data.success) {
                    // Show success message
                    showToast('Setup Saved', data.message, 'success');
                    
                    // Close the modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('saveSetupModal'));
                    if (modal) {
                        modal.hide();
                    }
                } else {
                    // Show error message
                    showToast('Error', data.message || 'Failed to save setup', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Reset button state
                confirmSaveBtn.disabled = false;
                confirmSaveBtn.textContent = 'Save Setup';
                
                // Show error message
                showToast('Error', 'An error occurred while saving the setup', 'error');
            });
        });
    }
}