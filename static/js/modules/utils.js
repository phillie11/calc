/**
 * utils.js
 * Utility functions for the GT7 Tuning application
 */

/**
 * Format a value with appropriate units
 * @param {number} value - The value to format
 * @param {string} unit - The unit to append
 * @param {number} decimals - Number of decimal places
 * @returns {string} - Formatted value with unit
 */
export function formatWithUnit(value, unit, decimals = 2) {
    return `${formatNumber(value, decimals)} ${unit}`;
}

/**
 * Format a number with appropriate decimal places
 * @param {number} value - The number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} - Formatted number
 */
export function formatNumber(value, decimals = 2) {
    if (typeof value !== 'number') {
        value = parseFloat(value);
    }
    
    if (isNaN(value)) {
        return 'N/A';
    }
    
    // Use appropriate precision based on the number
    if (value === 0) {
        return '0';
    } else if (Math.abs(value) < 0.01) {
        return value.toFixed(4);
    } else if (Math.abs(value) < 0.1) {
        return value.toFixed(3);
    } else if (Math.abs(value) < 1) {
        return value.toFixed(2);
    } else if (Math.abs(value) < 10 && decimals > 1) {
        return value.toFixed(2);
    } else if (Math.abs(value) < 100 && decimals > 0) {
        return value.toFixed(1);
    } else {
        return Math.round(value).toString();
    }
}

/**
 * Debounce a function
 * @param {Function} func - The function to debounce
 * @param {number} wait - Time to wait in milliseconds
 * @returns {Function} - Debounced function
 */
export function debounce(func, wait = 300) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

/**
 * Convert between different units
 * @param {number} value - The value to convert
 * @param {string} fromUnit - The original unit
 * @param {string} toUnit - The target unit
 * @returns {number} - Converted value
 */
export function convertUnit(value, fromUnit, toUnit) {
    // Define conversion factors
    const conversionFactors = {
        // Length conversions
        'mm_to_in': 1 / 25.4,
        'in_to_mm': 25.4,
        
        // Speed conversions
        'kph_to_mph': 0.621371,
        'mph_to_kph': 1.60934,
        
        // Weight conversions
        'kg_to_lb': 2.20462,
        'lb_to_kg': 0.453592,
        
        // Force conversions
        'n_to_lbf': 0.224809,
        'lbf_to_n': 4.44822,
        
        // Spring rate conversions
        'nmm_to_lbin': 5.71014,
        'lbin_to_nmm': 0.175127
    };
    
    // Determine conversion key
    const conversionKey = `${fromUnit}_to_${toUnit}`;
    
    // Check if conversion exists
    if (conversionFactors[conversionKey]) {
        return value * conversionFactors[conversionKey];
    }
    
    // No conversion found, return original value
    console.warn(`No conversion found from ${fromUnit} to ${toUnit}`);
    return value;
}

/**
 * Get color for a value based on a range
 * @param {number} value - The value to check
 * @param {number} min - Minimum of range
 * @param {number} max - Maximum of range
 * @param {string} minColor - Color for minimum value (hex or rgba)
 * @param {string} maxColor - Color for maximum value (hex or rgba)
 * @returns {string} - CSS color string
 */
export function getColorForValue(value, min, max, minColor = '#28a745', maxColor = '#dc3545') {
    // Clamp value to range
    value = Math.max(min, Math.min(max, value));
    
    // Calculate percentage within range
    const percent = (value - min) / (max - min);
    
    // Convert hex colors to RGB if needed
    let minRGB = parseColor(minColor);
    let maxRGB = parseColor(maxColor);
    
    // Interpolate between colors
    const r = Math.round(minRGB.r + percent * (maxRGB.r - minRGB.r));
    const g = Math.round(minRGB.g + percent * (maxRGB.g - minRGB.g));
    const b = Math.round(minRGB.b + percent * (maxRGB.b - minRGB.b));
    
    return `rgb(${r}, ${g}, ${b})`;
}

/**
 * Parse color string to RGB object
 * @param {string} color - CSS color string (hex or rgb)
 * @returns {object} - Object with r, g, b values
 */
function parseColor(color) {
    // Handle hex color
    if (color.startsWith('#')) {
        const hex = color.slice(1);
        const bigint = parseInt(hex, 16);
        
        return {
            r: (bigint >> 16) & 255,
            g: (bigint >> 8) & 255,
            b: bigint & 255
        };
    }
    
    // Handle rgb/rgba color
    const rgbMatch = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)/);
    if (rgbMatch) {
        return {
            r: parseInt(rgbMatch[1]),
            g: parseInt(rgbMatch[2]),
            b: parseInt(rgbMatch[3])
        };
    }
    
    // Default fallback
    return { r: 0, g: 0, b: 0 };
}

/**
 * Check if a value is within a reasonable range
 * @param {number} value - Value to check
 * @param {number} expected - Expected value
 * @param {number} tolerance - Tolerance as a percentage
 * @returns {boolean} - True if within range, false otherwise
 */
export function isWithinRange(value, expected, tolerance = 10) {
    const range = expected * (tolerance / 100);
    return value >= (expected - range) && value <= (expected + range);
}

/**
 * Generate a unique ID
 * @param {string} prefix - Optional prefix for the ID
 * @returns {string} - Unique ID
 */
export function generateId(prefix = 'gt7-') {
    return prefix + Math.random().toString(36).substring(2, 9);
}

/**
 * Get the appropriate weight distribution for a drivetrain type
 * @param {string} drivetrain - Drivetrain type (FR, FF, MR, RR, 4WD)
 * @returns {number} - Recommended front weight distribution percentage
 */
export function getWeightDistribution(drivetrain) {
    switch (drivetrain) {
        case 'FF':
            return 62; // Front-engine, front-wheel drive
        case 'FR':
            return 52; // Front-engine, rear-wheel drive
        case 'MR':
            return 42; // Mid-engine, rear-wheel drive
        case 'RR':
            return 38; // Rear-engine, rear-wheel drive
        case '4WD':
            return 50; // All-wheel drive
        default:
            return 50; // Default balanced distribution
    }
}

/**
 * Create a validation function for numerical ranges
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @param {string} errorMessage - Custom error message
 * @returns {Function} - Validation function
 */
export function createRangeValidator(min, max, errorMessage = null) {
    return function(value) {
        const numValue = parseFloat(value);
        if (isNaN(numValue)) {
            return 'Please enter a valid number';
        }
        
        if (numValue < min || numValue > max) {
            return errorMessage || `Value must be between ${min} and ${max}`;
        }
        
        return null; // No error
    };
}

/**
 * Format a date string
 * @param {string|Date} date - Date to format
 * @param {boolean} includeTime - Whether to include time
 * @returns {string} - Formatted date string
 */
export function formatDate(date, includeTime = false) {
    if (!date) return '';
    
    const dateObj = new Date(date);
    if (isNaN(dateObj.getTime())) return 'Invalid date';
    
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric'
    };
    
    if (includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
    }
    
    return dateObj.toLocaleDateString('en-US', options);
}

/**
 * Deep clone an object
 * @param {object} obj - Object to clone
 * @returns {object} - Cloned object
 */
export function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

/**
 * Parse URL parameters into an object
 * @returns {object} - Object with URL parameters
 */
export function getUrlParams() {
    const params = {};
    const queryString = window.location.search.slice(1);
    
    if (!queryString) return params;
    
    queryString.split('&').forEach(pair => {
        const [key, value] = pair.split('=');
        params[decodeURIComponent(key)] = decodeURIComponent(value || '');
    });
    
    return params;
}