# spring_calc/gear_calculator.py

import math

def calculate_optimal_gear_ratios(num_gears, first_gear_ratio, last_gear_ratio):
    """
    Calculate a series of gear ratios using geometric progression
    
    Args:
        num_gears (int): Number of gears in the transmission
        first_gear_ratio (float): Ratio for first gear
        last_gear_ratio (float): Ratio for last gear
        
    Returns:
        dict: Dictionary of gear ratios
    """
    # Calculate the common ratio between gears
    ratio = math.pow(first_gear_ratio / last_gear_ratio, 1/(num_gears - 1))
    
    gear_ratios = {}
    for i in range(num_gears):
        # Calculate each gear using the geometric progression
        current_ratio = first_gear_ratio / math.pow(ratio, i)
        # Round to 3 decimal places as GT7 does
        gear_name = f"{i+1}st" if i == 0 else f"{i+1}nd" if i == 1 else f"{i+1}rd" if i == 2 else f"{i+1}th"
        gear_ratios[gear_name] = round(current_ratio, 3)
    
    return gear_ratios

def calculate_speed_at_rpm(rpm, gear_ratio, final_drive, tire_diameter_inches):
    """
    Calculate vehicle speed at a given RPM and gear ratio
    
    Args:
        rpm (int): Engine RPM
        gear_ratio (float): Gear ratio
        final_drive (float): Final drive ratio
        tire_diameter_inches (float): Tire diameter in inches
        
    Returns:
        tuple: (speed_mph, speed_kph)
    """
    # Convert tire diameter to meters
    tire_diameter_meters = tire_diameter_inches * 0.0254
    tire_circumference = math.pi * tire_diameter_meters
    
    # Calculate speed in m/s
    speed_mps = (rpm * tire_circumference) / (gear_ratio * final_drive * 60)
    
    # Convert to km/h and mph
    speed_kph = speed_mps * 3.6
    speed_mph = speed_kph / 1.60934
    
    return speed_mph, speed_kph

def estimate_acceleration(power_hp, weight_kg, gear_ratios, final_drive, tire_diameter_inches):
    """
    Estimate 0-60 mph acceleration time based on power-to-weight ratio and gearing
    
    Args:
        power_hp (int): Engine power in HP
        weight_kg (float): Vehicle weight in kg
        gear_ratios (dict): Dictionary of gear ratios
        final_drive (float): Final drive ratio
        tire_diameter_inches (float): Tire diameter in inches
        
    Returns:
        float: Estimated 0-60 mph time in seconds
    """
    # Basic power-to-weight calculation (simplified)
    power_to_weight = power_hp / weight_kg
    
    # Get first and second gear ratios
    first_gear = list(gear_ratios.values())[0]
    second_gear = list(gear_ratios.values())[1] if len(gear_ratios) > 1 else first_gear * 0.6
    
    # Calculate gear coverage factor (how well the gears cover the acceleration range)
    gear_factor = 1.0  # Default factor
    if first_gear > 0 and second_gear > 0:
        ratio = first_gear / second_gear
        # Ideal ratio is around 1.7-1.8, penalize if too far from this
        if ratio < 1.5 or ratio > 2.0:
            gear_factor = 0.9  # Slight penalty for sub-optimal gear spacing
    
    # Simple formula for 0-60 mph time (very approximate)
    # Lower time is better (faster acceleration)
    acceleration_estimate = 5.0 / (power_to_weight * gear_factor) * 2.5
    
    # Apply a small correction based on first gear ratio
    # If first gear is too high, it can be harder to launch
    launch_factor = 1.0
    if first_gear > 3.5:
        launch_factor = 1.05  # Small penalty for very tall first gear
    
    return acceleration_estimate * launch_factor

def optimize_final_drive(target_top_speed_mph, redline_rpm, last_gear_ratio, tire_diameter_inches):
    """
    Calculate optimal final drive ratio to achieve a target top speed
    
    Args:
        target_top_speed_mph (float): Desired top speed in mph
        redline_rpm (int): Engine redline RPM
        last_gear_ratio (float): Last gear ratio
        tire_diameter_inches (float): Tire diameter in inches
        
    Returns:
        float: Optimal final drive ratio
    """
    # Convert target speed to m/s
    target_top_speed_kph = target_top_speed_mph * 1.60934
    target_top_speed_mps = target_top_speed_kph / 3.6
    
    # Convert tire diameter to meters
    tire_diameter_meters = tire_diameter_inches * 0.0254
    tire_circumference = math.pi * tire_diameter_meters
    
    # Calculate ideal final drive using the speed formula rearranged
    ideal_final_drive = (redline_rpm * tire_circumference) / (target_top_speed_mps * last_gear_ratio * 60)
    
    # Round to 3 decimal places as GT7 does
    return round(ideal_final_drive, 3)