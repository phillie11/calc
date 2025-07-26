# services/calculation_service.py
import math
import logging
from typing import Dict, Tuple, List, Union, Optional, Any

logger = logging.getLogger(__name__)

# Constants for calculations
# Tire type multiplier tables
TIRE_SPRING_MULTIPLIER_TABLE = {
    # Sports series
    'SM': 1.0,      # Sport: Medium (reference)
    'SH': 0.99,     # Sport: Hard (minus 1% from SM)
    'SS': 1.01,     # Sport: Soft (plus 1% from SM)
    
    # Comfort series (each 1% less than the previous)
    'CS': 0.98,     # Comfort: Soft (minus 1% from SH)
    'CM': 0.97,     # Comfort: Medium (minus 1% from CS)
    'CH': 0.96,     # Comfort: Hard (minus 1% from CM)
    
    # Racing series (each 1% more than the previous)
    'RM': 1.02,     # Racing: Medium (plus 1% from SS)
    'RH': 1.01,     # Racing: Hard (minus 1% from RM)
    'RS': 1.03,     # Racing: Soft (plus 1% from RM)
    'RI': 1.0,      # Racing: Intermediate (same as SM)
    'RW': 0.98,     # Racing: Heavy Wet (same as CS)
}

# Smaller multiplier differentials for damping, roll bars, and camber (0.5% steps)
DAMPER_ROLLBAR_CAMBER_MULTIPLIER_TABLE = {
    # Sports series
    'SM': 1.0,       # Sport: Medium (reference)
    'SH': 0.995,     # Sport: Hard (minus 0.5% from SM)
    'SS': 1.005,     # Sport: Soft (plus 0.5% from SM)
    
    # Comfort series (each 0.5% less than the previous)
    'CS': 0.99,      # Comfort: Soft (minus 0.5% from SH)
    'CM': 0.985,     # Comfort: Medium (minus 0.5% from CS)
    'CH': 0.98,      # Comfort: Hard (minus 0.5% from CM)
    
    # Racing series (each 0.5% more than the previous)
    'RM': 1.01,      # Racing: Medium (plus 0.5% from SS)
    'RH': 1.005,     # Racing: Hard (minus 0.5% from RM)
    'RS': 1.015,     # Racing: Soft (plus 0.5% from RM)
    'RI': 1.0,       # Racing: Intermediate (same as SM)
    'RW': 0.99,      # Racing: Heavy Wet (same as CS)
}

# Multiplier for toe settings (0.1% steps)
TOE_MULTIPLIER_TABLE = {
    # Sports series
    'SM': 1.0,         # Sport: Medium (reference)
    'SH': 0.999,       # Sport: Hard (minus 0.1% from SM)
    'SS': 1.001,       # Sport: Soft (plus 0.1% from SM)
    
    # Comfort series (each 0.1% less than the previous)
    'CS': 0.998,       # Comfort: Soft (minus 0.1% from SH)
    'CM': 0.997,       # Comfort: Medium (minus 0.1% from CS)
    'CH': 0.996,       # Comfort: Hard (minus 0.1% from CM)
    
    # Racing series (each 0.1% more than the previous)
    'RM': 1.002,       # Racing: Medium (plus 0.1% from SS)
    'RH': 1.001,       # Racing: Hard (minus 0.1% from RM)
    'RS': 1.003,       # Racing: Soft (plus 0.1% from RM)
    'RI': 1.0,         # Racing: Intermediate (same as SM)
    'RW': 0.998,       # Racing: Heavy Wet (same as CS)
}

# Unsprung weight table based on drivetrain
UNSPRUNG_WEIGHT_TABLE = {
    "4WD": 55, 
    "FF": 55, 
    "FR": 45, 
    "MR": 45, 
    "RR": 45
}

# Car type multiplier table for spring frequency
CAR_TYPE_MULTIPLIER_TABLE = {
    "ROAD": 1.3, 
    "GR4": 1.333, 
    "RACE": 1.333, 
    "VGT": 1.666, 
    "FAN": 2.0
}

# Spring frequency offset table
SPRING_FREQUENCY_OFFSET_TABLE = {
    -5: 0.5, -4: 0.6, -3: 0.7, -2: 0.8, -1: 0.9,
    0: 1.0, 1: 1.1, 2: 1.2, 3: 1.3, 4: 1.4,
    5: 1.5, 6: 1.6
}

# Oversteer/Understeer multiplier table
OU_MULTIPLIER_TABLE = {
    -5: [1.5, 0.5],  # [front, rear] - Understeer
    -4: [1.4, 0.6],
    -3: [1.3, 0.7],
    -2: [1.2, 0.8],
    -1: [1.1, 0.9],
    0: [1.0, 1.0],   # Neutral
    1: [0.9, 1.1],
    2: [0.8, 1.2],
    3: [0.7, 1.3],
    4: [0.6, 1.4],
    5: [0.5, 1.5]    # Oversteer
}

# Corner entry adjustment table
CORNER_ENTRY_ADJUSTMENT_TABLE = {
    # For understeer on entry (need more front grip):
    -5: {"front_compression": 0.80, "front_rebound": 1.20, "rear_compression": 1.20, "rear_rebound": 0.80},
    -4: {"front_compression": 0.85, "front_rebound": 1.15, "rear_compression": 1.15, "rear_rebound": 0.85},
    -3: {"front_compression": 0.90, "front_rebound": 1.10, "rear_compression": 1.10, "rear_rebound": 0.90},
    -2: {"front_compression": 0.95, "front_rebound": 1.05, "rear_compression": 1.05, "rear_rebound": 0.95},
    -1: {"front_compression": 0.98, "front_rebound": 1.02, "rear_compression": 1.02, "rear_rebound": 0.98},
    # Neutral
    0: {"front_compression": 1.00, "front_rebound": 1.00, "rear_compression": 1.00, "rear_rebound": 1.00},
    # For oversteer on entry (need more rear grip):
    1: {"front_compression": 1.02, "front_rebound": 0.98, "rear_compression": 0.98, "rear_rebound": 1.02},
    2: {"front_compression": 1.05, "front_rebound": 0.95, "rear_compression": 0.95, "rear_rebound": 1.05},
    3: {"front_compression": 1.10, "front_rebound": 0.90, "rear_compression": 0.90, "rear_rebound": 1.10},
    4: {"front_compression": 1.15, "front_rebound": 0.85, "rear_compression": 0.85, "rear_rebound": 1.15},
    5: {"front_compression": 1.20, "front_rebound": 0.80, "rear_compression": 0.80, "rear_rebound": 1.20}
}

# Corner exit adjustment table
CORNER_EXIT_ADJUSTMENT_TABLE = {
    # For understeer on exit (need to slow weight transfer from front):
    -5: {"front_compression": 1.05, "front_rebound": 1.20, "rear_compression": 0.80, "rear_rebound": 0.95},
    -4: {"front_compression": 1.04, "front_rebound": 1.15, "rear_compression": 0.85, "rear_rebound": 0.96},
    -3: {"front_compression": 1.03, "front_rebound": 1.10, "rear_compression": 0.90, "rear_rebound": 0.97},
    -2: {"front_compression": 1.02, "front_rebound": 1.05, "rear_compression": 0.95, "rear_rebound": 0.98},
    -1: {"front_compression": 1.01, "front_rebound": 1.02, "rear_compression": 0.98, "rear_rebound": 0.99},
    # Neutral
    0: {"front_compression": 1.00, "front_rebound": 1.00, "rear_compression": 1.00, "rear_rebound": 1.00},
    # For oversteer on exit (need to reduce rear spring effect):
    1: {"front_compression": 0.99, "front_rebound": 0.98, "rear_compression": 0.95, "rear_rebound": 1.01},
    2: {"front_compression": 0.98, "front_rebound": 0.95, "rear_compression": 0.90, "rear_rebound": 1.02},
    3: {"front_compression": 0.97, "front_rebound": 0.90, "rear_compression": 0.85, "rear_rebound": 1.03},
    4: {"front_compression": 0.96, "front_rebound": 0.85, "rear_compression": 0.80, "rear_rebound": 1.04},
    5: {"front_compression": 0.95, "front_rebound": 0.80, "rear_compression": 0.75, "rear_rebound": 1.05}
}

def calculate_spring_rates(
    vehicle_weight: int, 
    front_weight_distribution: float, 
    front_ride_height: int, 
    rear_ride_height: int, 
    front_lever_ratio: float, 
    rear_lever_ratio: float,
    front_downforce: int = 0,
    rear_downforce: int = 0,
    stiffness_multiplier: float = 1.0,
    front_tire_type: str = 'RM',
    rear_tire_type: str = 'RM',
    drivetrain: str = 'FR'
) -> Tuple[float, float]:
    """
    Calculate spring rates based on vehicle parameters
    
    Args:
        vehicle_weight: Total vehicle weight in kg
        front_weight_distribution: Front weight percentage (0-100)
        front_ride_height: Front ride height in mm
        rear_ride_height: Rear ride height in mm
        front_lever_ratio: Front suspension lever ratio
        rear_lever_ratio: Rear suspension lever ratio
        front_downforce: Front downforce value
        rear_downforce: Rear downforce value
        stiffness_multiplier: Overall stiffness adjustment
        front_tire_type: Front tire type code (e.g., 'RM')
        rear_tire_type: Rear tire type code (e.g., 'RM')
        drivetrain: Drivetrain type code
        
    Returns:
        Tuple of (front_spring_rate, rear_spring_rate) in N/mm
    """
    try:
        logger.debug(f"Calculating spring rates for vehicle weight {vehicle_weight}kg, "
                    f"distribution {front_weight_distribution}%, ride heights F:{front_ride_height}mm R:{rear_ride_height}mm")
        
        # Convert front weight distribution to decimal
        front_weight_ratio = front_weight_distribution / 100.0
        
        # Get unsprung weights
        unsprung_front_weight = UNSPRUNG_WEIGHT_TABLE.get(drivetrain, 45)
        unsprung_rear_weight = UNSPRUNG_WEIGHT_TABLE.get(drivetrain, 45)
        
        # Calculate mass distribution
        front_mass = vehicle_weight * front_weight_ratio
        rear_mass = vehicle_weight * (1 - front_weight_ratio)
        
        # Calculate loads taking into account downforce and unsprung weight
        front_load = (front_mass + (front_downforce / 2) - unsprung_front_weight) / front_lever_ratio
        rear_load = (rear_mass + (rear_downforce / 2) - unsprung_rear_weight) / rear_lever_ratio
        
        # Convert to Newtons
        front_load_n = front_load * 9.81
        rear_load_n = rear_load * 9.81
        
        # Convert ride height to meters
        front_ride_height_m = max(1, front_ride_height) / 1000
        rear_ride_height_m = max(1, rear_ride_height) / 1000
        
        # Calculate spring rates in N/m
        front_spring_rate_nm = front_load_n / front_ride_height_m
        rear_spring_rate_nm = rear_load_n / rear_ride_height_m
        
        # Get tire multipliers
        front_tire_multiplier = TIRE_SPRING_MULTIPLIER_TABLE.get(front_tire_type, 1.0)
        rear_tire_multiplier = TIRE_SPRING_MULTIPLIER_TABLE.get(rear_tire_type, 1.0)
        
        # Apply stiffness multiplier and tire type multiplier
        adjusted_front_spring_rate = front_spring_rate_nm * stiffness_multiplier * front_tire_multiplier
        adjusted_rear_spring_rate = rear_spring_rate_nm * stiffness_multiplier * rear_tire_multiplier
        
        # Convert spring rates from N/m to N/mm for GT7
        front_spring_rate_nmm = adjusted_front_spring_rate / 1000
        rear_spring_rate_nmm = adjusted_rear_spring_rate / 1000
        
        # Round to GT7 increments
        if front_spring_rate_nmm < 10:
            front_spring_rate_gt7 = round(front_spring_rate_nmm * 10) / 10
        elif front_spring_rate_nmm < 30:
            front_spring_rate_gt7 = round(front_spring_rate_nmm * 2) / 2
        else:
            front_spring_rate_gt7 = round(front_spring_rate_nmm)
            
        if rear_spring_rate_nmm < 10:
            rear_spring_rate_gt7 = round(rear_spring_rate_nmm * 10) / 10
        elif rear_spring_rate_nmm < 30:
            rear_spring_rate_gt7 = round(rear_spring_rate_nmm * 2) / 2
        else:
            rear_spring_rate_gt7 = round(rear_spring_rate_nmm)
            
        logger.debug(f"Calculated spring rates: Front = {front_spring_rate_gt7} N/mm, Rear = {rear_spring_rate_gt7} N/mm")
        
        return front_spring_rate_gt7, rear_spring_rate_gt7
        
    except Exception as e:
        logger.error(f"Error calculating spring rates: {str(e)}")
        # Return default values in case of error
        return 7.0, 7.0

def calculate_spring_frequencies(
    spring_rates: Tuple[float, float],
    vehicle_weight: int,
    front_weight_distribution: float,
    car_type: str,
    spring_frequency_offset: int
) -> Tuple[float, float]:
    """
    Calculate spring frequencies in Hz based on spring rates
    
    Args:
        spring_rates: Tuple of (front_spring_rate, rear_spring_rate) in N/mm
        vehicle_weight: Total vehicle weight in kg
        front_weight_distribution: Front weight percentage (0-100)
        car_type: Vehicle car type code (e.g., 'ROAD', 'GR4')
        spring_frequency_offset: Spring frequency offset value (-5 to 6)
        
    Returns:
        Tuple of (front_frequency, rear_frequency) in Hz
    """
    try:
        # Unpack spring rates
        front_spring_rate, rear_spring_rate = spring_rates
        
        # Convert front weight distribution to decimal
        front_weight_ratio = front_weight_distribution / 100.0
        
        # Calculate mass distribution
        front_mass = vehicle_weight * front_weight_ratio
        rear_mass = vehicle_weight * (1 - front_weight_ratio)
        
        # Convert spring rates from N/mm to N/m
        front_spring_rate_nm = front_spring_rate * 1000
        rear_spring_rate_nm = rear_spring_rate * 1000
        
        # Calculate raw spring frequencies
        front_spring_frequency = math.sqrt(front_spring_rate_nm / front_mass)
        rear_spring_frequency = math.sqrt(rear_spring_rate_nm / rear_mass)
        
        # Convert to Hz
        front_frequency_hz = (1 / (2 * math.pi)) * front_spring_frequency
        rear_frequency_hz = (1 / (2 * math.pi)) * rear_spring_frequency
        
        # Apply car type multiplier
        car_type_multiplier = CAR_TYPE_MULTIPLIER_TABLE.get(car_type, 1.333)
        
        # Apply frequency offset multiplier
        offset_multiplier = SPRING_FREQUENCY_OFFSET_TABLE.get(spring_frequency_offset, 1.0)
        
        # Calculate final frequencies
        final_front_frequency = front_frequency_hz * car_type_multiplier * offset_multiplier
        final_rear_frequency = rear_frequency_hz * car_type_multiplier * offset_multiplier
        
        # Round to 2 decimal places
        final_front_frequency = round(final_front_frequency, 2)
        final_rear_frequency = round(final_rear_frequency, 2)
        
        logger.debug(f"Calculated spring frequencies: Front = {final_front_frequency} Hz, Rear = {final_rear_frequency} Hz")
        
        return final_front_frequency, final_rear_frequency
        
    except Exception as e:
        logger.error(f"Error calculating spring frequencies: {str(e)}")
        # Return default values in case of error
        return 2.50, 2.50

def calculate_damper_settings(
    spring_rates: Tuple[float, float],
    vehicle_weight: int,
    front_weight_distribution: float,
    corner_entry_adjustment: int,
    corner_exit_adjustment: int,
    front_tire_type: str = 'RM',
    rear_tire_type: str = 'RM'
) -> Dict[str, int]:
    """
    Calculate optimal damper settings based on spring rates
    
    Args:
        spring_rates: Tuple of (front_spring_rate, rear_spring_rate) in N/mm
        vehicle_weight: Total vehicle weight in kg
        front_weight_distribution: Front weight percentage (0-100)
        corner_entry_adjustment: Corner entry adjustment value (-5 to 5)
        corner_exit_adjustment: Corner exit adjustment value (-5 to 5)
        front_tire_type: Front tire type code (e.g., 'RM')
        rear_tire_type: Rear tire type code (e.g., 'RM')
        
    Returns:
        Dict containing damper settings
    """
    try:
        # Unpack spring rates
        front_spring_rate, rear_spring_rate = spring_rates
        
        # Convert front weight distribution to decimal
        front_weight_ratio = front_weight_distribution / 100.0
        
        # Calculate mass distribution
        front_mass = vehicle_weight * front_weight_ratio
        rear_mass = vehicle_weight * (1 - front_weight_ratio)
        
        # Convert spring rates from N/mm to N/m
        front_spring_rate_nm = front_spring_rate * 1000
        rear_spring_rate_nm = rear_spring_rate * 1000
        
        # Calculate critical damping
        front_critical_damping = 2 * math.sqrt(front_spring_rate_nm * front_mass)
        rear_critical_damping = 2 * math.sqrt(rear_spring_rate_nm * rear_mass)
        
        # Use half of critical damping as baseline
        front_critical_damping_half = front_critical_damping * 0.5
        rear_critical_damping_half = rear_critical_damping * 0.5
        
        # Get tire multipliers
        front_tire_damper_multiplier = DAMPER_ROLLBAR_CAMBER_MULTIPLIER_TABLE.get(front_tire_type, 1.0)
        rear_tire_damper_multiplier = DAMPER_ROLLBAR_CAMBER_MULTIPLIER_TABLE.get(rear_tire_type, 1.0)
        
        # Get corner adjustment multipliers
        entry_multipliers = CORNER_ENTRY_ADJUSTMENT_TABLE.get(corner_entry_adjustment, CORNER_ENTRY_ADJUSTMENT_TABLE[0])
        exit_multipliers = CORNER_EXIT_ADJUSTMENT_TABLE.get(corner_exit_adjustment, CORNER_EXIT_ADJUSTMENT_TABLE[0])
        
        # Calculate damper settings for corner entry
        front_compression_entry = int((20 + front_critical_damping_half / 1000) * 
                                    front_tire_damper_multiplier * 
                                    entry_multipliers["front_compression"])
        
        rear_compression_entry = int((20 + rear_critical_damping_half / 1000) * 
                                   rear_tire_damper_multiplier * 
                                   entry_multipliers["rear_compression"])
        
        front_extension_entry = int((30 + front_critical_damping_half / 800) * 
                                  front_tire_damper_multiplier * 
                                  entry_multipliers["front_rebound"])
        
        rear_extension_entry = int((30 + rear_critical_damping_half / 800) * 
                                 rear_tire_damper_multiplier * 
                                 entry_multipliers["rear_rebound"])
        
        # Calculate damper settings for corner exit
        front_compression_exit = int((20 + front_critical_damping_half / 1000) * 
                                   front_tire_damper_multiplier * 
                                   exit_multipliers["front_compression"])
        
        rear_compression_exit = int((20 + rear_critical_damping_half / 1000) * 
                                  rear_tire_damper_multiplier * 
                                  exit_multipliers["rear_compression"])
        
        front_extension_exit = int((30 + front_critical_damping_half / 800) * 
                                 front_tire_damper_multiplier * 
                                 exit_multipliers["front_rebound"])
        
        rear_extension_exit = int((30 + rear_critical_damping_half / 800) * 
                               rear_tire_damper_multiplier * 
                               exit_multipliers["rear_rebound"])
        
        # Combine entry and exit settings (weighting toward the more extreme value)
        front_compression = int((front_compression_entry + front_compression_exit) / 2)
        rear_compression = int((rear_compression_entry + rear_compression_exit) / 2)
        front_extension = int((front_extension_entry + front_extension_exit) / 2)
        rear_extension = int((rear_extension_entry + rear_extension_exit) / 2)
        
        # Ensure values stay within bounds
        front_compression = max(20, min(40, front_compression))
        rear_compression = max(20, min(40, rear_compression))
        front_extension = max(30, min(50, front_extension))
        rear_extension = max(30, min(50, rear_extension))
        
        logger.debug(f"Calculated damper settings: Front compression = {front_compression}, Front extension = {front_extension}, "
                    f"Rear compression = {rear_compression}, Rear extension = {rear_extension}")
        
        return {
            'front_compression': front_compression,
            'front_extension': front_extension,
            'rear_compression': rear_compression,
            'rear_extension': rear_extension
        }
        
    except Exception as e:
        logger.error(f"Error calculating damper settings: {str(e)}")
        # Return default values in case of error
        return {
            'front_compression': 30,
            'front_extension': 40,
            'rear_compression': 30,
            'rear_extension': 40
        }

def calculate_roll_bar_stiffness(
    rotational_g_values: List[float],
    low_speed_stability: float,
    high_speed_stability: float,
    arb_stiffness_multiplier: float,
    ou_adjustment: int
) -> Tuple[float, float]:
    """
    Calculate front and rear roll bar stiffness
    
    Args:
        rotational_g_values: List of rotational G values [40mph, 75mph, 150mph]
        low_speed_stability: Low-speed stability value (-1 to 1)
        high_speed_stability: High-speed stability value (-1 to 1)
        arb_stiffness_multiplier: Overall anti-roll bar stiffness multiplier
        ou_adjustment: Oversteer/Understeer adjustment value (-5 to 5)
        
    Returns:
        Tuple of (front_roll_bar, rear_roll_bar) values
    """
    try:
        # Get O/U multipliers
        front_ou_multiplier, rear_ou_multiplier = OU_MULTIPLIER_TABLE.get(ou_adjustment, [1.0, 1.0])
        
        # Calculate front roll bar
        front_base_value = sum(rotational_g_values) * -high_speed_stability
        front_adjusted_value = front_base_value * arb_stiffness_multiplier * front_ou_multiplier
        front_roll_bar = min(10, max(1, front_adjusted_value))
        
        # Calculate rear roll bar
        stability_sum = low_speed_stability + high_speed_stability
        rear_base_value = sum(rotational_g_values) * -stability_sum
        rear_adjusted_value = rear_base_value * arb_stiffness_multiplier * rear_ou_multiplier
        rear_roll_bar = min(10, max(1, rear_adjusted_value))
        
        logger.debug(f"Calculated roll bar stiffness: Front = {front_roll_bar}, Rear = {rear_roll_bar}")
        
        return front_roll_bar, rear_roll_bar
        
    except Exception as e:
        logger.error(f"Error calculating roll bar stiffness: {str(e)}")
        # Return default values in case of error
        return 5.0, 5.0

def calculate_alignment_settings(
    rotational_g_75mph: float,
    drivetrain: str,
    tire_wear_multiplier: int,
    track_type: str,
    front_weight_distribution: float,
    low_speed_stability: float,
    high_speed_stability: float,
    front_tire_type: str = 'RM',
    rear_tire_type: str = 'RM'
) -> Dict[str, float]:
    """
    Calculate camber and toe settings
    
    Args:
        rotational_g_75mph: Rotational G value at 75mph
        drivetrain: Drivetrain type code
        tire_wear_multiplier: Tire wear multiplier value (0-50)
        track_type: Track type ("Fast" or "Technical")
        front_weight_distribution: Front weight percentage (0-100)
        low_speed_stability: Low-speed stability value (-1 to 1)
        high_speed_stability: High-speed stability value (-1 to 1)
        front_tire_type: Front tire type code (e.g., 'RM')
        rear_tire_type: Rear tire type code (e.g., 'RM')
        
    Returns:
        Dict containing front_camber, rear_camber, front_toe, rear_toe values
    """
    try:
        # Drivetrain lookup tables
        front_camber_drivetrain_table = {
            "4WD": 2.5,
            "FF": 1.5,
            "FR": 3.0,
            "MR": 2.0,
            "RR": 2.0
        }
        
        rear_camber_drivetrain_table = {
            "4WD": 2.5,
            "FF": 3.0,
            "FR": 1.5,
            "MR": 2.5,
            "RR": 2.5
        }
        
        # Track type lookup table
        track_lookup_table = {
            "Fast": 0.9,
            "Technical": 1.1
        }
        
        # Alignment lookup table for tire wear
        alignment_lookup_factor = 1.0
        if 1 <= tire_wear_multiplier <= 50:
            alignment_lookup_factor = 1.0 - (0.3 * tire_wear_multiplier / 50)
        
        # Get multipliers
        front_drivetrain_multiplier = front_camber_drivetrain_table.get(drivetrain, 1.0)
        rear_drivetrain_multiplier = rear_camber_drivetrain_table.get(drivetrain, 1.0)
        track_multiplier = track_lookup_table.get(track_type, 1.0)
        
        # Get tire multipliers
        front_tire_multiplier = DAMPER_ROLLBAR_CAMBER_MULTIPLIER_TABLE.get(front_tire_type, 1.0)
        rear_tire_multiplier = DAMPER_ROLLBAR_CAMBER_MULTIPLIER_TABLE.get(rear_tire_type, 1.0)
        front_toe_multiplier = TOE_MULTIPLIER_TABLE.get(front_tire_type, 1.0)
        rear_toe_multiplier = TOE_MULTIPLIER_TABLE.get(rear_tire_type, 1.0)
        
        # Convert front weight distribution to decimal
        front_weight_ratio = front_weight_distribution / 100.0
        
        # Calculate front camber
        front_camber_base = ((rotational_g_75mph / 2) * 
                           front_drivetrain_multiplier * 
                           track_multiplier * 
                           alignment_lookup_factor * 
                           1) + front_weight_ratio
        front_camber = front_camber_base * 1.2 * front_tire_multiplier
        
        # Calculate rear camber
        rear_camber_base = (
            ((rotational_g_75mph / 2) * 
            rear_drivetrain_multiplier * 
            track_multiplier * 
            alignment_lookup_factor * 
            1) - front_weight_ratio + 1
        ) * 1.2
        rear_camber = rear_camber_base * rear_tire_multiplier
        
        # Calculate front toe
        front_toe_base = (low_speed_stability / -(high_speed_stability * 40)) * \
                       front_drivetrain_multiplier * \
                       alignment_lookup_factor * \
                       (track_multiplier * 3)
        front_toe = front_toe_base * front_toe_multiplier
        
        # Calculate rear toe
        rear_toe_base = -(high_speed_stability * low_speed_stability * 0.05) * \
                      rear_drivetrain_multiplier * \
                      alignment_lookup_factor * \
                      (track_multiplier * 3) + 0.2
        rear_toe = rear_toe_base * rear_toe_multiplier
        
        # Round values for display
        front_camber = round(front_camber, 1)
        rear_camber = round(rear_camber, 1)
        front_toe = round(front_toe, 2)
        rear_toe = round(rear_toe, 2)
        
        logger.debug(f"Calculated alignment settings: Front camber = {front_camber}, Rear camber = {rear_camber}, "
                   f"Front toe = {front_toe}, Rear toe = {rear_toe}")
        
        return {
            'front_camber': front_camber,
            'rear_camber': rear_camber,
            'front_toe': front_toe,
            'rear_toe': rear_toe
        }
        
    except Exception as e:
        logger.error(f"Error calculating alignment settings: {str(e)}")
        # Return default values in case of error
        return {
            'front_camber': -3.0,
            'rear_camber': -2.0,
            'front_toe': 0.05,
            'rear_toe': 0.20
        }

def calculate_tire_diameter(gear_ratio: float, rpm: int, speed: float, final_drive: float) -> float:
    """
    Calculate tire diameter based on speed, RPM, gear ratio and final drive
    
    Args:
        gear_ratio: Current gear ratio
        rpm: Engine RPM
        speed: Vehicle speed in km/h
        final_drive: Final drive ratio
        
    Returns:
        Calculated tire diameter in inches
    """
    try:
        if not gear_ratio or not rpm or not speed or not final_drive:
            return 26.0  # Default value
            
        # Convert speed to km/h if it's not already
        speed_kmh = float(speed)
        
        # Formula: Tire Diameter (inches) = (Speed in km/h * 1000) / ((RPM / (gear ratio * final drive)) * 60 * π) * 39.37
        numerator = speed_kmh * 1000
        denominator = (float(rpm) / (float(gear_ratio) * float(final_drive))) * 60 * math.pi
        diameter_inches = (numerator / denominator) * 39.37
        
        # Validate result is reasonable (between 15 and 35 inches)
        if 15 <= diameter_inches <= 35:
            return round(diameter_inches, 2)
        else:
            logger.warning(f"Calculated tire diameter {diameter_inches} is outside reasonable range, using default")
            return 26.0
            
    except Exception as e:
        logger.error(f"Error calculating tire diameter: {str(e)}")
        return 26.0  # Default value