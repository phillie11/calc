# spring_calc/views/setup_views.py
import logging
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from ..models import SavedSetup, SpringCalculation, GearCalculation, Vehicle
from ..forms import SavedSetupForm
from ..decorators import handle_view_exceptions, require_vehicle_selection, log_view_access

from services.calculation_service import calculate_damper_settings

logger = logging.getLogger(__name__)

def dashboard(request):
    """
    View to render the React dashboard
    """
    return render(request, 'dashboard.html')
@handle_view_exceptions
@require_http_methods(["POST"])
def reset_calculations(request):
    """
    Reset only the calculation data in the session (not all session data)
    """
    try:
        # Keys related to calculations
        calculation_keys = [
            'spring_calculation_id', 
            'gear_calculation_id',
            'suspension_form_data',
            'complete_setup'
        ]
        
        # Remove calculation keys from session
        for key in calculation_keys:
            if key in request.session:
                del request.session[key]
        
        # Save the session
        request.session.save()
        
        # Get redirect URL from request or default to home
        redirect_url = request.POST.get('redirect_url', '/')
        
        # Add a success message
        messages.success(request, "Calculation data has been reset.")
        
        # Redirect to the specified URL
        return redirect(redirect_url)
        
    except Exception as e:
        logger.error(f"Error resetting calculations: {str(e)}", exc_info=True)
        messages.error(request, f"Error resetting calculations: {str(e)}")
        return redirect(request.META.get('HTTP_REFERER', '/'))

@handle_view_exceptions
@log_view_access
def complete_setup(request):
    """
    View to display a combined view of suspension and gear calculator results
    """
    spring_calculation = None
    gear_calculation = None
    damper_settings = None
    torque_curve_data = None
    engine_data = None
    gear_speeds = None
    
    # Get vehicle information
    vehicle_id = None
    vehicle_name = "Unknown Vehicle"
    vehicle = None
    
    if 'ocr_data' in request.session and 'vehicle' in request.session['ocr_data']:
        vehicle_id = request.session['ocr_data']['vehicle']
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
            vehicle_name = vehicle.name
        except Vehicle.DoesNotExist:
            pass
    
    # Retrieve spring calculation if available
    if 'spring_calculation_id' in request.session:
        try:
            spring_calculation = SpringCalculation.objects.get(id=request.session['spring_calculation_id'])
            
            # Initialize vehicle from spring calculation if not already set
            if not vehicle and spring_calculation.vehicle:
                vehicle = spring_calculation.vehicle
                vehicle_name = vehicle.name
            
            # Calculate damper values (these were not stored in the model)
            if spring_calculation:
                # Use vehicle_weight from spring_calculation
                vehicle_weight = spring_calculation.vehicle_weight
                front_weight_distribution = spring_calculation.front_weight_distribution
                
                # Calculate damper settings
                damper_settings = calculate_damper_settings(
                    spring_rates=(spring_calculation.front_spring_rate, spring_calculation.rear_spring_rate),
                    vehicle_weight=vehicle_weight,
                    front_weight_distribution=front_weight_distribution,
                    corner_entry_adjustment=spring_calculation.corner_entry_adjustment,
                    corner_exit_adjustment=spring_calculation.corner_exit_adjustment,
                    front_tire_type=spring_calculation.front_tires,
                    rear_tire_type=spring_calculation.rear_tires
                )
        except SpringCalculation.DoesNotExist:
            pass
    
    # Retrieve gear calculation if available
    if 'gear_calculation_id' in request.session:
        try:
            gear_calculation = GearCalculation.objects.get(id=request.session['gear_calculation_id'])
            
            # Initialize vehicle from gear calculation if not already set
            if not vehicle and gear_calculation.vehicle:
                vehicle = gear_calculation.vehicle
                vehicle_name = vehicle.name
            
            # Prepare torque curve data for the graph
            if gear_calculation.torque_curve:
                torque_curve_data = gear_calculation.torque_curve
            
            # Calculate gear speeds
            if gear_calculation.gear_ratios and gear_calculation.final_drive:
                from services.gear_service import generate_gear_speeds
                gear_speeds = generate_gear_speeds(
                    gear_ratios=gear_calculation.gear_ratios,
                    final_drive=gear_calculation.final_drive,
                    max_power_rpm=gear_calculation.max_power_rpm,
                    tire_diameter_inches=gear_calculation.tire_diameter_inches
                )
                
                # Generate engine performance data for table
                engine_data = generate_engine_data(
                    min_rpm=gear_calculation.min_rpm,
                    max_rpm=gear_calculation.max_rpm,
                    max_power_rpm=gear_calculation.max_power_rpm,
                    torque_kgfm=gear_calculation.torque_kgfm,
                    power_hp=gear_calculation.power_hp
                )
        except GearCalculation.DoesNotExist:
            pass
    
    context = {
        'spring_calculation': spring_calculation,
        'gear_calculation': gear_calculation,
        'vehicle_name': vehicle_name,
        'vehicle': vehicle,
        'torque_curve_data': torque_curve_data,
        'engine_data': engine_data,
        'gear_speeds': gear_speeds,
        'debug': False,  # Set to True to show debug information
    }

    gear_graph_data = None
    if gear_calculation:
        gear_graph_data = {
            'gearRatios': gear_calculation.gear_ratios,
            'finalDrive': gear_calculation.final_drive,
            'maxRPM': gear_calculation.max_rpm,
            'minRPM': gear_calculation.min_rpm,
            'tireDiameter': gear_calculation.tire_diameter_inches
        }
        for key, value in gear_graph_data.items():
            if isinstance(value, dict):
                # Ensure gear_ratios is a regular dict, not a complex Django JSON field
                gear_graph_data[key] = dict(value)

    context = {
        'spring_calculation': spring_calculation,
        'gear_calculation': gear_calculation,
        'vehicle_name': vehicle_name,
        'vehicle': vehicle,
        'torque_curve_data': torque_curve_data,
        'engine_data': engine_data,
        'gear_speeds': gear_speeds,
        'gear_graph_data': json.dumps(gear_graph_data) if gear_graph_data else None,
        'debug': False,  # Set to True to show debug information
    }
    
    # Add damper settings to context if available
    if damper_settings:
        context.update({
            'front_compression': damper_settings['front_compression'],
            'rear_compression': damper_settings['rear_compression'],
            'front_extension': damper_settings['front_extension'],
            'rear_extension': damper_settings['rear_extension'],
        })
    
    return render(request, 'spring_calc/complete_setup.html', context)

@handle_view_exceptions
@require_http_methods(["POST"])
def save_setup(request):
    """
    View to save a complete setup to the database
    """
    try:
        # Check if the request has JSON content
        if request.content_type == 'application/json':
            # Parse JSON data from request
            data = json.loads(request.body)
        else:
            # Use POST data directly
            data = request.POST
        
        # Extract data
        name = data.get('name', 'Unnamed Setup')
        spring_calculation_id = data.get('spring_calculation_id')
        gear_calculation_id = data.get('gear_calculation_id')
        notes = data.get('notes', '')
        reset_after_save = data.get('reset_after_save') == 'true'
        
        # Create form instance with data
        form = SavedSetupForm(
            data={
                'name': name,
                'notes': notes
            },
            spring_calculation_id=spring_calculation_id,
            gear_calculation_id=gear_calculation_id
        )
        
        # Validate form
        if not form.is_valid():
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'errors': errors,
                    'message': "Invalid form data"
                }, status=400)
            else:
                messages.error(request, "Could not save setup: " + str(errors))
                return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # Save the setup
        setup = form.save()
        
        # Check if we should reset after saving
        if reset_after_save:
            # Clear all session data except auth-related
            keys_to_preserve = ['_auth_user_id', '_auth_user_backend', '_auth_user_hash']
            keys_to_clear = [key for key in request.session.keys() if key not in keys_to_preserve]
            
            for key in keys_to_clear:
                del request.session[key]
            
            # Save the session
            request.session.save()
            
            # Add success message
            messages.success(request, f"Setup '{setup.name}' saved successfully. Starting a new setup.")
            
            # Redirect to upload screenshot page
            return redirect('upload_screenshot')
        
        # If not resetting, return appropriate response
        if request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'setup_id': setup.id,
                'message': f"Setup '{setup.name}' saved successfully."
            })
        else:
            messages.success(request, f"Setup '{setup.name}' saved successfully.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
    except Exception as e:
        logger.error(f"Error saving setup: {str(e)}", exc_info=True)
        
        if request.content_type == 'application/json':
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': "An error occurred while saving the setup"
            }, status=500)
        else:
            messages.error(request, f"Error saving setup: {str(e)}")
            return redirect(request.META.get('HTTP_REFERER', '/'))

@handle_view_exceptions
@log_view_access
def saved_setups(request):
    """
    View to display and load saved setups
    """
    setups = SavedSetup.objects.all().order_by('-date_saved')
    
    if request.method == 'POST':
        # Handle loading a setup
        setup_id = request.POST.get('setup_id')
        if setup_id:
            try:
                setup = SavedSetup.objects.get(id=setup_id)
                
                # Clear all existing calculation data first
                clear_session_calculation_data(request)
                
                # Now store the new calculation IDs in session
                if setup.spring_calculation:
                    request.session['spring_calculation_id'] = setup.spring_calculation.id
                
                if setup.gear_calculation:
                    request.session['gear_calculation_id'] = setup.gear_calculation.id
                
                # Store vehicle information if available
                if setup.vehicle:
                    if 'ocr_data' not in request.session:
                        request.session['ocr_data'] = {}
                    request.session['ocr_data']['vehicle'] = setup.vehicle.id
                
                # Save the session to ensure changes are persisted
                request.session.save()
                
                # Set a message and redirect to complete setup
                messages.success(request, f"Setup '{setup.name}' loaded successfully!")
                return redirect('complete_setup')
                
            except SavedSetup.DoesNotExist:
                messages.error(request, "Setup not found.")
    
    return render(request, 'spring_calc/saved_setups.html', {'setups': setups})

@handle_view_exceptions
@log_view_access
@require_http_methods(["POST"])
def delete_setup(request):
    """
    View to delete a saved setup
    """
    setup_id = request.POST.get('setup_id')
    
    if not setup_id:
        messages.error(request, "No setup ID provided.")
        return redirect('saved_setups')
    
    try:
        setup = SavedSetup.objects.get(id=setup_id)
        setup_name = setup.name
        setup.delete()
        messages.success(request, f"Setup '{setup_name}' deleted successfully.")
    except SavedSetup.DoesNotExist:
        messages.error(request, "Setup not found.")
    
    return redirect('saved_setups')

@handle_view_exceptions
@require_http_methods(["POST"])
def save_setup(request):
    """
    AJAX endpoint to save a complete setup to the database
    """
    try:
        # Parse JSON data from request
        data = json.loads(request.body)
        
        # Extract data
        name = data.get('name', 'Unnamed Setup')
        spring_calculation_id = data.get('spring_calculation_id')
        gear_calculation_id = data.get('gear_calculation_id')
        notes = data.get('notes', '')
        
        # Create form instance with data
        form = SavedSetupForm(
            data={
                'name': name,
                'notes': notes
            },
            spring_calculation_id=spring_calculation_id,
            gear_calculation_id=gear_calculation_id
        )
        
        # Validate form
        if not form.is_valid():
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            
            return JsonResponse({
                'success': False,
                'errors': errors,
                'message': "Invalid form data"
            }, status=400)
        
        # Save the setup
        setup = form.save()
        
        return JsonResponse({
            'success': True,
            'setup_id': setup.id,
            'message': f"Setup '{setup.name}' saved successfully."
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': "Invalid JSON data",
            'message': "Could not parse request data"
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error saving setup: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': "An error occurred while saving the setup"
        }, status=500)

@handle_view_exceptions
@require_http_methods(["POST"])
def reset_all_data(request):
    """Endpoint to reset all application data in the session"""
    try:
        # Print debug info
        print(f"Reset request received: {request.method}")
        print(f"POST data: {request.POST}")
        
        # Clear all session data except auth-related
        keys_to_preserve = ['_auth_user_id', '_auth_user_backend', '_auth_user_hash']
        keys_to_clear = [key for key in request.session.keys() if key not in keys_to_preserve]
        
        print(f"Keys to clear: {keys_to_clear}")
        
        for key in keys_to_clear:
            del request.session[key]
        
        # Save the session to ensure changes are persisted
        request.session.save()
        
        # Get redirect URL from request or default to home
        redirect_url = request.POST.get('redirect_url', '/')
        
        print(f"Redirect URL: {redirect_url}")
        
        # Add a success message
        messages.success(request, "All application data has been reset successfully.")
        
        # Always redirect (no JSON response)
        return redirect(redirect_url)
        
    except Exception as e:
        # Log the error
        print(f"Error resetting data: {str(e)}")
        logger.error(f"Error resetting all data: {str(e)}", exc_info=True)
        
        # Add error message
        messages.error(request, f"Error resetting data: {str(e)}")
        
        # Redirect to home page or referrer
        return redirect(request.META.get('HTTP_REFERER', '/'))

def dashboard(request):
    return render(request, 'dashboard.html')

@handle_view_exceptions
@csrf_exempt  # For simplicity in the reset button
@require_http_methods(["POST"])
def reset_all_data(request):
    """
    Endpoint to reset all application data in the session
    """
    try:
        # Clear all session data except auth-related
        keys_to_preserve = ['_auth_user_id', '_auth_user_backend', '_auth_user_hash']
        keys_to_clear = [key for key in request.session.keys() if key not in keys_to_preserve]
        
        for key in keys_to_clear:
            del request.session[key]
        
        # Save the session to ensure changes are persisted
        request.session.save()
        
        # Get redirect URL from request or default to home
        redirect_url = request.POST.get('redirect_url', '/')
        
        # Return JSON response for AJAX or redirect for form
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({
                'success': True,
                'message': 'All application data reset successfully',
                'redirect': redirect_url
            })
        else:
            messages.success(request, "All application data has been reset successfully.")
            return redirect(redirect_url)
        
    except Exception as e:
        logger.error(f"Error resetting all data: {str(e)}", exc_info=True)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': "An error occurred while resetting application data"
            }, status=500)
        else:
            messages.error(request, f"Error resetting data: {str(e)}")
            return redirect(request.META.get('HTTP_REFERER', '/'))

# Helper functions

def clear_session_calculation_data(request):
    """
    Helper function to clear all calculation-related session data
    """
    keys_to_clear = [
        'spring_calculation_id', 
        'gear_calculation_id',
        'suspension_form_data',
        'ocr_data',
        'complete_setup'
    ]
    
    # Remove each key if it exists
    for key in keys_to_clear:
        if key in request.session:
            del request.session[key]
    
    # Save the session to ensure changes are persisted
    request.session.save()
    
    return True

def generate_engine_data(min_rpm, max_rpm, max_power_rpm, torque_kgfm, power_hp, num_points=10):
    """
    Generate engine performance data for display in the table
    
    Returns:
        list of dicts with RPM, Torque, and Power values
    """
    from services.gear_service import generate_torque_curve
    
    # Generate torque curve data
    torque_curve = generate_torque_curve(
        min_rpm=min_rpm,
        max_rpm=max_rpm,
        max_power_rpm=max_power_rpm,
        torque_kgfm=torque_kgfm,
        power_hp=power_hp,
        num_points=num_points
    )
    
    # Calculate power values
    engine_data = []
    
    for rpm, torque in torque_curve:
        # Calculate power (HP) at this RPM point
        # Power (HP) = Torque (kg·m) × RPM / 5252 × 7.124
        # 7.124 is the conversion factor from kg·m to lb·ft
        power = (torque * rpm / 5252) * 7.124
        
        # Convert torque from kg·m to ft·lb
        torque_ftlb = torque * 7.233
        
        engine_data.append({
            'RPM': int(rpm),
            'Torque_kgfm': float(torque),
            'Torque_ftlb': float(torque_ftlb),
            'Power_hp': float(power)
        })
    
    return engine_data