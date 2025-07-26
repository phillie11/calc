# spring_calc/views/gear_views.py
import logging
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from ..models import GearCalculation, Vehicle
from ..forms import GearCalculatorForm
from ..decorators import handle_view_exceptions, require_vehicle_selection, log_view_access

from services.gear_service import (
    calculate_optimal_gear_ratios,
    calculate_speed_at_rpm,
    estimate_acceleration,
    generate_torque_curve,
    generate_gear_speeds
)
logger = logging.getLogger(__name__)

@handle_view_exceptions
@log_view_access
def calculate_gears(request):
    """
    View to calculate optimal gear ratios
    """
    print("="*50)
    print(f"DEBUG: calculate_gears called with method {request.method}")
    if request.method == 'GET':
        print(f"DEBUG: GET parameters: {dict(request.GET)}")
    print("="*50)

    # Get vehicle from session if available
    vehicle_id = None
    vehicle_name = "Unknown Vehicle"
    vehicle = None

    if 'ocr_data' in request.session:
        gear_ratio = request.session['ocr_data'].get('gear_ratio')
        rpm = request.session['ocr_data'].get('rpm')  
        speed = request.session['ocr_data'].get('speed')
        final_drive = request.session['ocr_data'].get('final_drive')
        
        if 'vehicle' in request.session['ocr_data']:
            vehicle_id = request.session['ocr_data']['vehicle']
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id)
                vehicle_name = vehicle.name
            except Vehicle.DoesNotExist:
                pass
    
    # Also check spring_calculation_id and retrieve vehicle
    elif 'spring_calculation_id' in request.session:
        from ..models import SpringCalculation
        try:
            spring_calculation = SpringCalculation.objects.get(id=request.session['spring_calculation_id'])
            vehicle = spring_calculation.vehicle
            vehicle_id = vehicle.id
            vehicle_name = vehicle.name
        except SpringCalculation.DoesNotExist:
            pass

    
    # Check if we're coming back to this page from another page
    # In that case, try to load the previous calculation from session
    previous_calculation = None
    if 'gear_calculation_id' in request.session:
        try:
            previous_calculation = GearCalculation.objects.get(id=request.session['gear_calculation_id'])
        except GearCalculation.DoesNotExist:
            pass
    
    # Get OCR data from session if available
    ocr_data = request.session.get('ocr_data', {})
    
    # Extract gear ratios and final drive if available from OCR
    extracted_gear_ratios = ocr_data.get('gear_ratios', {})
    extracted_final_drive = ocr_data.get('final_drive')
    
    # Prepare initial form data with OCR values if available
    initial_data = {}
    for field in ['power_hp', 'torque_kgfm', 'min_rpm', 'max_rpm', 'max_power_rpm', 'num_gears']:
        if field in ocr_data:
            initial_data[field] = ocr_data[field]

    if request.method == 'GET' and 'ocr_data' in request.session:
        ocr_data = request.session['ocr_data']
        if 'tire_diameter_inches' in ocr_data:
            initial_data['tire_diameter_inches'] = ocr_data['tire_diameter_inches']
    
    # Check if we have GET parameters (high priority)
    if request.method == 'GET' and request.GET:
        # If there are GET parameters, pre-populate the form
        form = GearCalculatorForm(request.GET, vehicle_id=vehicle_id)
        return render(request, 'spring_calc/calculate_gears.html', {
            'form': form,
            'vehicle_name': vehicle_name,
            'previous_calculation': previous_calculation,
            'extracted_gear_ratios': extracted_gear_ratios,
            'extracted_final_drive': extracted_final_drive,
            'ocr_data': ocr_data 
        })
    
    if request.method == 'POST':
        form = GearCalculatorForm(request.POST, vehicle_id=vehicle_id)
        
        logger.debug(f"Form valid: {form.is_valid()}")
        if not form.is_valid():
            logger.debug(f"Form errors: {form.errors}")
            return render(request, 'spring_calc/calculate_gears.html', {
                'form': form,
                'vehicle_name': vehicle_name,
                'previous_calculation': previous_calculation,
                'extracted_gear_ratios': extracted_gear_ratios,
                'extracted_final_drive': extracted_final_drive,
                'ocr_data': ocr_data
            })
        
        try:
            # Get the form data but don't save yet
            calculation = form.save(commit=False)
            
            # Set the vehicle if not already set
            if not calculation.vehicle_id and vehicle_id:
                calculation.vehicle_id = vehicle_id
                logger.debug(f"Set vehicle_id to {vehicle_id}")
            
            # Log all parameters for debugging
            logger.debug("Calculation parameters:")
            logger.debug(f"- vehicle_id: {calculation.vehicle_id}")
            logger.debug(f"- top_speed_mph: {calculation.top_speed_mph}")
            logger.debug(f"- min_corner_speed_mph: {calculation.min_corner_speed_mph}")
            logger.debug(f"- tire_diameter_inches: {calculation.tire_diameter_inches}")
            logger.debug(f"- power_hp: {calculation.power_hp}")
            logger.debug(f"- torque_kgfm: {calculation.torque_kgfm}")
            logger.debug(f"- min_rpm: {calculation.min_rpm}")
            logger.debug(f"- max_rpm: {calculation.max_rpm}")
            logger.debug(f"- max_power_rpm: {calculation.max_power_rpm}")
            logger.debug(f"- num_gears: {calculation.num_gears}")
            logger.debug(f"- min_corner_gear: {calculation.min_corner_gear}")
            
            # Calculate optimal gear ratios and final drive
            gear_ratios, final_drive = calculate_optimal_gear_ratios(
                num_gears=calculation.num_gears,
                top_speed_mph=calculation.top_speed_mph,
                min_corner_speed_mph=calculation.min_corner_speed_mph,
                max_rpm=calculation.max_rpm,
                min_rpm=calculation.min_rpm,
                tire_diameter_inches=calculation.tire_diameter_inches,
                power_hp=calculation.power_hp,
                max_power_rpm=calculation.max_power_rpm,
                min_corner_gear=int(calculation.min_corner_gear)
            )
            
            # Calculate estimated acceleration
            acceleration_estimate = estimate_acceleration(
                power_hp=calculation.power_hp,
                weight_kg=vehicle.base_weight if vehicle else 1400,
                gear_ratios=gear_ratios,
                final_drive=final_drive,
                tire_diameter_inches=calculation.tire_diameter_inches
            )
            
            # Generate torque curve data
            torque_curve = generate_torque_curve(
                min_rpm=calculation.min_rpm,
                max_rpm=calculation.max_rpm,
                max_power_rpm=calculation.max_power_rpm,
                torque_kgfm=calculation.torque_kgfm,
                power_hp=calculation.power_hp
            )
            
            # Calculate gear speeds at max power RPM
            gear_speeds = generate_gear_speeds(
                gear_ratios=gear_ratios,
                final_drive=final_drive,
                max_power_rpm=calculation.max_power_rpm,
                tire_diameter_inches=calculation.tire_diameter_inches
            )
            
            # Calculate top speed for verification
            top_gear = list(gear_ratios.keys())[-1]
            top_gear_ratio = gear_ratios[top_gear]
            top_speed_mph, _ = calculate_speed_at_rpm(
                rpm=calculation.max_rpm,
                gear_ratio=top_gear_ratio,
                final_drive=final_drive,
                tire_diameter_inches=calculation.tire_diameter_inches
            )

            engine_data_table = None
            if 'ocr_data' in request.session and 'engine_data_table' in request.session['ocr_data']:
                engine_data_table = request.session['ocr_data']['engine_data_table']
            
            # Store the results
            calculation.gear_ratios = gear_ratios
            calculation.final_drive = final_drive
            calculation.torque_curve = torque_curve
            calculation.acceleration_estimate = acceleration_estimate
            calculation.top_speed_calculated = top_speed_mph
            
            # Save calculation to database
            calculation.save()
            
            # Store the calculation id in session
            request.session['gear_calculation_id'] = calculation.id
            
            # Success message
            messages.success(request, "Gear ratio calculation successful!")
            
            # Render the template with the results
            return render(request, 'spring_calc/calculate_gears.html', {
                'form': form,
                'calculation': calculation,
                'vehicle_name': vehicle_name,
                'gear_speeds': gear_speeds,
                'final_drive': final_drive,
                'top_speed_mph': top_speed_mph,
                'acceleration_estimate': acceleration_estimate
            })
            
        except Exception as e:
            # Detailed error handling for calculation errors
            logger.error(f"Error calculating gear ratios: {str(e)}", exc_info=True)
            messages.error(request, f"Error calculating gear ratios: {str(e)}")
            
            return render(request, 'spring_calc/calculate_gears.html', {
                'form': form,
                'vehicle_name': vehicle_name,
                'previous_calculation': previous_calculation,
                'extracted_gear_ratios': extracted_gear_ratios,
                'extracted_final_drive': extracted_final_drive,
                'ocr_data': ocr_data
            })
    
    # For GET requests, create an appropriate form
    if previous_calculation:
        # Use previous calculation to initialize form
        form = GearCalculatorForm(instance=previous_calculation)
    else:
        # Create a new form with vehicle_id and any initial data
        form = GearCalculatorForm(initial=initial_data, vehicle_id=vehicle_id)
    
    return render(request, 'spring_calc/calculate_gears.html', {
        'form': form,
        'vehicle_name': vehicle_name,
        'vehicle': vehicle,
        'previous_calculation': previous_calculation,
        'extracted_gear_ratios': extracted_gear_ratios,
        'extracted_final_drive': extracted_final_drive
    })