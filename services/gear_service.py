# services/gear_service.py
import math
import logging
from typing import Dict, Tuple, List, Union, Optional, Any

logger = logging.getLogger(__name__)

def calculate_optimal_gear_ratios(
    num_gears: int,
    top_speed_mph: int,
    min_corner_speed_mph: int,
    max_rpm: int,
    min_rpm: int,
    tire_diameter_inches: float,
    power_hp: int,
    max_power_rpm: int,
    min_corner_gear: int = 1
) -> Tuple[Dict[str, float], float]:
    """
    Calculate optimal gear ratios for maximum performance
    
    Args:
        num_gears: Number of gears in the transmission
        top_speed_mph: Target top speed in mph
        min_corner_speed_mph: Minimum corner speed in mph
        max_rpm: Maximum engine RPM
        min_rpm: Minimum engine RPM
        tire_diameter_inches: Tire diameter in inches
        power_hp: Engine power in HP
        max_power_rpm: RPM at maximum power
        min_corner_gear: Minimum gear to use in corners
        
    Returns:
        Tuple of (gear_ratios_dict, final_drive)
    """
    try:
        logger.debug(f"Calculating gear ratios for {num_gears} gears, top speed {top_speed_mph} mph, "
                    f"min corner speed {min_corner_speed_mph} mph")
        
        # Constants for conversion
        mph_to_mps = 0.44704  # mph to m/s conversion
        kph_to_mps = 1/3.6    # km/h to m/s conversion
        
        # Calculate optimal final drive based on power-to-weight
        # This is a simplified formula based on GT7's physics
        optimal_final_drive = 4.5 - (0.0015 * power_hp)
        optimal_final_drive = max(3.0, min(5.0, optimal_final_drive))
        
        # Calculate top gear ratio to achieve top speed at max RPM
        top_speed_mps = top_speed_mph * mph_to_mps
        
        # Formula: Top Gear Ratio = (RPM * π * tire diameter in meters) / (60 * speed in m/s * final drive)
        # Convert tire diameter to meters
        tire_diameter_meters = tire_diameter_inches * 0.0254
        
        # Calculate top gear ratio
        top_gear_ratio = (max_rpm * math.pi * tire_diameter_meters) / (60 * top_speed_mps * optimal_final_drive)
        
        # Calculate target RPM for minimum corner speed
        # We want to be at a good point in the power band in the corner
        target_corner_rpm = min_rpm + (max_power_rpm - min_rpm) * 0.4
        
        # Calculate first gear ratio based on desired corner speed in first gear
        # For good acceleration from standstill
        first_gear_ratio = (target_corner_rpm * math.pi * tire_diameter_meters) / (60 * (min_corner_speed_mph * mph_to_mps / 2) * optimal_final_drive)
        
        # If the first gear is too high, adjust it down
        max_first_gear = 5.0
        if first_gear_ratio > max_first_gear:
            first_gear_ratio = max_first_gear
        
        # Calculate gear ratio step (geometric progression)
        ratio_step = math.pow(first_gear_ratio / top_gear_ratio, 1/(num_gears-1))
        
        # Generate all gear ratios
        gear_ratios = {}
        
        for i in range(num_gears):
            gear_number = i + 1
            
            if i == 0:
                # First gear
                ratio = first_gear_ratio
            elif i == num_gears - 1:
                # Top gear
                ratio = top_gear_ratio
            else:
                # Intermediate gears with geometric progression
                ratio = first_gear_ratio / math.pow(ratio_step, i)
            
            # Format gear name
            if gear_number == 1:
                gear_name = f"{gear_number}st"
            elif gear_number == 2:
                gear_name = f"{gear_number}nd"
            elif gear_number == 3:
                gear_name = f"{gear_number}rd"
            else:
                gear_name = f"{gear_number}th"
            
            # Round to 3 decimal places
            gear_ratios[gear_name] = round(ratio, 3)
        
        # Round final drive to 3 decimal places
        final_drive = round(optimal_final_drive, 3)
        
        logger.debug(f"Calculated gear ratios: {gear_ratios}")
        logger.debug(f"Calculated final drive: {final_drive}")
        
        return gear_ratios, final_drive
        
    except Exception as e:
        logger.error(f"Error calculating gear ratios: {str(e)}")
        # Return default values in case of error
        default_ratios = {
            "1st": 3.545,
            "2nd": 2.053,
            "3rd": 1.395,
            "4th": 1.052,
            "5th": 0.851,
            "6th": 0.709
        }
        return default_ratios, 3.700

def calculate_speed_at_rpm(
    rpm: int, 
    gear_ratio: float, 
    final_drive: float, 
    tire_diameter_inches: float
) -> Tuple[float, float]:
    """
    Calculate vehicle speed at a given RPM and gear ratio
    
    Args:
        rpm: Engine RPM
        gear_ratio: Gear ratio
        final_drive: Final drive ratio
        tire_diameter_inches: Tire diameter in inches
        
    Returns:
        Tuple of (speed_mph, speed_kph)
    """
    try:
        # Convert tire diameter to meters
        tire_diameter_meters = tire_diameter_inches * 0.0254
        tire_circumference = math.pi * tire_diameter_meters
        
        # Calculate speed in m/s
        # Formula: Speed (m/s) = (RPM * circumference) / (gear ratio * final drive * 60)
        speed_mps = (rpm * tire_circumference) / (gear_ratio * final_drive * 60)
        
        # Convert to km/h and mph
        speed_kph = speed_mps * 3.6
        speed_mph = speed_kph / 1.60934
        
        return speed_mph, speed_kph
        
    except Exception as e:
        logger.error(f"Error calculating speed at RPM: {str(e)}")
        return 0.0, 0.0

def estimate_acceleration(
    power_hp: int, 
    weight_kg: float, 
    gear_ratios: Dict[str, float], 
    final_drive: float, 
    tire_diameter_inches: float
) -> float:
    """
    Estimate 0-60 mph acceleration time based on power-to-weight ratio and gearing
    
    Args:
        power_hp: Engine power in HP
        weight_kg: Vehicle weight in kg
        gear_ratios: Dictionary of gear ratios
        final_drive: Final drive ratio
        tire_diameter_inches: Tire diameter in inches
        
    Returns:
        Estimated 0-60 mph time in seconds
    """
    try:
        # Basic power-to-weight calculation (simplified)
        power_to_weight = power_hp / weight_kg
        
        # Get first and second gear ratios
        gear_values = list(gear_ratios.values())
        first_gear = gear_values[0] if gear_values else 3.545 
        second_gear = gear_values[1] if len(gear_values) > 1 else first_gear * 0.6
        
        # Calculate gear coverage factor (how well the gears cover the acceleration range)
        gear_factor = 1.0  # Default factor
        if first_gear > 0 and second_gear > 0:
            ratio = first_gear / second_gear
            # Ideal ratio is around 1.7-1.8, penalize if too far from this
            if ratio < 1.5:
                gear_factor = 0.9 + (ratio - 1.0) * 0.1  # Penalty for too close ratios
            elif ratio > 2.0:
                gear_factor = 0.9 + (2.5 - ratio) * 0.1  # Penalty for too wide ratios
        
        # Simple formula for 0-60 mph time (approximation)
        # Lower time is better (faster acceleration)
        acceleration_estimate = 5.0 / (power_to_weight * gear_factor) * 2.5
        
        # Apply a small correction based on first gear ratio
        # If first gear is too high, it can be harder to launch
        launch_factor = 1.0
        if first_gear > 3.5:
            launch_factor = 1.0 + (first_gear - 3.5) * 0.03  # Small penalty for very tall first gear
        elif first_gear < 2.5:
            launch_factor = 1.0 + (2.5 - first_gear) * 0.05  # Larger penalty for very short first gear
        
        # Final estimation with launch factor
        final_estimate = acceleration_estimate * launch_factor
        
        # Round to 1 decimal place
        final_estimate = round(final_estimate, 1)
        
        logger.debug(f"Estimated 0-60 mph acceleration: {final_estimate} seconds")
        
        return final_estimate
        
    except Exception as e:
        logger.error(f"Error estimating acceleration: {str(e)}")
        return 9.9  # Default if calculation fails

def optimize_final_drive(
    target_top_speed_mph: float, 
    redline_rpm: int, 
    last_gear_ratio: float, 
    tire_diameter_inches: float
) -> float:
    """
    Calculate optimal final drive ratio to achieve a target top speed
    
    Args:
        target_top_speed_mph: Desired top speed in mph
        redline_rpm: Engine redline RPM
        last_gear_ratio: Last gear ratio
        tire_diameter_inches: Tire diameter in inches
        
    Returns:
        Optimal final drive ratio
    """
    try:
        # Convert target speed to m/s
        target_top_speed_kph = target_top_speed_mph * 1.60934
        target_top_speed_mps = target_top_speed_kph / 3.6
        
        # Convert tire diameter to meters
        tire_diameter_meters = tire_diameter_inches * 0.0254
        tire_circumference = math.pi * tire_diameter_meters
        
        # Calculate ideal final drive using the speed formula rearranged
        # Formula: Final Drive = (RPM * circumference) / (speed in m/s * last gear ratio * 60)
        ideal_final_drive = (redline_rpm * tire_circumference) / (target_top_speed_mps * last_gear_ratio * 60)
        
        # Round to 3 decimal places
        ideal_final_drive = round(ideal_final_drive, 3)
        
        logger.debug(f"Optimized final drive ratio: {ideal_final_drive}")
        
        return ideal_final_drive
        
    except Exception as e:
        logger.error(f"Error optimizing final drive: {str(e)}")
        return 4.100  # Default if calculation fails

def generate_gear_speeds(
    gear_ratios: Dict[str, float], 
    final_drive: float,
    max_power_rpm: int,
    tire_diameter_inches: float
) -> Dict[str, float]:
    """
    Generate speed at max power RPM for each gear
    
    Args:
        gear_ratios: Dictionary of gear ratios
        final_drive: Final drive ratio
        max_power_rpm: RPM at maximum power
        tire_diameter_inches: Tire diameter in inches
        
    Returns:
        Dictionary of gear name to speed at max power RPM
    """
    try:
        gear_speeds = {}
        
        for gear_name, ratio in gear_ratios.items():
            # Calculate speed at max power RPM
            speed_mph, _ = calculate_speed_at_rpm(
                max_power_rpm, 
                ratio, 
                final_drive, 
                tire_diameter_inches
            )
            
            # Round to 1 decimal place
            gear_speeds[gear_name] = round(speed_mph, 1)
        
        logger.debug(f"Generated gear speeds: {gear_speeds}")
        
        return gear_speeds
        
    except Exception as e:
        logger.error(f"Error generating gear speeds: {str(e)}")
        return {}  # Empty dict if calculation fails

def generate_torque_curve(
    min_rpm: int,
    max_rpm: int,
    max_power_rpm: int,
    torque_kgfm: float,
    power_hp: int,
    num_points: int = 20
) -> List[List[float]]:
    """
    Generate a simulated torque curve based on engine parameters
    
    Args:
        min_rpm: Minimum engine RPM
        max_rpm: Maximum engine RPM
        max_power_rpm: RPM at maximum power
        torque_kgfm: Maximum torque in kg·m
        power_hp: Maximum power in HP
        num_points: Number of points to generate
        
    Returns:
        List of [rpm, torque] pairs
    """
    try:
        # Create the rpm range
        rpm_range = [min_rpm + (i * (max_rpm - min_rpm) / (num_points - 1)) for i in range(num_points)]
        
        # Calculate max torque RPM (typically lower than max power RPM)
        # As a rough approximation, max torque is around 50-70% of the way from min_rpm to max_power_rpm
        max_torque_rpm = min_rpm + (max_power_rpm - min_rpm) * 0.6
        
        # Generate the torque curve
        torque_curve = []
        
        for rpm in rpm_range:
            # Simplified torque curve model using a combination of quadratic functions
            if rpm <= max_torque_rpm:
                # Rising part of the curve (from min_rpm to max_torque_rpm)
                factor = (rpm - min_rpm) / (max_torque_rpm - min_rpm)
                torque = torque_kgfm * (1 - (1 - factor) ** 1.5)
            else:
                # Falling part of the curve (from max_torque_rpm to max_rpm)
                factor = (rpm - max_torque_rpm) / (max_rpm - max_torque_rpm)
                torque = torque_kgfm * (1 - factor ** 1.2)
            
            # Calculate power at this RPM (to ensure power curve peaks at max_power_rpm)
            power_factor = (rpm - min_rpm) / (max_rpm - min_rpm)
            power_modifier = 1 - ((rpm - max_power_rpm) / (max_rpm - min_rpm)) ** 2
            
            # Apply power modifier to fine-tune the torque curve
            if rpm > max_torque_rpm:
                torque *= max(0.5, power_modifier * 1.5)
            
            # Add point to the curve
            torque_curve.append([float(rpm), float(torque)])
        
        logger.debug(f"Generated torque curve with {len(torque_curve)} points")
        
        return torque_curve
        
    except Exception as e:
        logger.error(f"Error generating torque curve: {str(e)}")
        # Return a basic linear torque curve as fallback
        fallback_curve = []
        for i in range(num_points):
            rpm = min_rpm + (i * (max_rpm - min_rpm) / (num_points - 1))
            torque = torque_kgfm * (1 - abs((rpm - max_power_rpm) / (max_rpm - min_rpm)))
            fallback_curve.append([float(rpm), float(torque)])
        return fallback_curve