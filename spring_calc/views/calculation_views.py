# spring_calc/views/calculation_views.py
import logging
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings

from ..models import SpringCalculation, TireSizeCalculation, Vehicle
from ..forms import SpringCalculatorForm, TireSizeCalculatorForm
from ..decorators import handle_view_exceptions, require_vehicle_selection, log_view_access

from services.calculation_service import (
    calculate_spring_rates, 
    calculate_spring_frequencies,
    calculate_damper_settings,
    calculate_roll_bar_stiffness,
    calculate_alignment_settings,
    calculate_tire_diameter
)

logger = logging.getLogger(__name__)

@handle_view_exceptions
@log_view_access
def calculate_springs(request):
    """
    View to calculate optimal suspension settings
    """
    # Check if we have a previous calculation in the session
    previous_calculation = None
    if 'spring_calculation_id' in request.session:
        try:
            previous_calculation = SpringCalculation.objects.get(id=request.session['spring_calculation_id'])
        except SpringCalculation.DoesNotExist:
            pass
            
    # Check if we have GET parameters (high priority)
    if request.method == 'GET' and request.GET:
        # If there are GET parameters, pre-populate the form
        form = SpringCalculatorForm(request.GET)
        return render(request, 'spring_calc/calculate.html', {
            'form': form
        })
    
    # For GET requests with OCR data in session
    if request.method == 'GET' and 'ocr_data' in request.session:
        # Get OCR data fields relevant to suspension calculation
        ocr_data = request.session['ocr_data']
        
        # Create a dictionary with only the fields that match the form
        form_fields = [field.name for field in SpringCalculation._meta.get_fields()]
        initial_data = {k: v for k, v in ocr_data.items() if k in form_fields}
        
        # Special handling for vehicle ID if needed
        if 'vehicle' in ocr_data and isinstance(ocr_data['vehicle'], int):
            try:
                vehicle = Vehicle.objects.get(id=ocr_data['vehicle'])
                initial_data['vehicle'] = vehicle
            except Vehicle.DoesNotExist:
                pass
        
        # Create form with initial data
        form = SpringCalculatorForm(initial=initial_data)
        return render(request, 'spring_calc/calculate.html', {
            'form': form
        })
    
    if request.method == 'POST':
        form = SpringCalculatorForm(request.POST)
        if form.is_valid():
            # Get the form data but don't save yet
            calculation = form.save(commit=False)

            # Get data from form
            vehicle = form.cleaned_data['vehicle']
            front_lever_ratio = vehicle.lever_ratio_front
            rear_lever_ratio = vehicle.lever_ratio_rear
            vehicle_weight = form.cleaned_data['vehicle_weight']
            front_weight_distribution = form.cleaned_data['front_weight_distribution']
            front_ride_height = form.cleaned_data['front_ride_height']
            rear_ride_height = form.cleaned_data['rear_ride_height']
            front_downforce = form.cleaned_data['front_downforce']
            rear_downforce = form.cleaned_data['rear_downforce']
            front_tires = form.cleaned_data['front_tires']
            rear_tires = form.cleaned_data['rear_tires']
            stiffness_multiplier = form.cleaned_data['stiffness_multiplier']
            spring_frequency_offset = form.cleaned_data['spring_frequency_offset']
            arb_stiffness_multiplier = form.cleaned_data['arb_stiffness_multiplier']
            ou_adjustment = form.cleaned_data['ou_adjustment']
            corner_entry_adjustment = form.cleaned_data['corner_entry_adjustment']
            corner_exit_adjustment = form.cleaned_data['corner_exit_adjustment']
            rotational_g_values = [
                form.cleaned_data['rotational_g_40mph'],
                form.cleaned_data['rotational_g_75mph'],
                form.cleaned_data['rotational_g_150mph']
            ]
            track_type = form.cleaned_data['track_type']
            tire_wear_multiplier = form.cleaned_data['tire_wear_multiplier']
            low_speed_stability = form.cleaned_data['low_speed_stability']
            high_speed_stability = form.cleaned_data['high_speed_stability']
            
            try:
                logger.debug("Calculating spring rates")
                
                # Calculate spring rates
                front_spring_rate, rear_spring_rate = calculate_spring_rates(
                    vehicle_weight=vehicle_weight,
                    front_weight_distribution=front_weight_distribution,
                    front_ride_height=front_ride_height,
                    rear_ride_height=rear_ride_height,
                    front_lever_ratio=front_lever_ratio,
                    rear_lever_ratio=rear_lever_ratio,
                    front_downforce=front_downforce,
                    rear_downforce=rear_downforce,
                    stiffness_multiplier=stiffness_multiplier,
                    front_tire_type=front_tires,
                    rear_tire_type=rear_tires,
                    drivetrain=vehicle.drivetrain
                )
                
                # Calculate spring frequencies
                front_spring_frequency, rear_spring_frequency = calculate_spring_frequencies(
                    spring_rates=(front_spring_rate, rear_spring_rate),
                    vehicle_weight=vehicle_weight,
                    front_weight_distribution=front_weight_distribution,
                    car_type=vehicle.car_type,
                    spring_frequency_offset=spring_frequency_offset
                )
                
                # Calculate damper settings
                damper_settings = calculate_damper_settings(
                    spring_rates=(front_spring_rate, rear_spring_rate),
                    vehicle_weight=vehicle_weight,
                    front_weight_distribution=front_weight_distribution,
                    corner_entry_adjustment=corner_entry_adjustment,
                    corner_exit_adjustment=corner_exit_adjustment,
                    front_tire_type=front_tires,
                    rear_tire_type=rear_tires
                )
                
                # Calculate roll bar stiffness
                front_roll_bar, rear_roll_bar = calculate_roll_bar_stiffness(
                    rotational_g_values=rotational_g_values,
                    low_speed_stability=low_speed_stability,
                    high_speed_stability=high_speed_stability,
                    arb_stiffness_multiplier=arb_stiffness_multiplier,
                    ou_adjustment=ou_adjustment
                )
                
                # Calculate alignment settings
                alignment_settings = calculate_alignment_settings(
                    rotational_g_75mph=form.cleaned_data['rotational_g_75mph'],
                    drivetrain=vehicle.drivetrain,
                    tire_wear_multiplier=tire_wear_multiplier,
                    track_type=track_type,
                    front_weight_distribution=front_weight_distribution,
                    low_speed_stability=low_speed_stability,
                    high_speed_stability=high_speed_stability,
                    front_tire_type=front_tires,
                    rear_tire_type=rear_tires
                )
                
                # Store results in the calculation model
                calculation.front_spring_rate = front_spring_rate
                calculation.rear_spring_rate = rear_spring_rate
                calculation.front_spring_frequency = front_spring_frequency
                calculation.rear_spring_frequency = rear_spring_frequency
                calculation.front_roll_bar = front_roll_bar
                calculation.rear_roll_bar = rear_roll_bar
                calculation.front_camber = alignment_settings['front_camber']
                calculation.rear_camber = alignment_settings['rear_camber']
                calculation.front_toe = alignment_settings['front_toe']
                calculation.rear_toe = alignment_settings['rear_toe']
                
                # Save the calculation
                calculation.save()
                
                # Store ID in session for persistence
                request.session['spring_calculation_id'] = calculation.id
                
                # Save form data to session for persistence
                form_data = {}
                for field_name, field_value in form.cleaned_data.items():
                    # Convert non-serializable types to string or appropriate format
                    if isinstance(field_value, (int, float, str, bool)) or field_value is None:
                        form_data[field_name] = field_value
                    elif hasattr(field_value, 'id'):
                        # For model instances, store the ID
                        form_data[field_name] = field_value.id
                    else:
                        # For other types, try string conversion
                        try:
                            form_data[field_name] = str(field_value)
                        except:
                            pass
                
                # Store in session
                request.session['suspension_form_data'] = form_data
                
                # Show success message
                messages.success(request, "Calculation Successful!")
                
                return render(request, 'spring_calc/calculate.html', {
                    'form': form,
                    'calculation': calculation,
                    'front_spring_raw': round(front_spring_rate, 2),
                    'rear_spring_raw': round(rear_spring_rate, 2),
                    'front_compression': damper_settings['front_compression'],
                    'front_extension': damper_settings['front_extension'],
                    'rear_compression': damper_settings['rear_compression'],
                    'rear_extension': damper_settings['rear_extension'],
                    'front_roll_bar': front_roll_bar,
                    'rear_roll_bar': rear_roll_bar,
                    'front_camber': alignment_settings['front_camber'],
                    'rear_camber': alignment_settings['rear_camber'],
                    'front_toe': alignment_settings['front_toe'],
                    'rear_toe': alignment_settings['rear_toe']
                })
                
            except Exception as e:
                # Handle calculation errors
                logger.error(f"Error calculating spring rates: {str(e)}")
                messages.error(request, f"Error calculating spring rates: {str(e)}")
                return render(request, 'spring_calc/calculate.html', {'form': form})
        else:
            # Form is invalid - preserve all alignment settings and other fields
            preserved_form = SpringCalculatorForm(request.POST)
            # Add error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
            
            return render(request, 'spring_calc/calculate.html', {'form': preserved_form})
    
    # Default case - load from session if available
    if 'suspension_form_data' in request.session and not previous_calculation:
        form_data = request.session['suspension_form_data']
    
        # If there's a vehicle_id, try to get the Vehicle instance
        if 'vehicle' in form_data and isinstance(form_data['vehicle'], int):
            try:
                form_data['vehicle'] = Vehicle.objects.get(id=form_data['vehicle'])
            except Vehicle.DoesNotExist:
                pass
    
        form = SpringCalculatorForm(initial=form_data)
    elif previous_calculation:
        # When using a previous calculation, use it to initialize the form
        form = SpringCalculatorForm(instance=previous_calculation)
    else:
        form = SpringCalculatorForm()
    
    return render(request, 'spring_calc/calculate.html', {'form': form})

@handle_view_exceptions
@require_http_methods(["POST"])
def calculate_tire_diameter(request):
    """
    API endpoint to calculate tire diameter
    """
    try:
        form = TireSizeCalculatorForm(request.POST)
        
        if form.is_valid():
            # Get the form data
            speed = form.cleaned_data['speed']
            rpm = form.cleaned_data['rpm']
            gear_ratio = form.cleaned_data['gear_ratio']
            final_drive = form.cleaned_data['final_drive']
            
            # Calculate tire diameter
            tire_diameter = calculate_tire_diameter(gear_ratio, rpm, speed, final_drive)
            
            # Save calculation to database
            calculation = TireSizeCalculation(
                speed=speed,
                rpm=rpm,
                gear_ratio=gear_ratio,
                final_drive=final_drive,
                tire_size=tire_diameter
            )
            calculation.save()
            
            # Return JSON response
            return JsonResponse({
                'success': True,
                'tire_diameter': tire_diameter,
                'message': f"Calculated tire diameter: {tire_diameter} inches"
            })
        else:
            # Form is invalid
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            
            return JsonResponse({
                'success': False,
                'errors': errors,
                'message': "Invalid form data"
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error calculating tire diameter: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': "An error occurred during calculation"
        }, status=500)