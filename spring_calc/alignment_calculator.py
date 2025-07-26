# spring_calc/alignment_calculator.py

def calculate_front_roll_bar_stiffness(rotational_g_values, high_speed_stability, arb_stiffness_multiplier, ou_multiplier):
    """
    Calculates front roll bar stiffness based on Excel formula:
    =MIN(10,(MAX(1,SUM(Setup!C11:C13)*-SUM(Setup!C10)*J22)*'Spring Calcs'!L45))
    
    Args:
    - rotational_g_values: List of rotational G values
    - high_speed_stability: High-speed stability value
    - stiffness_multiplier: Overall stiffness adjustment
    - ou_multiplier: Single Oversteer/Understeer multiplier
    """
    # Sum of rotational G values multiplied by negative high speed stability
    base_value = sum(rotational_g_values) * -high_speed_stability 
    
    # Apply stiffness multiplier and O/U multiplier (using same multiplier for front and rear)
    adjusted_value = base_value * arb_stiffness_multiplier * ou_multiplier
    
    # Constrain value between 1 and 10
    final_value = min(10, max(1, adjusted_value))
    
    return final_value

def calculate_rear_roll_bar_stiffness(rotational_g_values, low_speed_stability, high_speed_stability, arb_stiffness_multiplier, ou_multiplier):
    """
    Calculates rear roll bar stiffness based on Excel formula:
    =MIN(10,(MAX(1,SUM(Setup!C11:C13)*-SUM(Setup!C9:C10)*J22)*'Spring Calcs'!M45))
    
    Args:
    - rotational_g_values: List of rotational G values
    - low_speed_stability: Low-speed stability value
    - high_speed_stability: High-speed stability value
    - stiffness_multiplier: Overall stiffness adjustment
    - ou_multiplier: Single Oversteer/Understeer multiplier
    """
    # Sum of low speed and high speed stability
    stability_sum = low_speed_stability + high_speed_stability
    
    # Sum of rotational G values multiplied by negative stability sum
    base_value = sum(rotational_g_values) * -stability_sum
    
    # Apply stiffness multiplier and O/U multiplier (using same multiplier for front and rear)
    adjusted_value = base_value * arb_stiffness_multiplier * ou_multiplier
    
    # Constrain value between 1 and 10
    final_value = min(10, max(1, adjusted_value))
    
    return final_value

def calculate_front_camber(rotational_g_75mph, drivetrain_type, tire_wear_multiplier, track_type, front_weight_distribution):
    """
    Calculates the front camber angle based on the specified formula
    ((0.555 * 2.0 * 0.9 * 0.993878 * 1) + front_weight_distribution) * 1.2
    """
    # Drivetrain lookup table for front camber (column 2)
    drivetrain_lookup_table = {
        "4WD": 2.5,
        "FF": 1.5,
        "FR": 3.0,
        "MR": 2.0,
        "RR": 2.0
    }

    # Track type lookup table
    track_lookup_table = {
        "Fast": 0.9,
        "Technical": 1.1
    }

    # Alignment lookup table
    alignment_lookup_table = {
        x: y for x, y in zip(range(1, 51), [
            1.0, 0.993878, 0.987755, 0.981633, 0.97551, 0.969388, 0.963265, 0.957143,
            0.95102, 0.944898, 0.938776, 0.932653, 0.926531, 0.920408, 0.914286,
            0.908163, 0.902041, 0.895918, 0.889796, 0.883673, 0.877551, 0.871429,
            0.865306, 0.859184, 0.853061, 0.846939, 0.840816, 0.834694, 0.828571,
            0.822449, 0.816327, 0.810204, 0.804082, 0.797959, 0.791837, 0.785714,
            0.779592, 0.773469, 0.767347, 0.761224, 0.755102, 0.74898, 0.742857,
            0.736735, 0.730612, 0.72449, 0.718367, 0.712245, 0.706122, 0.7
        ])
    }

    # Get drivetrain multiplier
    drivetrain_multiplier = drivetrain_lookup_table.get(drivetrain_type, 1.0)

    # Get track multiplier
    track_multiplier = track_lookup_table.get(track_type, 1.0)

    # Get alignment adjustment from lookup table
    alignment_adjustment = alignment_lookup_table.get(tire_wear_multiplier, 1.0)

    # Calculate camber angle exactly as specified
    front_camber = ((rotational_g_75mph / 2) * 
        drivetrain_multiplier * 
        track_multiplier * 
        alignment_adjustment * 
        1) + front_weight_distribution

    # Multiply the entire result by 1.2 at the end
    front_camber *= 1.2

    return front_camber

def calculate_rear_camber(rotational_g_75mph, drivetrain_type, tire_wear_multiplier, track_type, front_weight_distribution):
    """
    Calculates the rear camber angle based on the specified formula
    ((0.555 * 2.0 * 0.9 * 0.993878 * 1) - front_weight_distribution + 1) * 1.2
    """
    # Drivetrain lookup table for rear camber (column 3)
    drivetrain_lookup_table = {
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

    # Alignment lookup table
    alignment_lookup_table = {
        x: y for x, y in zip(range(1, 51), [
            1.0, 0.993878, 0.987755, 0.981633, 0.97551, 0.969388, 0.963265, 0.957143,
            0.95102, 0.944898, 0.938776, 0.932653, 0.926531, 0.920408, 0.914286,
            0.908163, 0.902041, 0.895918, 0.889796, 0.883673, 0.877551, 0.871429,
            0.865306, 0.859184, 0.853061, 0.846939, 0.840816, 0.834694, 0.828571,
            0.822449, 0.816327, 0.810204, 0.804082, 0.797959, 0.791837, 0.785714,
            0.779592, 0.773469, 0.767347, 0.761224, 0.755102, 0.74898, 0.742857,
            0.736735, 0.730612, 0.72449, 0.718367, 0.712245, 0.706122, 0.7
        ])
    }

    # Get drivetrain multiplier
    drivetrain_multiplier = drivetrain_lookup_table.get(drivetrain_type, 1.0)

    # Get track multiplier
    track_multiplier = track_lookup_table.get(track_type, 1.0)

    # Get alignment adjustment from lookup table
    alignment_adjustment = alignment_lookup_table.get(tire_wear_multiplier, 1.0)

    # Calculate camber angle exactly as specified
    rear_camber = (
        ((rotational_g_75mph / 2) * 
        drivetrain_multiplier * 
        track_multiplier * 
        alignment_adjustment * 
        1) - front_weight_distribution + 1
    ) * 1.2

    return rear_camber

def calculate_front_toe(low_speed_stability, high_speed_stability, drivetrain_type, tire_wear_multiplier, track_type):
    # Drivetrain lookup table (column 2)
    drivetrain_lookup_table = {
        "4WD": 2.5,
        "FF": 1.5,
        "FR": 3.0,
        "MR": 2.0,
        "RR": 2.0
    }

    # Track type lookup table (multiplied by 3)
    track_lookup_table = {
        "Fast": 0.9 * 3,
        "Technical": 1.1 * 3
    }

    # Alignment lookup table
    alignment_lookup_table = {
        x: y for x, y in zip(range(1, 51), [
            1.0, 0.993878, 0.987755, 0.981633, 0.97551, 0.969388, 0.963265, 0.957143,
            0.95102, 0.944898, 0.938776, 0.932653, 0.926531, 0.920408, 0.914286,
            0.908163, 0.902041, 0.895918, 0.889796, 0.883673, 0.877551, 0.871429,
            0.865306, 0.859184, 0.853061, 0.846939, 0.840816, 0.834694, 0.828571,
            0.822449, 0.816327, 0.810204, 0.804082, 0.797959, 0.791837, 0.785714,
            0.779592, 0.773469, 0.767347, 0.761224, 0.755102, 0.74898, 0.742857,
            0.736735, 0.730612, 0.72449, 0.718367, 0.712245, 0.706122, 0.7
        ])
    }

    # Get drivetrain multiplier
    drivetrain_multiplier = drivetrain_lookup_table.get(drivetrain_type, 1.0)

    # Get track multiplier
    track_multiplier = track_lookup_table.get(track_type, 1.0)

    # Get alignment adjustment from lookup table
    alignment_adjustment = alignment_lookup_table.get(tire_wear_multiplier, 1.0)

    # Calculate toe exactly as in the Excel formula
    front_toe = (low_speed_stability / -(high_speed_stability * 40)) * \
                drivetrain_multiplier * \
                alignment_adjustment * \
                track_multiplier

    return front_toe

def calculate_rear_toe(high_speed_stability, low_speed_stability, drivetrain_type, tire_wear_multiplier, track_type):
    # Drivetrain lookup table (column 2)
    drivetrain_lookup_table = {
        "4WD": 2.5,
        "FF": 1.5,
        "FR": 3.0,
        "MR": 2.0,
        "RR": 2.0
    }

    # Track type lookup table (multiplied by 3)
    track_lookup_table = {
        "Fast": 0.9 * 3,
        "Technical": 1.1 * 3
    }

    # Alignment lookup table
    alignment_lookup_table = {
        x: y for x, y in zip(range(1, 51), [
            1.0, 0.993878, 0.987755, 0.981633, 0.97551, 0.969388, 0.963265, 0.957143,
            0.95102, 0.944898, 0.938776, 0.932653, 0.926531, 0.920408, 0.914286,
            0.908163, 0.902041, 0.895918, 0.889796, 0.883673, 0.877551, 0.871429,
            0.865306, 0.859184, 0.853061, 0.846939, 0.840816, 0.834694, 0.828571,
            0.822449, 0.816327, 0.810204, 0.804082, 0.797959, 0.791837, 0.785714,
            0.779592, 0.773469, 0.767347, 0.761224, 0.755102, 0.74898, 0.742857,
            0.736735, 0.730612, 0.72449, 0.718367, 0.712245, 0.706122, 0.7
        ])
    }

    # Get drivetrain multiplier
    drivetrain_multiplier = drivetrain_lookup_table.get(drivetrain_type, 1.0)

    # Get track multiplier
    track_multiplier = track_lookup_table.get(track_type, 1.0)

    # Get alignment adjustment from lookup table
    alignment_adjustment = alignment_lookup_table.get(tire_wear_multiplier, 1.0)

    # Calculate rear toe exactly as in the Excel formula
    rear_toe = -(high_speed_stability * low_speed_stability * 0.05) * \
               drivetrain_multiplier * \
               alignment_adjustment * \
               track_multiplier + 0.2

    return rear_toe