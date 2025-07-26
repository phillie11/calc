/**
 * calculation.js
 * Module for handling client-side calculations in the GT7 Tuning application
 */

/**
 * Calculate spring rate based on weight, ride height, and lever ratio
 * @param {number} weight - Weight in kg
 * @param {number} weightDistribution - Weight distribution percentage (0-100)
 * @param {number} rideHeight - Ride height in mm
 * @param {number} leverRatio - Lever ratio
 * @param {number} downforce - Downforce value
 * @param {number} stiffnessMultiplier - Stiffness multiplier
 * @returns {number} - Spring rate in N/mm
 */
export function calculateSpringRate(weight, weightDistribution, rideHeight, leverRatio, downforce = 0, stiffnessMultiplier = 1.0) {
    // Convert percentage to decimal
    const weightRatio = weightDistribution / 100;
    
    // Calculate load
    const massAtWheel = weight * weightRatio + (downforce / 2) - 45; // 45kg is approximate unsprung weight
    const load = massAtWheel / leverRatio;
    
    // Convert to Newtons
    const loadN = load * 9.81;
    
    // Convert ride height to meters
    const rideHeightM = Math.max(1, rideHeight) / 1000;
    
    // Calculate spring rate in N/m
    const springRateNm = loadN / rideHeightM;
    
    // Apply stiffness multiplier
    const adjustedSpringRate = springRateNm * stiffnessMultiplier;
    
    // Convert to N/mm and round appropriately
    let springRateNmm = adjustedSpringRate / 1000;
    
    // Round to GT7 increments
    if (springRateNmm < 10) {
        springRateNmm = Math.round(springRateNmm * 10) / 10; // 0.1 N/mm increments
    } else if (springRateNmm < 30) {
        springRateNmm = Math.round(springRateNmm * 2) / 2; // 0.5 N/mm increments
    } else {
        springRateNmm = Math.round(springRateNmm); // 1.0 N/mm increments
    }
    
    return springRateNmm;
}

/**
 * Calculate spring frequency from spring rate and weight
 * @param {number} springRate - Spring rate in N/mm
 * @param {number} weight - Weight in kg
 * @param {number} carTypeMultiplier - Multiplier based on car type
 * @param {number} offsetMultiplier - User adjustment multiplier
 * @returns {number} - Spring frequency in Hz
 */
export function calculateSpringFrequency(springRate, weight, carTypeMultiplier = 1.333, offsetMultiplier = 1.0) {
    // Convert spring rate from N/mm to N/m
    const springRateNm = springRate * 1000;
    
    // Calculate raw spring frequency
    const rawFrequency = Math.sqrt(springRateNm / weight);
    
    // Convert to Hz
    const frequencyHz = (1 / (2 * Math.PI)) * rawFrequency;
    
    // Apply multipliers
    const finalFrequency = frequencyHz * carTypeMultiplier * offsetMultiplier;
    
    // Round to 2 decimal places
    return Math.round(finalFrequency * 100) / 100;
}

/**
 * Calculate tire diameter based on speed, RPM, gear ratio, and final drive
 * @param {number} gearRatio - Current gear ratio
 * @param {number} rpm - Engine RPM
 * @param {number} speed - Vehicle speed in km/h
 * @param {number} finalDrive - Final drive ratio
 * @returns {number} - Calculated tire diameter in inches
 */
export function calculateTireDiameter(gearRatio, rpm, speed, finalDrive) {
    // Formula: Tire Diameter (inches) = (Speed in km/h * 1000) / ((RPM / (gear ratio * final drive)) * 60 * π) * 39.37
    const numerator = speed * 1000;
    const denominator = (rpm / (gearRatio * finalDrive)) * 60 * Math.PI;
    const diameterInches = (numerator / denominator) * 39.37;
    
    // Round to 2 decimal places
    const roundedDiameter = Math.round(diameterInches * 100) / 100;
    
    // Validate result is reasonable (between 15 and 35 inches)
    if (roundedDiameter >= 15 && roundedDiameter <= 35) {
        return roundedDiameter;
    } else {
        console.warn(`Calculated tire diameter ${roundedDiameter} is outside reasonable range, using default`);
        return 26.0; // Default value
    }
}

/**
 * Calculate vehicle speed at a given RPM and gear ratio
 * @param {number} rpm - Engine RPM
 * @param {number} gearRatio - Gear ratio
 * @param {number} finalDrive - Final drive ratio
 * @param {number} tireDiameterInches - Tire diameter in inches
 * @returns {object} - Object with speed in mph and km/h
 */
export function calculateSpeed(rpm, gearRatio, finalDrive, tireDiameterInches) {
    // Convert tire diameter to meters
    const tireDiameterMeters = tireDiameterInches * 0.0254;
    const tireCircumference = Math.PI * tireDiameterMeters;
    
    // Calculate speed in m/s
    // Formula: Speed (m/s) = (RPM * circumference) / (gear ratio * final drive * 60)
    const speedMps = (rpm * tireCircumference) / (gearRatio * finalDrive * 60);
    
    // Convert to km/h and mph
    const speedKph = speedMps * 3.6;
    const speedMph = speedKph / 1.60934;
    
    return {
        mph: Math.round(speedMph * 10) / 10,
        kph: Math.round(speedKph * 10) / 10
    };
}

/**
 * Estimate 0-60 mph acceleration time
 * @param {number} powerHp - Engine power in HP
 * @param {number} weightKg - Vehicle weight in kg
 * @param {object} gearRatios - Object with gear ratios
 * @param {number} finalDrive - Final drive ratio
 * @param {number} tireDiameterInches - Tire diameter in inches
 * @returns {number} - Estimated 0-60 mph time in seconds
 */
export function estimateAcceleration(powerHp, weightKg, gearRatios, finalDrive, tireDiameterInches) {
    // Basic power-to-weight calculation (simplified)
    const powerToWeight = powerHp / weightKg;
    
    // Get first and second gear ratios
    const gearValues = Object.values(gearRatios);
    const firstGear = gearValues[0] || 3.545;
    const secondGear = gearValues[1] || firstGear * 0.6;
    
    // Calculate gear coverage factor
    let gearFactor = 1.0;
    if (firstGear > 0 && secondGear > 0) {
        const ratio = firstGear / secondGear;
        // Ideal ratio is around 1.7-1.8
        if (ratio < 1.5) {
            gearFactor = 0.9 + (ratio - 1.0) * 0.1; // Penalty for too close ratios
        } else if (ratio > 2.0) {
            gearFactor = 0.9 + (2.5 - ratio) * 0.1; // Penalty for too wide ratios
        }
    }
    
    // Apply correction for first gear ratio
    let launchFactor = 1.0;
    if (firstGear > 3.5) {
        launchFactor = 1.0 + (firstGear - 3.5) * 0.03; // Small penalty for very tall first gear
    } else if (firstGear < 2.5) {
        launchFactor = 1.0 + (2.5 - firstGear) * 0.05; // Larger penalty for very short first gear
    }
    
    // Calculate 0-60 time
    const accelerationEstimate = 5.0 / (powerToWeight * gearFactor) * 2.5;
    const finalEstimate = accelerationEstimate * launchFactor;
    
    // Round to 1 decimal place
    return Math.round(finalEstimate * 10) / 10;
}

/**
 * Generate tire size options based on vehicle type and year
 * @param {string} vehicleType - Type of vehicle (ROAD, GR4, GR3, etc.)
 * @param {number} year - Model year
 * @returns {object} - Object with front and rear tire size recommendations
 */
export function getTireSizeRecommendations(vehicleType, year) {
    let frontTireSize = 0;
    let rearTireSize = 0;
    
    // Set default sizes based on vehicle type
    switch(vehicleType) {
        case 'ROAD':
            frontTireSize = year < 1990 ? 22.5 : 24.0;
            rearTireSize = year < 1990 ? 23.0 : 24.5;
            break;
        case 'GR4':
            frontTireSize = 26.0;
            rearTireSize = 26.0;
            break;
        case 'GR3':
            frontTireSize = 27.0;
            rearTireSize = 27.0;
            break;
        case 'RACE':
            frontTireSize = 28.0;
            rearTireSize = 28.5;
            break;
        case 'VGT':
            frontTireSize = 26.5;
            rearTireSize = 27.0;
            break;
        default:
            frontTireSize = 26.0;
            rearTireSize = 26.0;
    }
    
    return {
        frontTireSize,
        rearTireSize,
        recommended: true
    };
}