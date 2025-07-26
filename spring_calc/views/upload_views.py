# spring_calc/views/upload_views.py
import logging
import json
import os
import urllib.parse
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings

from ..models import Vehicle
from ..decorators import handle_view_exceptions, log_view_access

from services.calculation_service import calculate_tire_diameter
from services.ocr_service import (
    process_uploaded_screenshot,
    extract_power_data_from_screenshot,
    process_transmission_screenshot,
    OCRError
)
from services.image_processing import process_screenshot, ImageProcessingError

logger = logging.getLogger(__name__)

@handle_view_exceptions
@log_view_access
def home(request):
    """
    Home page with options to calculate or upload screenshot
    """
    return render(request, 'spring_calc/home.html')

@handle_view_exceptions
@log_view_access
def upload_screenshot(request):
    """
    View for uploading and processing screenshots
    """
    vehicles = Vehicle.objects.all().order_by('name')
    
    if request.method == 'POST':
        # Clear previous session data first
        clear_session_calculation_data(request)
        
        # Track uploaded screenshot types
        uploaded_screenshots = {
            'suspension': 'suspension_screenshot' in request.FILES,
            'power': 'power_screenshot' in request.FILES,
            'transmission': 'transmission_screenshot' in request.FILES
        }
        
        # Validate vehicle selection
        vehicle_id = request.POST.get('vehicle')
        if not vehicle_id:
            messages.error(request, "Please select a vehicle.")
            return render(request, 'spring_calc/upload_screenshot.html', {'vehicles': vehicles})
        
        # Initialize combined data dict with vehicle ID
        combined_data = {'vehicle': vehicle_id}
        
        try:
            # Process suspension screenshot if uploaded
            if uploaded_screenshots['suspension']:
                try:
                    suspension_screenshot = request.FILES['suspension_screenshot']
                    
                    # Create debug directory if in debug mode
                    debug_dir = None
                    if hasattr(settings, 'DEBUG_OCR') and settings.DEBUG_OCR:
                        debug_dir = os.path.join(settings.MEDIA_ROOT, 'debug_ocr', datetime.now().strftime('%Y%m%d_%H%M%S'))
                        os.makedirs(debug_dir, exist_ok=True)
                    
                    # Process the screenshot
                    processed_image_path = process_screenshot(
                        suspension_screenshot, 
                        output_dir=debug_dir,
                        debug_mode=(hasattr(settings, 'DEBUG_OCR') and settings.DEBUG_OCR)
                    )
                    
                    # Extract data using OCR
                    suspension_data = process_uploaded_screenshot(
                        processed_image_path,
                        debug_mode=(hasattr(settings, 'DEBUG_OCR') and settings.DEBUG_OCR)
                    )
                    
                    # Update combined data with suspension details
                    suspension_keys = [
                        'vehicle_weight', 'front_weight_distribution', 
                        'front_ride_height', 'rear_ride_height',
                        'front_downforce', 'rear_downforce',
                        'low_speed_stability', 'high_speed_stability',
                        'rotational_g_40mph', 'rotational_g_75mph', 'rotational_g_150mph',
                        'performance_points', 'front_tires', 'rear_tires'
                    ]
                    for key in suspension_keys:
                        if key in suspension_data:
                            combined_data[key] = suspension_data[key]
                    
                    messages.success(request, "Suspension screenshot processed successfully!")
                except (OCRError, ImageProcessingError) as e:
                    messages.warning(request, f"Problem processing suspension screenshot: {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing suspension screenshot: {str(e)}", exc_info=True)
                    messages.error(request, f"Error processing suspension screenshot: {str(e)}")
            
            # Process power screenshot if uploaded
            if uploaded_screenshots['power']:
                try:
                    power_screenshot = request.FILES['power_screenshot']
                    
                    # Create debug directory if in debug mode
                    debug_dir = None
                    if hasattr(settings, 'DEBUG_OCR') and settings.DEBUG_OCR:
                        debug_dir = os.path.join(settings.MEDIA_ROOT, 'debug_ocr', datetime.now().strftime('%Y%m%d_%H%M%S'))
                        os.makedirs(debug_dir, exist_ok=True)
                    
                    # Process the screenshot
                    processed_image_path = process_screenshot(
                        power_screenshot, 
                        output_dir=debug_dir,
                        debug_mode=(hasattr(settings, 'DEBUG_OCR') and settings.DEBUG_OCR)
                    )
                    
                    # Extract data using OCR
                    power_data = extract_power_data_from_screenshot(
                        processed_image_path,
                        debug_mode=(hasattr(settings, 'DEBUG_OCR') and settings.DEBUG_OCR)
                    )
                    # Force update the combined data with ALL extracted fields
                    # Don't skip any fields - even if they're None
                    for key, value in power_data.items():
                        combined_data[key] = value
                    
                    messages.success(request, "Power screenshot processed successfully!")
                except (OCRError, ImageProcessingError) as e:
                    messages.warning(request, f"Problem processing power screenshot: {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing power screenshot: {str(e)}", exc_info=True)
                    messages.error(request, f"Error processing power screenshot: {str(e)}")
            
            # Process transmission screenshot if uploaded
            if uploaded_screenshots['transmission']:
                try:
                    transmission_screenshot = request.FILES['transmission_screenshot']
        
                    # Create debug directory if in debug mode
                    debug_dir = None
                    if hasattr(settings, 'DEBUG_OCR') and settings.DEBUG_OCR:
                        debug_dir = os.path.join(settings.MEDIA_ROOT, 'debug_ocr', datetime.now().strftime('%Y%m%d_%H%M%S'))
                        os.makedirs(debug_dir, exist_ok=True)
        
                    # Process the screenshot with inverted colors for better OCR
                    processed_image_path = process_screenshot(
                        transmission_screenshot, 
                        output_dir=debug_dir,
                        debug_mode=(hasattr(settings, 'DEBUG_OCR') and settings.DEBUG_OCR),
                        invert_colors=True  # Add this parameter
                    )
        
                    # Extract data using OCR
                    transmission_data = process_transmission_screenshot(
                        processed_image_path,
                        debug_mode=(hasattr(settings, 'DEBUG_OCR') and settings.DEBUG_OCR)
                    )
        
                    # Update combined data with transmission details
                    transmission_keys = [
                        'gear_ratio', 'rpm', 'speed', 'final_drive', 
                        'num_gears', 'tire_diameter_inches'
                    ]
                    for key in transmission_keys:
                        if key in transmission_data:
                            combined_data[key] = transmission_data[key]
        
                    # Calculate tire diameter if we have all the required data
                    gear_ratio = transmission_data.get('gear_ratio')
                    rpm = transmission_data.get('rpm')
                    speed = transmission_data.get('speed')
                    final_drive = transmission_data.get('final_drive')
        
                    if gear_ratio and rpm and speed and final_drive:
                        tire_diameter = calculate_tire_diameter(gear_ratio, rpm, speed, final_drive)
                        combined_data['tire_diameter_inches'] = tire_diameter
                        logger.info(f"Calculated tire diameter: {tire_diameter} inches")
        
                    messages.success(request, "Transmission screenshot processed successfully!")
                except (OCRError, ImageProcessingError) as e:
                    messages.warning(request, f"Problem processing transmission screenshot: {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing transmission screenshot: {str(e)}", exc_info=True)
                    messages.error(request, f"Error processing transmission screenshot: {str(e)}")
            
            # Add debug info if enabled
            if hasattr(settings, 'DEBUG_OCR') and settings.DEBUG_OCR:
                # Log the full OCR data in the debug directory
                debug_dir = os.path.join(settings.MEDIA_ROOT, 'debug_ocr')
                os.makedirs(debug_dir, exist_ok=True)
                
                with open(os.path.join(debug_dir, 'ocr_data_session.json'), 'w') as f:
                    json.dump(combined_data, f, indent=2)
                
                # Add debug info to session for display
                request.session['debug_info'] = {
                    'ocr_data': combined_data,
                    'timestamp': str(datetime.now())
                }
            
            # Store in session with minimal processing
            request.session['ocr_data'] = combined_data

            logger.debug(f"Storing in session: {combined_data}")
            
            # Prepare URL parameters for redirecting
            url_params = urllib.parse.urlencode({
                k: v for k, v in combined_data.items() 
                if isinstance(v, (int, float, str))
            })
            
            # Routing logic based on uploaded screenshots
            if uploaded_screenshots['suspension'] and (uploaded_screenshots['power'] or uploaded_screenshots['transmission']):
                # Both suspension and power/transmission - go to suspension calculator first
                return redirect(f"{reverse('calculate_springs')}?{url_params}")
            elif uploaded_screenshots['suspension']:
                # Only suspension - go to suspension calculator
                return redirect(f"{reverse('calculate_springs')}?{url_params}")
            elif uploaded_screenshots['power'] or uploaded_screenshots['transmission']:
                # Only power or transmission - go to gear calculator
                return redirect(f"{reverse('calculate_gears')}?{url_params}")
            
            # No valid screenshots uploaded
            messages.warning(request, "No valid calculations could be performed from the uploaded screenshots.")
            
        except Exception as e:
            logger.error(f"Critical error processing screenshots: {str(e)}", exc_info=True)
            messages.error(request, f"Critical error processing screenshots: {str(e)}")
        
        # Save the session changes
        request.session.modified = True
    
    return render(request, 'spring_calc/upload_screenshot.html', {'vehicles': vehicles})

# Helper function
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

def reverse(url_name):
    """
    Simple helper function to mimic Django's reverse function
    Used in this file to avoid circular imports
    """
    # Since we're not using dynamic URLs in this project, a simple mapping will do
    url_map = {
        'home': '/',
        'calculate_springs': '/spring-calculator/',
        'calculate_gears': '/gear-calculator/',
        'complete_setup': '/complete-setup/',
        'upload_screenshot': '/upload-screenshot/',
        'saved_setups': '/saved-setups/',
    }
    
    return url_map.get(url_name, '/')