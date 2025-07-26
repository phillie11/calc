import pytesseract
import tempfile
import json
import math
import io
import re
import os
import urllib.parse
from PIL import Image
import numpy as np
import cv2
from io import BytesIO
from datetime import datetime
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .models import SavedSetup
from .ocr import process_uploaded_screenshot, extract_power_data_from_screenshot, process_transmission_screenshot
from cars.models import Vehicle
from .forms import SpringCalculatorForm, GearCalculatorForm
from .models import SavedSetup, SpringCalculation, TireSizeCalculation, GearCalculation, Vehicle
from .gear_calculator import calculate_optimal_gear_ratios, calculate_speed_at_rpm, estimate_acceleration, optimize_final_drive

from .alignment_calculator import (
    calculate_front_roll_bar_stiffness, calculate_rear_roll_bar_stiffness,
    calculate_front_camber, calculate_rear_camber, 
    calculate_front_toe, calculate_rear_toe
)
import math

def calculate_tire_diameter(gear_ratio, rpm, speed, final_drive):
    """
    Calculate tire diameter based on gear ratio, rpm, speed and final drive
    Returns tire diameter in inches
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
            print(f"Calculated tire diameter {diameter_inches} is outside reasonable range, using default")
            return 26.0
    except Exception as e:
        print(f"Error calculating tire diameter: {e}")
        return 26.0  # Default value

def extract_max_power_rpm_from_graph(screenshot_path, min_rpm, max_rpm):
    """
    Extract the RPM at max power by analyzing the position of the power curve peak
    
    Args:
        screenshot_path (str): Path to the screenshot image
        min_rpm (int): Minimum RPM value from x-axis
        max_rpm (int): Maximum RPM value from x-axis
        
    Returns:
        int: Estimated RPM at maximum power
    """

    try:
        # Define the region of the power graph
        with Image.open(screenshot_path) as img:
            width, height = img.size
            
        # Graph region in GT7 power screen (adjust based on your UI layout)
        graph_left = int(0.58 * width)
        graph_right = int(0.77 * width)
        graph_top = int(0.09 * height)
        graph_bottom = int(0.32 * height)
        
        # Open the image and crop to graph region
        with Image.open(screenshot_path) as img:
            graph_img = img.crop((graph_left, graph_top, graph_right, graph_bottom))
            
        # Save cropped graph for debugging
        debug_dir = os.path.join(os.path.dirname(screenshot_path), 'debug_power_regions')
        os.makedirs(debug_dir, exist_ok=True)
        graph_debug_path = os.path.join(debug_dir, "power_graph_region.jpg")
        graph_img.save(graph_debug_path)
        
        # Convert to numpy array for processing
        graph_array = np.array(graph_img)
        
        # Convert to grayscale if not already
        if len(graph_array.shape) > 2:
            gray_graph = cv2.cvtColor(graph_array, cv2.COLOR_RGB2GRAY)
        else:
            gray_graph = graph_array
            
        # Threshold to isolate the power curve line (assuming it's white or bright)
        _, thresh = cv2.threshold(gray_graph, 200, 255, cv2.THRESH_BINARY)
        
        # Save thresholded image for debugging
        cv2.imwrite(os.path.join(debug_dir, "power_graph_threshold.jpg"), thresh)
        
        # Locate white pixels (the curve)
        y_indices, x_indices = np.where(thresh > 0)
        
        if len(x_indices) == 0:
            print("No curve found, using default estimation")
            return int(min_rpm + (max_rpm - min_rpm) * 0.75)
            
        # Create a map of x positions to lowest y positions (highest point on graph)
        # In images, lower y values are higher on the graph (power peak)
        x_to_min_y = {}
        for x, y in zip(x_indices, y_indices):
            if x not in x_to_min_y or y < x_to_min_y[x]:
                x_to_min_y[x] = y
        
        # Find x position with lowest y (peak of power curve)
        if not x_to_min_y:
            return int(min_rpm + (max_rpm - min_rpm) * 0.75)
            
        peak_x = min(x_to_min_y.items(), key=lambda item: item[1])[0]
        
        # Calculate the relative position of the peak on the x-axis
        relative_position = (peak_x - 0) / (graph_img.width - 0)
        
        # Calculate RPM based on the position between min and max RPM
        rpm_at_max_power = int(min_rpm + relative_position * (max_rpm - min_rpm))
        
        # Round to nearest 100
        rpm_at_max_power = int(round(rpm_at_max_power / 100) * 100)
        
        print(f"Calculated RPM at max power: {rpm_at_max_power} (peak at {relative_position:.2f} of x-axis)")
        
        return rpm_at_max_power
        
    except Exception as e:
        print(f"Error extracting max power RPM from graph: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback to default estimation
        return int(min_rpm + (max_rpm - min_rpm) * 0.75)

def clear_session_calculation_data(request):
    """Helper function to clear all calculation-related session data"""
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

def reset_calculations(request):
    """View to reset all calculation data in the session"""
    if request.method == 'POST':
        try:
            # Use the helper function to clear all calculation data
            clear_session_calculation_data(request)
            
            return JsonResponse({
                'success': True,
                'message': 'All calculations reset successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

# Update saved_setups function to use this helper:

def saved_setups(request):
    """View to display and load saved setups with improved data clearing"""
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

def reset_calculations(request):
    """View to reset all calculation data in the session"""
    if request.method == 'POST':
        try:
            # Clear calculation IDs from session
            if 'spring_calculation_id' in request.session:
                del request.session['spring_calculation_id']
            
            if 'gear_calculation_id' in request.session:
                del request.session['gear_calculation_id']
            
            # Clear other related session data
            if 'suspension_form_data' in request.session:
                del request.session['suspension_form_data']
            
            if 'ocr_data' in request.session:
                del request.session['ocr_data']
            
            # Clear any other setup-related session data
            if 'complete_setup' in request.session:
                del request.session['complete_setup']
            
            # Save the session to ensure changes are persisted
            request.session.save()
            
            return JsonResponse({
                'success': True,
                'message': 'All calculations reset successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })
def save_setup(request):
    """View to save a complete setup to the database"""
    if request.method == 'POST':
        try:
            # Parse JSON data from request
            data = json.loads(request.body)
            
            # Extract data
            name = data.get('name', 'Unnamed Setup')
            spring_calculation_id = data.get('spring_calculation_id')
            gear_calculation_id = data.get('gear_calculation_id')
            
            # Validate required data
            if not (spring_calculation_id or gear_calculation_id):
                return JsonResponse({
                    'success': False,
                    'error': 'At least one calculation must be provided'
                })
            
            # Get calculation objects
            spring_calculation = None
            gear_calculation = None
            vehicle = None
            
            if spring_calculation_id and spring_calculation_id.strip():
                try:
                    spring_calculation = SpringCalculation.objects.get(id=spring_calculation_id)
                    vehicle = spring_calculation.vehicle
                except SpringCalculation.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Spring calculation not found'
                    })
            
            if gear_calculation_id and gear_calculation_id.strip():
                try:
                    gear_calculation = GearCalculation.objects.get(id=gear_calculation_id)
                    if not vehicle:
                        vehicle = gear_calculation.vehicle
                except GearCalculation.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Gear calculation not found'
                    })
            
            if not vehicle:
                return JsonResponse({
                    'success': False,
                    'error': 'No valid vehicle found'
                })
            
            # Create and save the setup
            saved_setup = SavedSetup(
                name=name,
                vehicle=vehicle,
                spring_calculation=spring_calculation,
                gear_calculation=gear_calculation
            )
            saved_setup.save()
            
            return JsonResponse({
                'success': True,
                'setup_id': saved_setup.id
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

def saved_setups(request):
    """View to display and load saved setups with improved data clearing"""
    setups = SavedSetup.objects.all().order_by('-date_saved')
    
    if request.method == 'POST':
        # Handle loading a setup
        setup_id = request.POST.get('setup_id')
        if setup_id:
            try:
                setup = SavedSetup.objects.get(id=setup_id)
                
                # Clear all existing calculation data first
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

def delete_setup(request):
    """View to delete a saved setup"""
    if request.method == 'POST':
        setup_id = request.POST.get('setup_id')
        if setup_id:
            try:
                setup = SavedSetup.objects.get(id=setup_id)
                setup_name = setup.name
                setup.delete()
                messages.success(request, f"Setup '{setup_name}' deleted successfully!")
            except SavedSetup.DoesNotExist:
                messages.error(request, "Setup not found.")
    
    return redirect('saved_setups')

def get_session_vehicle(request):
    """Helper function to get vehicle from session data"""
    vehicle_id = None
    vehicle_name = "Unknown Vehicle"
    
    if 'ocr_data' in request.session and 'vehicle' in request.session['ocr_data']:
        vehicle_id = request.session['ocr_data']['vehicle']
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
            vehicle_name = vehicle.name
            return vehicle_id, vehicle_name, vehicle
        except:
            pass
    
    return vehicle_id, vehicle_name, None

# Map tire types to multipliers (base reference is SM - Sport Medium = 1.0)
TIRE_MULTIPLIER_TABLE = {
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

# Main view functions
def home(request):
    """Home page with options to calculate or upload screenshot"""
    return render(request, 'spring_calc/home.html')
def process_power_screenshot(uploaded_file):
    """
    Robust processing of power screenshot with comprehensive data extraction
    
    Args:
        uploaded_file: Django UploadedFile object
        
    Returns:
        dict: Comprehensive extracted power and gear data
    """
    # Create a temporary file to save the uploaded image
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp:
        for chunk in uploaded_file.chunks():
            temp.write(chunk)
        temp_path = temp.name
    
    try:
        # Extract inputs using OCR
        from .ocr import extract_power_data_from_screenshot
        power_data = extract_power_data_from_screenshot(temp_path)
        
        # Print the exact values we're getting from OCR
        print("Raw power data extracted from OCR:", power_data)
        
        # Explicitly update power_hp from OCR if available
        if 'power_hp' in power_data and power_data['power_hp'] is not None:
            power_hp = power_data['power_hp']
            print(f"Using extracted power: {power_hp}")
        else:
            # If not found in OCR, use a value that indicates it wasn't found
            # We'll use None, which will cause the form to show an error
            power_data['power_hp'] = None
            print("Power not found in OCR")
        
        # Do the same for other values
        if 'torque_kgfm' in power_data and power_data['torque_kgfm'] is not None:
            torque_kgfm = power_data['torque_kgfm']
            print(f"Using extracted torque: {torque_kgfm}")
        else:
            power_data['torque_kgfm'] = None
            print("Torque not found in OCR")
        
        # RPM values
        if 'min_rpm' in power_data and power_data['min_rpm'] is not None:
            min_rpm = power_data['min_rpm']
            print(f"Using extracted min_rpm: {min_rpm}")
        else:
            power_data['min_rpm'] = None
            print("Min RPM not found in OCR")
        
        if 'max_rpm' in power_data and power_data['max_rpm'] is not None:
            max_rpm = power_data['max_rpm']
            print(f"Using extracted max_rpm: {max_rpm}")
        else:
            power_data['max_rpm'] = None
            print("Max RPM not found in OCR")
        
        if 'max_power_rpm' in power_data and power_data['max_power_rpm'] is not None:
            max_power_rpm = power_data['max_power_rpm']
            print(f"Using extracted max_power_rpm: {max_power_rpm}")
        else:
            power_data['max_power_rpm'] = None
            print("Max power RPM not found in OCR")
            
        # Attempt to extract max power RPM from graph if not directly extracted
        if not power_data.get('max_power_rpm') and 'min_rpm' in power_data and 'max_rpm' in power_data:
            try:
                from .ocr import extract_max_power_rpm_from_graph
                max_power_rpm = extract_max_power_rpm_from_graph(
                    temp_path, 
                    power_data['min_rpm'], 
                    power_data['max_rpm']
                )
                power_data['max_power_rpm'] = max_power_rpm
            except Exception as e:
                print(f"Could not calculate max_power_rpm from graph: {str(e)}")
                # Fallback estimation at 75% of RPM range
                power_data['max_power_rpm'] = int(
                    power_data['min_rpm'] + 
                    (power_data['max_rpm'] - power_data['min_rpm']) * 0.75
                )
        
        # For debugging, don't delete the temp file yet
        # os.unlink(temp_path)
        
        return power_data
    except Exception as e:
        # For debugging, don't delete the temp file on error
        # os.unlink(temp_path)
        print(f"Critical error processing power screenshot: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e
        

def upload_screenshot(request):
    """
    Simplified screenshot upload with direct, clear data transfer
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
                    suspension_data = process_uploaded_screenshot(suspension_screenshot)
                    
                    # Update combined data with suspension details
                    suspension_keys = [
                        'vehicle_weight', 'front_weight_distribution', 
                        'front_ride_height', 'rear_ride_height',
                        'front_downforce', 'rear_downforce',
                        'low_speed_stability', 'high_speed_stability',
                        'rotational_g_40mph', 'rotational_g_75mph', 'rotational_g_150mph'
                    ]
                    for key in suspension_keys:
                        if suspension_data.get(key):
                            combined_data[key] = suspension_data[key]
                    
                    messages.success(request, "Suspension screenshot processed successfully!")
                except Exception as suspension_error:
                    messages.warning(request, f"Could not process suspension screenshot: {str(suspension_error)}")
            
            # Process power screenshot if uploaded
            if uploaded_screenshots['power']:
                try:
                    power_screenshot = request.FILES['power_screenshot']
                    power_data = process_power_screenshot(power_screenshot)
                    
                    # Force update the combined data with ALL extracted fields
                    # Don't skip any fields - even if they're None
                    for key, value in power_data.items():
                        combined_data[key] = value
                    
                    messages.success(request, "Power screenshot processed successfully!")
                except Exception as power_error:
                    messages.warning(request, f"Could not process power screenshot: {str(power_error)}")
            
            # Process transmission screenshot if uploaded
            if uploaded_screenshots['transmission']:
                try:
                    transmission_screenshot = request.FILES['transmission_screenshot']
                    transmission_data = process_transmission_screenshot(transmission_screenshot)
                    
                    # Update combined data with transmission details
                    transmission_keys = [
                        'gear_ratio', 'rpm', 'speed', 'final_drive', 
                        'num_gears', 'tire_diameter_inches'
                    ]
                    for key in transmission_keys:
                        if transmission_data.get(key):
                            combined_data[key] = transmission_data[key]
                    
                    messages.success(request, "Transmission screenshot processed successfully!")
                except Exception as transmission_error:
                    messages.warning(request, f"Could not process transmission screenshot: {str(transmission_error)}")
            
            # Add debug info if enabled
            if hasattr(settings, 'DEBUG_OCR') and settings.DEBUG_OCR:
                # Log the full OCR data in the debug directory
                import json
                import os
                debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debug')
                os.makedirs(debug_dir, exist_ok=True)
                
                with open(os.path.join(debug_dir, 'ocr_data_session.json'), 'w') as f:
                    json.dump(combined_data, f, indent=2)
                
                # Add debug info to session for display
                request.session['debug_info'] = {
                    'ocr_data': combined_data,
                    'timestamp': str(datetime.now())
                }
            
            # Directly store in session with minimal processing
            request.session['ocr_data'] = combined_data
            
            # Prepare URL parameters for redirecting
            url_params = urllib.parse.urlencode({
                k: v for k, v in combined_data.items() 
                if isinstance(v, (int, float, str))
            })
            
            # Routing logic
            if uploaded_screenshots['suspension'] and uploaded_screenshots['power']:
                return redirect(f"{reverse('calculate_springs')}?{url_params}")
            elif uploaded_screenshots['power'] or uploaded_screenshots['transmission']:
                return redirect(f"{reverse('calculate_gears')}?{url_params}")
            
            messages.warning(request, "No valid calculations could be performed.")
            return render(request, 'spring_calc/upload_screenshot.html', {'vehicles': vehicles})
            
        except Exception as overall_error:
            messages.error(request, f"Critical error processing screenshots: {str(overall_error)}")
            import traceback
            traceback.print_exc()
            
        request.session.modified = True
    
    return render(request, 'spring_calc/upload_screenshot.html', {'vehicles': vehicles})

def calculate_springs(request):
    # Check if we have a previous calculation in the session
    previous_calculation = None
    if 'spring_calculation_id' in request.session:
        try:
            previous_calculation = SpringCalculation.objects.get(id=request.session['spring_calculation_id'])
        except SpringCalculation.DoesNotExist:
            pass
            
    # Check if we have GET parameters (high priority)
    if request.method == 'GET' and request.GET:
        # Use these parameters to pre-populate the form
        # Convert QueryDict to regular dict for easier handling
        form_data = {}
        for key, value in request.GET.items():
            # Try to convert to appropriate types
            try:
                # Attempt int conversion first
                form_data[key] = int(value)
            except (ValueError, TypeError):
                try:
                    # Attempt float conversion
                    form_data[key] = float(value)
                except (ValueError, TypeError):
                    # Keep as string otherwise
                    form_data[key] = value
        
        # Create form with GET data
        form = SpringCalculatorForm(initial=form_data)
        
        # Explicitly set certain values to ensure they take priority
        if 'vehicle' in request.GET:
            try:
                vehicle_id = int(request.GET['vehicle'])
                form.fields['vehicle'].initial = vehicle_id
            except (ValueError, TypeError):
                pass
        
        if 'vehicle_weight' in request.GET:
            try:
                form.fields['vehicle_weight'].initial = int(request.GET['vehicle_weight'])
            except (ValueError, TypeError):
                pass
        
        if 'front_weight_distribution' in request.GET:
            try:
                form.fields['front_weight_distribution'].initial = int(request.GET['front_weight_distribution'])
            except (ValueError, TypeError):
                pass
        
        # Print for debugging
        print("Form initialized with GET parameters:")
        for key, value in form_data.items():
            print(f"  {key}: {value}")
        
        return render(request, 'spring_calc/calculate.html', {
            'form': form
        })
    
    if request.method == 'POST':
        form = SpringCalculatorForm(request.POST)
        if form.is_valid():
            # Get the form data but don't save yet
            calculation = form.save(commit=False)

            # Make sure stability and G values are explicitly saved
            calculation.low_speed_stability = form.cleaned_data['low_speed_stability']
            calculation.high_speed_stability = form.cleaned_data['high_speed_stability']
            calculation.rotational_g_40mph = form.cleaned_data['rotational_g_40mph']
            calculation.rotational_g_75mph = form.cleaned_data['rotational_g_75mph']
            calculation.rotational_g_150mph = form.cleaned_data['rotational_g_150mph']
            
            # Get the vehicle and its lever ratios
            vehicle = form.cleaned_data['vehicle']
            front_lever_ratio = vehicle.lever_ratio_front
            rear_lever_ratio = vehicle.lever_ratio_rear
            
            # Get data from form
            front_weight_distribution = form.cleaned_data['front_weight_distribution'] / 100.0  # Convert percentage to decimal
            performance_points = form.cleaned_data.get('performance_points')
            front_tires = form.cleaned_data.get('front_tires')
            rear_tires = form.cleaned_data.get('rear_tires')
            arb_stiffness_multiplier = form.cleaned_data.get('arb_stiffness_multiplier')
            total_car_weight = form.cleaned_data['vehicle_weight']
            front_ride_height = form.cleaned_data['front_ride_height']
            rear_ride_height = form.cleaned_data['rear_ride_height']
            front_downforce = form.cleaned_data['front_downforce']
            rear_downforce = form.cleaned_data['rear_downforce']
            track_type = form.cleaned_data['track_type']
            tire_wear_multiplier = form.cleaned_data['tire_wear_multiplier']
            low_speed_stability = form.cleaned_data['low_speed_stability']
            high_speed_stability = form.cleaned_data['high_speed_stability']
            rotational_g_40mph = form.cleaned_data['rotational_g_40mph']
            rotational_g_75mph = form.cleaned_data['rotational_g_75mph']
            rotational_g_150mph = form.cleaned_data['rotational_g_150mph']
            stiffness_multiplier = form.cleaned_data['stiffness_multiplier']
            spring_frequency_offset = form.cleaned_data['spring_frequency_offset']
            ou_adjustment = form.cleaned_data['ou_adjustment']
            car_type = vehicle.car_type
            drivetrain = vehicle.drivetrain
            
            # Get corner entry/exit adjustment if they exist in the form
            corner_entry_adjustment = form.cleaned_data.get('corner_entry_adjustment', 0)
            corner_exit_adjustment = form.cleaned_data.get('corner_exit_adjustment', 0)
            
            # Get the multipliers for the selected tires
            front_tire_spring_multiplier = TIRE_MULTIPLIER_TABLE.get(front_tires, 1.0)
            rear_tire_spring_multiplier = TIRE_MULTIPLIER_TABLE.get(rear_tires, 1.0)
            front_tire_damper_rollbar_camber_multiplier = DAMPER_ROLLBAR_CAMBER_MULTIPLIER_TABLE.get(front_tires, 1.0)
            rear_tire_damper_rollbar_camber_multiplier = DAMPER_ROLLBAR_CAMBER_MULTIPLIER_TABLE.get(rear_tires, 1.0)
            front_tire_toe_multiplier = TOE_MULTIPLIER_TABLE.get(front_tires, 1.0)
            rear_tire_toe_multiplier = TOE_MULTIPLIER_TABLE.get(rear_tires, 1.0)
            
            # Constants for calculations
            UNSPRUNG_WEIGHT_TABLE = {
                "4WD": 55, "FF": 55, "FR": 45, "MR": 45, "RR": 45
            }
            
            CAR_TYPE_MULTIPLIER_TABLE = {
                "ROAD": 1.3, "GR4": 1.333, "RACE": 1.333, "VGT": 1.666, "FAN": 2.0
            }
            
            SPRING_FREQUENCY_OFFSET_TABLE = {
                -5: 0.5, -4: 0.6, -3: 0.7, -2: 0.8, -1: 0.9,
                0: 1.0, 1: 1.1, 2: 1.2, 3: 1.3, 4: 1.4,
                5: 1.5, 6: 1.6
            }
            
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
            
            rotational_g_values = [rotational_g_40mph, rotational_g_75mph, rotational_g_150mph]

            # Set default values for these parameters that were previously user inputs
            roll_bar_multiplier = 1.0  # Default value
            base_camber = 0.0
            
            # Perform the spring calculations
            try:
                # Get unsprung weights
                unsprung_front_weight = UNSPRUNG_WEIGHT_TABLE.get(drivetrain, 45)
                unsprung_rear_weight = UNSPRUNG_WEIGHT_TABLE.get(drivetrain, 45)
                
                # Calculate mass distribution
                front_mass = total_car_weight * front_weight_distribution
                rear_mass = total_car_weight * (1 - front_weight_distribution)
                
                # Calculate loads taking into account downforce and unsprung weight
                front_load = (front_mass + (front_downforce / 2) - unsprung_front_weight) / front_lever_ratio
                rear_load = (rear_mass + (rear_downforce / 2) - unsprung_rear_weight) / rear_lever_ratio
                
                # Convert to Newtons
                front_load_n = front_load * 9.81
                rear_load_n = rear_load * 9.81
                
                # Convert ride height to meters
                front_ride_height_m = front_ride_height / 1000
                rear_ride_height_m = rear_ride_height / 1000
                
                # Calculate spring rates in N/m
                front_spring_rate_nm = front_load_n / front_ride_height_m
                rear_spring_rate_nm = rear_load_n / rear_ride_height_m
                
                # Apply stiffness multiplier and tire type multiplier
                adjusted_front_spring_rate = front_spring_rate_nm * stiffness_multiplier * front_tire_spring_multiplier
                adjusted_rear_spring_rate = rear_spring_rate_nm * stiffness_multiplier * rear_tire_spring_multiplier
                
                # Calculate spring frequencies
                front_spring_frequency = math.sqrt(adjusted_front_spring_rate / front_mass)
                rear_spring_frequency = math.sqrt(adjusted_rear_spring_rate / rear_mass)
                
                # Convert to Hz
                final_front_spring_frequency = (1 / (2 * math.pi)) * front_spring_frequency
                final_rear_spring_frequency = (1 / (2 * math.pi)) * rear_spring_frequency
                
                # Apply car type and frequency offset multipliers
                car_type_multiplier = CAR_TYPE_MULTIPLIER_TABLE.get(car_type, 1.333)
                frequency_offset_multiplier = SPRING_FREQUENCY_OFFSET_TABLE.get(spring_frequency_offset, 1.0)
                
                adjusted_final_front_spring_frequency = final_front_spring_frequency * car_type_multiplier * frequency_offset_multiplier
                adjusted_final_rear_spring_frequency = final_rear_spring_frequency * car_type_multiplier * frequency_offset_multiplier
                
                # Convert spring rates from N/m to N/mm for GT7
                front_spring_rate_nmm = adjusted_front_spring_rate / 1000
                rear_spring_rate_nmm = adjusted_rear_spring_rate / 1000
                
                # Round to GT7 increments (simplified)
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
                
                # Calculate damper settings
                front_critical_damping = 2 * math.sqrt(adjusted_front_spring_rate * front_mass)
                rear_critical_damping = 2 * math.sqrt(adjusted_rear_spring_rate * rear_mass)
                front_critical_damping_half = front_critical_damping * 0.5
                rear_critical_damping_half = rear_critical_damping * 0.5
                
                # Get the multipliers for entry and exit adjustments
                entry_multipliers = CORNER_ENTRY_ADJUSTMENT_TABLE.get(corner_entry_adjustment, CORNER_ENTRY_ADJUSTMENT_TABLE[0])
                exit_multipliers = CORNER_EXIT_ADJUSTMENT_TABLE.get(corner_exit_adjustment, CORNER_EXIT_ADJUSTMENT_TABLE[0])
                
                # For corner entry (primarily affects compression)
                front_compression_entry = int((20 + front_critical_damping_half / 1000) * 
                                          front_tire_damper_rollbar_camber_multiplier * 
                                          entry_multipliers["front_compression"])
                
                rear_compression_entry = int((20 + rear_critical_damping_half / 1000) * 
                                         rear_tire_damper_rollbar_camber_multiplier * 
                                         entry_multipliers["rear_compression"])
                
                # For corner exit (primarily affects rebound/extension)
                front_compression_exit = int((20 + front_critical_damping_half / 1000) * 
                                         front_tire_damper_rollbar_camber_multiplier * 
                                         exit_multipliers["front_compression"])
                
                rear_compression_exit = int((20 + rear_critical_damping_half / 1000) * 
                                        rear_tire_damper_rollbar_camber_multiplier * 
                                        exit_multipliers["rear_compression"])
                
                front_extension_entry = int((30 + front_critical_damping_half / 800) * 
                                        front_tire_damper_rollbar_camber_multiplier * 
                                        entry_multipliers["front_rebound"])
                
                rear_extension_entry = int((30 + rear_critical_damping_half / 800) * 
                                       rear_tire_damper_rollbar_camber_multiplier * 
                                       entry_multipliers["rear_rebound"])
                
                front_extension_exit = int((30 + front_critical_damping_half / 800) * 
                                       front_tire_damper_rollbar_camber_multiplier * 
                                       exit_multipliers["front_rebound"])
                
                rear_extension_exit = int((30 + rear_critical_damping_half / 800) * 
                                      rear_tire_damper_rollbar_camber_multiplier * 
                                      exit_multipliers["rear_rebound"])
                
                # Combine the entry and exit adjustments (giving slightly more weight to the most extreme value)
                front_compression = int((front_compression_entry + front_compression_exit) / 2)
                rear_compression = int((rear_compression_entry + rear_compression_exit) / 2)
                front_extension = int((front_extension_entry + front_extension_exit) / 2)
                rear_extension = int((rear_extension_entry + rear_extension_exit) / 2)
                
                # Ensure values stay within bounds
                front_compression = max(20, min(40, front_compression))
                rear_compression = max(20, min(40, rear_compression))
                front_extension = max(30, min(50, front_extension))
                rear_extension = max(30, min(50, rear_extension))
                
                # For roll bar calculations, set handling adjustments
                front_ou_multiplier, rear_ou_multiplier = OU_MULTIPLIER_TABLE.get(ou_adjustment, [1.0, 1.0])

                # Perform alignment calculations with updated parameters
                front_roll_bar = calculate_front_roll_bar_stiffness(
                    rotational_g_values, high_speed_stability, 
                    arb_stiffness_multiplier, front_ou_multiplier
                ) * front_tire_damper_rollbar_camber_multiplier

                rear_roll_bar = calculate_rear_roll_bar_stiffness(
                    rotational_g_values, low_speed_stability, high_speed_stability, 
                    arb_stiffness_multiplier, rear_ou_multiplier
                ) * rear_tire_damper_rollbar_camber_multiplier

                front_camber = calculate_front_camber(
                    form.cleaned_data['rotational_g_75mph'],
                    vehicle.drivetrain,
                    form.cleaned_data['tire_wear_multiplier'],
                    form.cleaned_data['track_type'],
                    form.cleaned_data['front_weight_distribution'] / 100.0  # Convert to decimal
                ) * front_tire_damper_rollbar_camber_multiplier

                rear_camber = calculate_rear_camber(
                    form.cleaned_data['rotational_g_75mph'],
                    vehicle.drivetrain,
                    form.cleaned_data['tire_wear_multiplier'],
                    form.cleaned_data['track_type'],
                    form.cleaned_data['front_weight_distribution'] / 100.0  # Convert to decimal
                ) * rear_tire_damper_rollbar_camber_multiplier

                front_toe = calculate_front_toe(
                    form.cleaned_data['low_speed_stability'],
                    form.cleaned_data['high_speed_stability'],
                    vehicle.drivetrain,
                    form.cleaned_data['tire_wear_multiplier'],
                    form.cleaned_data['track_type']
                ) * front_tire_toe_multiplier

                rear_toe = calculate_rear_toe(
                    form.cleaned_data['high_speed_stability'],
                    form.cleaned_data['low_speed_stability'],
                    vehicle.drivetrain,
                    form.cleaned_data['tire_wear_multiplier'],
                    form.cleaned_data['track_type']
                ) * rear_tire_toe_multiplier
                
                # Store results in the calculation model
                calculation.performance_points = performance_points
                calculation.front_tires = front_tires
                calculation.rear_tires = rear_tires
                calculation.arb_stiffness_multiplier = arb_stiffness_multiplier
                calculation.front_spring_rate = front_spring_rate_gt7
                calculation.rear_spring_rate = rear_spring_rate_gt7
                calculation.front_spring_frequency = round(adjusted_final_front_spring_frequency, 2)
                calculation.rear_spring_frequency = round(adjusted_final_rear_spring_frequency, 2)
               
                # Store alignment values in the calculation model
                calculation.front_roll_bar = round(front_roll_bar)
                calculation.rear_roll_bar = round(rear_roll_bar)
                calculation.front_camber = round(front_camber, 1)
                calculation.rear_camber = round(rear_camber, 1)
                calculation.front_toe = round(front_toe, 2)
                calculation.rear_toe = round(rear_toe, 2)
                
                # Make sure track_type and tire_wear_multiplier are saved
                calculation.track_type = track_type
                calculation.tire_wear_multiplier = tire_wear_multiplier
               
                # Store corner adjustments if they're part of the model
                if hasattr(calculation, 'corner_entry_adjustment'):
                    calculation.corner_entry_adjustment = corner_entry_adjustment
                if hasattr(calculation, 'corner_exit_adjustment'):
                    calculation.corner_exit_adjustment = corner_exit_adjustment
               
                # Check if we're doing a complete setup
                if request.session.get('complete_setup'):
                    # Clear the flag
                    del request.session['complete_setup']
                
                    # Store suspension results in session
                    suspension_result = {
                        'front_spring_rate': float(calculation.front_spring_rate) if calculation.front_spring_rate is not None else 0.0,
                        'rear_spring_rate': float(calculation.rear_spring_rate) if calculation.rear_spring_rate is not None else 0.0,
                        'front_compression': front_compression if 'front_compression' in locals() else 0.0,
                        'front_extension': front_extension if 'front_extension' in locals() else 0.0,
                        'rear_compression': rear_compression if 'rear_compression' in locals() else 0.0,
                        'rear_extension': rear_extension if 'rear_extension' in locals() else 0.0,
                        'front_roll_bar': int(calculation.front_roll_bar) if calculation.front_roll_bar is not None else 0,
                        'rear_roll_bar': int(calculation.rear_roll_bar) if calculation.rear_roll_bar is not None else 0,
                        'front_camber': float(calculation.front_camber) if calculation.front_camber is not None else 0.0,
                        'rear_camber': float(calculation.rear_camber) if calculation.rear_camber is not None else 0.0,
                        'front_toe': float(calculation.front_toe) if calculation.front_toe is not None else 0.0,
                        'rear_toe': float(calculation.rear_toe) if calculation.rear_toe is not None else 0.0
                    }
                    
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
            
                # Explicitly ensure the stability and rotational G values are in the form_data
                form_data['low_speed_stability'] = calculation.low_speed_stability
                form_data['high_speed_stability'] = calculation.high_speed_stability
                form_data['rotational_g_40mph'] = calculation.rotational_g_40mph
                form_data['rotational_g_75mph'] = calculation.rotational_g_75mph
                form_data['rotational_g_150mph'] = calculation.rotational_g_150mph
            
                # Store in session
                request.session['suspension_form_data'] = form_data
            
                # Show success message
                messages.success(request, "Calculation Successful!")
            
                return render(request, 'spring_calc/calculate.html', {
                    'form': form,
                    'calculation': calculation,
                    'front_spring_raw': round(front_spring_rate_nmm, 2),
                    'rear_spring_raw': round(rear_spring_rate_nmm, 2),
                    'front_compression': front_compression,
                    'front_extension': front_extension,
                    'rear_compression': rear_compression,
                    'rear_extension': rear_extension,
                    'front_roll_bar': calculation.front_roll_bar,
                    'rear_roll_bar': calculation.rear_roll_bar,
                    'front_camber': calculation.front_camber,
                    'rear_camber': calculation.rear_camber,
                    'front_toe': calculation.front_toe,
                    'rear_toe': calculation.rear_toe
                })

            except Exception as e:
                # Handle any calculation errors
                messages.error(request, f"Error calculating spring rates: {str(e)}")
                import traceback
                traceback.print_exc()
                return render(request, 'spring_calc/calculate.html', {'form': form})
        else:
            # Form is invalid - preserve all alignment settings and other fields
            preserved_form = SpringCalculatorForm(request.POST)
            # Add error messages if needed
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
            
            return render(request, 'spring_calc/calculate.html', {'form': preserved_form})
    
    # Default case - load from session if available
    if 'suspension_form_data' in request.session and not previous_calculation:
        form_data = request.session['suspension_form_data']
    
        # Ensure stability and rotational G values are correctly transferred
        fields_to_check = ['low_speed_stability', 'high_speed_stability', 
                          'rotational_g_40mph', 'rotational_g_75mph', 'rotational_g_150mph']
    
        for field in fields_to_check:
            if field in form_data:
                # Convert to float if necessary
                try:
                    form_data[field] = float(form_data[field])
                except (ValueError, TypeError):
                    pass
    
        # If there's a vehicle_id, try to get the Vehicle instance
        if 'vehicle' in form_data and isinstance(form_data['vehicle'], int):
            try:
                form_data['vehicle'] = Vehicle.objects.get(id=form_data['vehicle'])
            except Vehicle.DoesNotExist:
                pass
    
        form = SpringCalculatorForm(initial=form_data)
    elif previous_calculation:
        # When using a previous calculation, explicitly set the stability and G values
        form = SpringCalculatorForm(instance=previous_calculation)
    
        # If needed, explicitly set these values in the form's initial data
        if hasattr(previous_calculation, 'low_speed_stability'):
            form.fields['low_speed_stability'].initial = previous_calculation.low_speed_stability
        if hasattr(previous_calculation, 'high_speed_stability'):
            form.fields['high_speed_stability'].initial = previous_calculation.high_speed_stability
        if hasattr(previous_calculation, 'rotational_g_40mph'):
            form.fields['rotational_g_40mph'].initial = previous_calculation.rotational_g_40mph
        if hasattr(previous_calculation, 'rotational_g_75mph'):
            form.fields['rotational_g_75mph'].initial = previous_calculation.rotational_g_75mph
        if hasattr(previous_calculation, 'rotational_g_150mph'):
            form.fields['rotational_g_150mph'].initial = previous_calculation.rotational_g_150mph
    else:
        form = SpringCalculatorForm()
    
    return render(request, 'spring_calc/calculate.html', {'form': form})   

def extract_transmission_data_from_screenshot(screenshot_path):
    """
    Extract transmission data from screenshot using Tesseract OCR
    
    Args:
        screenshot_path (str): Path to the screenshot image
        
    Returns:
        dict: Extracted transmission data values
    """
    # Open image and get dimensions
    with Image.open(screenshot_path) as img:
        width, height = img.size
    
    # Define regions
    regions = {
        'gear_ratio': (0.38, 0.43, 0.425, 0.46),
        'rpm': (0.49, 0.35, 0.53, 0.375),
        'speed': (0.435, 0.43, 0.46, 0.46),
        'final_drive': (0.42, 0.67, 0.46, 0.71),
        'gear_section': (0.30, 0.35, 0.34, 0.67)  # For detecting number of gears
    }  

    results = {}
    debug_info = {}
    
    # Create debug directory
    debug_dir = os.path.join(os.path.dirname(screenshot_path), 'debug_transmission_regions')
    os.makedirs(debug_dir, exist_ok=True)
    
    # Process each region
    for param_name, region_pct in regions.items():
        try:
            # Convert percentage to actual pixel coordinates
            left = int(region_pct[0] * width)
            top = int(region_pct[1] * height)
            right = int(region_pct[2] * width)
            bottom = int(region_pct[3] * height)
            
            # Create a cropped image
            with Image.open(screenshot_path) as img:
                cropped = img.crop((left, top, right, bottom))
                
                # Save cropped image for debugging
                debug_path = os.path.join(debug_dir, f"{param_name}_region.jpg")
                cropped.save(debug_path)
                
                # Use Tesseract OCR with numeric configuration for this type of data
                numeric_config = '--oem 3 --psm 6 -c tessedit_char_whitelist="0123456789.:- "'
                region_text = pytesseract.image_to_string(cropped, config=numeric_config).strip()
                
                debug_info[param_name] = region_text
                print(f"{param_name}: Found text: '{region_text}'")
                
                # Enhanced number extraction logic
                if param_name == 'gear_ratio':
                    # First, try to find ratio patterns like "3.550" or "3.55:1"
                    match = re.search(r'(\d+\.\d+)(?:\s*:\s*1)?', region_text)
                    if match:
                        results[param_name] = float(match.group(1))
                        print(f"Extracted {param_name}: {results[param_name]}")
                    else:
                        # Try to find any number with decimal point
                        match = re.search(r'(\d+\.\d+)', region_text)
                        if match:
                            results[param_name] = float(match.group(1))
                            print(f"Extracted {param_name} (fallback): {results[param_name]}")
                
                elif param_name == 'rpm':
                    # Look for patterns like "8500 rpm" or just "8500"
                    match = re.search(r'(\d[\d,]*)\s*(?:rpm|RPM)?', region_text)
                    if match:
                        rpm_value = match.group(1).replace(',', '')
                        results[param_name] = int(rpm_value)
                        print(f"Extracted {param_name}: {results[param_name]}")
                
                elif param_name == 'speed':
                    # Look for patterns like "120 km/h" or "120km/h" or just "120"
                    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:km/h|KM/H|mph|MPH)?', region_text)
                    if match:
                        results[param_name] = float(match.group(1))
                        print(f"Extracted {param_name}: {results[param_name]}")
                
                elif param_name == 'final_drive':
                    # Look for patterns like "4.375:1" or just "4.375"
                    match = re.search(r'(\d+\.\d+)(?:\s*:\s*1)?', region_text)
                    if match:
                        results[param_name] = float(match.group(1))
                        print(f"Extracted {param_name}: {results[param_name]}")
                
                # Add this logic to calculate number of gears from the gear section text
                elif param_name == 'gear_section':
                    # Try to detect all gear numbers in the text
                    gear_matches = re.findall(r'(\d+)[a-z]{2}', region_text.lower())
        
                    # Count unique gear numbers
                    if gear_matches:
                        unique_gears = set([int(g) for g in gear_matches if g.isdigit()])
                        num_gears = max(unique_gears) if unique_gears else 5
            
                        # Validate range (4-9)
                        if 4 <= num_gears <= 9:
                            results['num_gears'] = num_gears
                            print(f"Detected {num_gears} gears")
                        else:
                            # Default if out of range
                            results['num_gears'] = 6
                            print(f"Gear count {num_gears} out of range, defaulting to 6")
                    else:
                        # Alternative detection - count lines containing 'gear' or ordinals
                        lines = region_text.lower().split('\n')
                        gear_lines = [l for l in lines if 'gear' in l or '1st' in l or '2nd' in l or 
                                     '3rd' in l or '4th' in l or '5th' in l or '6th' in l or 
                                     '7th' in l or '8th' in l or '9th' in l]
            
                        if gear_lines:
                            num_gears = len(gear_lines)
                            # Validate range
                            if 4 <= num_gears <= 9:
                                results['num_gears'] = num_gears
                                print(f"Detected {num_gears} gear lines")
                            else:
                                results['num_gears'] = 6
                                print(f"Gear line count {num_gears} out of range, defaulting to 6")
                        else:
                            results['num_gears'] = 6
                            print("Could not detect gears, defaulting to 6")
            
        except Exception as e:
            print(f"Error processing {param_name}: {str(e)}")
            debug_info[param_name] = f"Error: {str(e)}"
    
    # Save all debug info to a file
    try:
        debug_file_path = os.path.join(os.path.dirname(screenshot_path), 'transmission_ocr_debug.txt')
        with open(debug_file_path, 'w', encoding='utf-8') as f:
            f.write("Transmission OCR Debug Information\n")
            f.write("=" * 50 + "\n\n")
                
            for key, value in debug_info.items():
                f.write(f"{key}:\n")
                f.write(f"{str(value)}\n")  # Convert to string to handle any type
                f.write("-" * 30 + "\n")
                
            f.write("\nExtracted Results:\n")
            for key, value in results.items():
                f.write(f"{key}: {value}\n")
            
        print(f"Transmission OCR debug information saved to {debug_file_path}")
        print(f"Region images saved to {debug_dir} directory")
    except Exception as e:
        print(f"Error saving debug info: {str(e)}")
        
    # Set defaults for missing values
    if 'num_gears' not in results:
        results['num_gears'] = 6
    if 'speed' not in results:
        results['speed'] = 100.0
    if 'rpm' not in results:
        results['rpm'] = 5000
    if 'gear_ratio' not in results:
        results['gear_ratio'] = 1.0
    if 'final_drive' not in results:
        results['final_drive'] = 3.7
        
    return results
           
def process_transmission_screenshot(uploaded_file):
    """
    Process an uploaded transmission screenshot file
    """
    # Create a temporary file to save the uploaded image
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp:
        for chunk in uploaded_file.chunks():
            temp.write(chunk)
        temp_path = temp.name
    
    print(f"Saved transmission screenshot to temporary file: {temp_path}")
    
    try:
        # Extract data using OCR
        print("Starting OCR extraction for transmission screenshot...")
        transmission_data = extract_transmission_data_from_screenshot(temp_path)
        print(f"OCR extraction completed. Results: {transmission_data}")
        
        # For debugging, don't delete the temp file yet
        # os.unlink(temp_path)
        
        return transmission_data
    except Exception as e:
        # For debugging, don't delete the temp file on error
        # os.unlink(temp_path)
        print(f"ERROR in process_transmission_screenshot: {e}")
        import traceback
        traceback.print_exc()
        raise e

def complete_setup(request):
    """
    Display a combined view of suspension and gear calculator results
    """
    spring_calculation = None
    gear_calculation = None
    
    # Get vehicle information
    vehicle_id, vehicle_name, vehicle = get_session_vehicle(request)

    context = {
        'spring_calculation': None,
        'gear_calculation': None,
        'vehicle_name': vehicle_name,
        'vehicle': vehicle,
    }
    
    # Retrieve spring calculation if available
    if 'spring_calculation_id' in request.session:
        try:
            spring_calculation = SpringCalculation.objects.get(id=request.session['spring_calculation_id'])
            
            # Calculate damper values (these were not stored in the model)
            # Use vehicle_weight from spring_calculation rather than vehicle.weight
            vehicle_weight = spring_calculation.vehicle_weight
            front_critical_damping = 2 * math.sqrt(spring_calculation.front_spring_rate * 1000 * (vehicle_weight * spring_calculation.front_weight_distribution / 100))
            rear_critical_damping = 2 * math.sqrt(spring_calculation.rear_spring_rate * 1000 * (vehicle_weight * (1 - spring_calculation.front_weight_distribution / 100)))
            
            front_critical_damping_half = front_critical_damping * 0.5
            rear_critical_damping_half = rear_critical_damping * 0.5
            
            # Get tire multipliers
            front_tire_damper_multiplier = DAMPER_ROLLBAR_CAMBER_MULTIPLIER_TABLE.get(spring_calculation.front_tires, 1.0)
            rear_tire_damper_multiplier = DAMPER_ROLLBAR_CAMBER_MULTIPLIER_TABLE.get(spring_calculation.rear_tires, 1.0)
            
            # Get corner adjustments if they exist
            corner_entry_adjustment = getattr(spring_calculation, 'corner_entry_adjustment', 0)
            corner_exit_adjustment = getattr(spring_calculation, 'corner_exit_adjustment', 0)
            
            # Get entry/exit multipliers
            entry_multipliers = CORNER_ENTRY_ADJUSTMENT_TABLE.get(corner_entry_adjustment, CORNER_ENTRY_ADJUSTMENT_TABLE[0])
            exit_multipliers = CORNER_EXIT_ADJUSTMENT_TABLE.get(corner_exit_adjustment, CORNER_EXIT_ADJUSTMENT_TABLE[0])
            
            # Calculate damper settings
            front_compression = int((20 + front_critical_damping_half / 1000) * 
                                    front_tire_damper_multiplier * 
                                    (entry_multipliers["front_compression"] + exit_multipliers["front_compression"]) / 2)
            
            rear_compression = int((20 + rear_critical_damping_half / 1000) * 
                                   rear_tire_damper_multiplier * 
                                   (entry_multipliers["rear_compression"] + exit_multipliers["rear_compression"]) / 2)
            
            front_extension = int((30 + front_critical_damping_half / 800) * 
                                  front_tire_damper_multiplier * 
                                  (entry_multipliers["front_rebound"] + exit_multipliers["front_rebound"]) / 2)
            
            rear_extension = int((30 + rear_critical_damping_half / 800) * 
                                 rear_tire_damper_multiplier * 
                                 (entry_multipliers["rear_rebound"] + exit_multipliers["rear_rebound"]) / 2)
            
            # Ensure values stay within bounds
            front_compression = max(20, min(40, front_compression))
            rear_compression = max(20, min(40, rear_compression))
            front_extension = max(30, min(50, front_extension))
            rear_extension = max(30, min(50, rear_extension))

            context.update({
                'front_compression': front_compression,
                'rear_compression': rear_compression,
                'front_extension': front_extension,
                'rear_extension': rear_extension,
            })
            
        except SpringCalculation.DoesNotExist:
            pass
    
    # Retrieve gear calculation if available
    if 'gear_calculation_id' in request.session:
        try:
            gear_calculation = GearCalculation.objects.get(id=request.session['gear_calculation_id'])
        
            # Initialize gear_speeds regardless of calculation success
            gear_speeds = {}
        
            # Calculate gear speeds
            if gear_calculation.gear_ratios and gear_calculation.final_drive and vehicle:
                for gear_name, ratio in gear_calculation.gear_ratios.items():
                    try:
                        tire_diameter_inches = gear_calculation.tire_diameter_inches or 25  # Default if not available
                        tire_diameter_meters = tire_diameter_inches * 0.0254  # Convert inches to meters
                        tire_circumference = math.pi * tire_diameter_meters  # Circumference in meters
                    
                        speed_at_max_power_mps = (gear_calculation.max_power_rpm * tire_circumference) / (ratio * gear_calculation.final_drive * 60)
                        speed_at_max_power_kph = speed_at_max_power_mps * 3.6
                        speed_at_max_power_mph = speed_at_max_power_kph / 1.60934  # Convert km/h to mph
                        gear_speeds[gear_name] = round(speed_at_max_power_mph, 1)
                    except Exception as e:
                        print(f"Error calculating speed for gear {gear_name}: {str(e)}")
                        gear_speeds[gear_name] = 0  # Default value on error
        
            # Always add gear_speeds to context if gear_calculation exists
            context['gear_speeds'] = gear_speeds
                
        except GearCalculation.DoesNotExist:
            pass
    
    context = {
        'spring_calculation': spring_calculation,
        'gear_calculation': gear_calculation,
        'vehicle_name': vehicle_name,
        'vehicle': vehicle,
    }
    
    # Add damper settings to context if available
    if spring_calculation:
        context.update({
            'front_compression': front_compression,
            'rear_compression': rear_compression,
            'front_extension': front_extension,
            'rear_extension': rear_extension,
        })
    
    if gear_calculation and hasattr(gear_calculation, 'torque_curve'):
        # Convert the numpy float64 values to regular Python floats
        torque_curve = []
        for point in gear_calculation.torque_curve:
            # Each point is a tuple of (rpm, torque)
            rpm = float(point[0])
            torque = float(point[1])
            torque_curve.append([rpm, torque])
        
        context['torque_curve_data'] = torque_curve
    
  
    if gear_calculation and hasattr(gear_calculation, 'torque_curve'):
        context['torque_curve_data'] = gear_calculation.torque_curve
    
    return render(request, 'spring_calc/complete_setup.html', context)

def calculate_gears(request):
    """View to calculate optimal gear ratios with persistence between pages"""
    # Get vehicle from session if available
    vehicle_id = None
    vehicle_name = "Unknown Vehicle"
    vehicle = None
    
    # Get OCR data and extract values
    if 'ocr_data' in request.session:
        gear_ratio = request.session['ocr_data'].get('gear_ratio')
        rpm = request.session['ocr_data'].get('rpm')  
        speed = request.session['ocr_data'].get('speed')
        final_drive = request.session['ocr_data'].get('final_drive')
    
        if gear_ratio and rpm and speed and final_drive:
            tire_diameter = calculate_tire_diameter(gear_ratio, rpm, speed, final_drive)
            request.session['ocr_data']['tire_diameter_inches'] = tire_diameter
            print(f"Calculated tire diameter: {tire_diameter} inches")
        elif 'tire_diameter_inches' not in request.session['ocr_data'] or not request.session['ocr_data']['tire_diameter_inches']:
            request.session['ocr_data']['tire_diameter_inches'] = 26.0
            print("Using default tire diameter: 26.0 inches")

    # Get vehicle information
    if 'ocr_data' in request.session and 'vehicle' in request.session['ocr_data']:
        vehicle_id = request.session['ocr_data']['vehicle']
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
            vehicle_name = vehicle.name
        except Vehicle.DoesNotExist:
            pass
    elif 'spring_calculation_id' in request.session:
        try:
            spring_calculation = SpringCalculation.objects.get(id=request.session['spring_calculation_id'])
            vehicle = spring_calculation.vehicle
            vehicle_id = vehicle.id
            vehicle_name = vehicle.name
        except SpringCalculation.DoesNotExist:
            pass
    
    # Get session data
    ocr_data = request.session.get('ocr_data', {})
    
    # Load previous calculation if available
    previous_calculation = None
    if 'gear_calculation_id' in request.session:
        try:
            previous_calculation = GearCalculation.objects.get(id=request.session['gear_calculation_id'])
        except:
            pass
    
    # Get torque curve data from session
    torque_curve_data = None
    if 'ocr_data' in request.session and 'torque_curve' in request.session['ocr_data']:
        torque_curve_data = request.session['ocr_data']['torque_curve']
        print(f"Found torque curve data in session with {len(torque_curve_data)} points")
    
    # Get power data from session
    power_data = {}
    if 'ocr_data' in request.session:
        for key in ['power_hp', 'torque_kgfm', 'min_rpm', 'max_rpm', 'max_power_rpm']:
            if key in request.session['ocr_data']:
                power_data[key] = request.session['ocr_data'][key]
                print(f"Found power data in session: {power_data}")

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
    
    # Handle GET request with parameters
    if request.method == 'GET' and request.GET:
        form = GearCalculatorForm(request.GET, vehicle_id=vehicle_id)
        return render(request, 'spring_calc/calculate_gears.html', {
            'form': form,
            'vehicle_name': vehicle_name,
            'previous_calculation': previous_calculation,
            'extracted_gear_ratios': extracted_gear_ratios,
            'extracted_final_drive': extracted_final_drive,
            'ocr_data': ocr_data 
        })
    
    # Handle POST request for calculations
    if request.method == 'POST':
        form = GearCalculatorForm(request.POST, vehicle_id=vehicle_id)
        
        # Add explicit debug output
        print("Form valid:", form.is_valid())
        if not form.is_valid():
            print("Form errors:", form.errors)
        else:
            print("Form is valid, proceeding with calculation")
            
        # Even if form is not valid, try to continue with calculation
        try:
            # Get the form data
            calculation = form.save(commit=False)
            
            # Set the vehicle if not already set
            if not calculation.vehicle_id and vehicle_id:
                calculation.vehicle_id = vehicle_id
                print(f"Set vehicle_id to {vehicle_id}")
            
            # Add torque curve data if available
            if torque_curve_data:
                calculation.torque_curve = torque_curve_data
            
            # Print all the form values for debugging
            print("Calculation parameters:")
            print(f"- vehicle_id: {calculation.vehicle_id}")
            print(f"- top_speed_mph: {calculation.top_speed_mph}")
            print(f"- min_corner_speed_mph: {calculation.min_corner_speed_mph}")
            print(f"- tire_diameter_inches: {calculation.tire_diameter_inches}")
            print(f"- power_hp: {calculation.power_hp}")
            print(f"- torque_kgfm: {calculation.torque_kgfm}")
            print(f"- min_rpm: {calculation.min_rpm}")
            print(f"- max_rpm: {calculation.max_rpm}")
            print(f"- max_power_rpm: {calculation.max_power_rpm}")
            print(f"- num_gears: {calculation.num_gears}")
            
            # Fill in any missing values with defaults
            if not calculation.top_speed_mph:
                calculation.top_speed_mph = 180
                
            if not calculation.min_corner_speed_mph:
                calculation.min_corner_speed_mph = 60
                
            if not calculation.tire_diameter_inches:
                calculation.tire_diameter_inches = 26.31
                
            if not calculation.power_hp:
                calculation.power_hp = 498
                
            if not calculation.torque_kgfm:
                calculation.torque_kgfm = 50.1
                
            if not calculation.min_rpm:
                calculation.min_rpm = 1300
                
            if not calculation.max_rpm:
                calculation.max_rpm = 8755
                
            if not calculation.max_power_rpm:
                calculation.max_power_rpm = 8525
                
            if not calculation.num_gears:
                calculation.num_gears = 6

            # Calculate gear ratios
            try:
                # Calculate minimum first gear ratio based on min corner speed
                target_corner_rpm = calculation.min_rpm + (calculation.max_power_rpm - calculation.min_rpm) * 0.3
                
                # Excel uses ~22.5% drop between gears
                gear_ratio_step = 1 / 0.775
                
                # Calculate top gear ratio to reach top speed at max RPM
                mph_to_kph = 1.60934
                top_speed_kph = calculation.top_speed_mph * mph_to_kph
                top_speed_mps = top_speed_kph / 3.6
                
                # Now calculate a final drive based on power
                hp_based_final_drive = 4.8 - (calculation.power_hp - 100) * 0.0025
                hp_based_final_drive = max(3.0, min(5.0, hp_based_final_drive))
                
                # Calculate the top gear ratio
                final_top_gear_ratio = (calculation.max_rpm * math.pi * calculation.tire_diameter_inches) / (calculation.top_speed_mph * hp_based_final_drive * 1056)
                
                # Build all gear ratios
                gear_values = []
                for i in range(calculation.num_gears):
                    gear_number = calculation.num_gears - i
                    
                    if i == 0:
                        # Top gear
                        ratio = final_top_gear_ratio
                    else:
                        # Lower gears increase by step factor
                        ratio = gear_values[-1] * gear_ratio_step
                    
                    gear_values.append(ratio)
                
                # Reverse to get from 1st to top gear
                gear_values.reverse()
                
                # Format the gear ratios dict
                final_gear_ratios = {}
                for i in range(calculation.num_gears):
                    gear_number = i + 1
                    gear_ratio = gear_values[i]
                    
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
                    final_gear_ratios[gear_name] = round(gear_ratio, 3)
                
                # Round the final drive
                final_drive_rounded = round(hp_based_final_drive, 3)
                
                # Store the results
                calculation.gear_ratios = final_gear_ratios
                calculation.final_drive = final_drive_rounded
                
                # Save calculation to database
                calculation.save()
                
                # Store the calculation id in session
                request.session['gear_calculation_id'] = calculation.id
                
                # Success message
                messages.success(request, "Gear ratio calculation successful!")
                
                # Prepare gear speeds for display
                gear_speeds = {}
                for gear_name, ratio in final_gear_ratios.items():
                    # Calculate speed at max power RPM for display
                    speed_mph = (calculation.max_power_rpm * math.pi * calculation.tire_diameter_inches) / (ratio * final_drive_rounded * 1056)
                    gear_speeds[gear_name] = round(speed_mph, 1)
                
                # Render the template with the results
                return render(request, 'spring_calc/calculate_gears.html', {
                    'form': form,
                    'calculation': calculation,
                    'vehicle_name': vehicle_name,
                    'gear_speeds': gear_speeds,
                    'final_drive': final_drive_rounded
                })
                
            except Exception as calc_error:
                # Detailed error handling for calculation errors
                import traceback
                print("Error in gear ratio calculation:")
                traceback.print_exc()
                messages.error(request, f"Error calculating gear ratios: {str(calc_error)}")
                
        except Exception as e:
            # Handle any other errors
            print(f"Error processing gear form: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f"Error processing form: {str(e)}")
        
        # Always return the form with any available data if an error occurred
        return render(request, 'spring_calc/calculate_gears.html', {
            'form': form,
            'vehicle_name': vehicle_name,
            'previous_calculation': previous_calculation,
            'extracted_gear_ratios': extracted_gear_ratios,
            'extracted_final_drive': extracted_final_drive,
            'torque_curve_data': torque_curve_data
        })
    
    # Default case - GET request without parameters
    # Create a new form and render the template
    form = GearCalculatorForm(initial=initial_data, vehicle_id=vehicle_id)
    
    # Always return a response for the default case
    return render(request, 'spring_calc/calculate_gears.html', {
        'form': form, 
        'vehicle_name': vehicle_name,
        'previous_calculation': previous_calculation,
        'extracted_gear_ratios': extracted_gear_ratios,
        'extracted_final_drive': extracted_final_drive,
        'torque_curve_data': torque_curve_data
    })