# spring_calc/decorators.py
import logging
import traceback
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

logger = logging.getLogger(__name__)

def handle_view_exceptions(view_func):
    """
    Decorator to handle exceptions in views with proper logging and user feedback
    
    Args:
        view_func: The view function to wrap
        
    Returns:
        Wrapped function that handles exceptions
    """
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            # Log the error
            logger.error(f"Error in {view_func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Add message for user
            messages.error(request, f"An error occurred: {str(e)}")
            
            # Redirect to a safe page
            return redirect('home')
    return wrapped

def require_vehicle_selection(view_func):
    """
    Decorator to ensure a vehicle is selected before proceeding
    
    Args:
        view_func: The view function to wrap
        
    Returns:
        Wrapped function that checks for vehicle selection
    """
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        # Check if vehicle is selected in session
        vehicle_id = None
        
        if 'ocr_data' in request.session and 'vehicle' in request.session['ocr_data']:
            vehicle_id = request.session['ocr_data']['vehicle']
        
        # Also check spring_calculation_id and retrieve vehicle
        elif 'spring_calculation_id' in request.session:
            from .models import SpringCalculation
            try:
                spring_calculation = SpringCalculation.objects.get(id=request.session['spring_calculation_id'])
                vehicle_id = spring_calculation.vehicle.id
            except SpringCalculation.DoesNotExist:
                pass
        
        # Check gear_calculation_id as well
        elif 'gear_calculation_id' in request.session:
            from .models import GearCalculation
            try:
                gear_calculation = GearCalculation.objects.get(id=request.session['gear_calculation_id'])
                vehicle_id = gear_calculation.vehicle.id
            except GearCalculation.DoesNotExist:
                pass
        
        if not vehicle_id and request.method != 'POST':
            # No vehicle selected, redirect to upload screenshot
            messages.warning(request, "Please select a vehicle before proceeding")
            return redirect('upload_screenshot')
        
        # Vehicle is selected, proceed with the view
        return view_func(request, *args, **kwargs)
    return wrapped

def log_view_access(view_func):
    """
    Decorator to log access to views for debugging
    
    Args:
        view_func: The view function to wrap
        
    Returns:
        Wrapped function that logs access
    """
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        logger.debug(f"Accessing {view_func.__name__} view")
        
        # Log session data if debug mode is enabled
        if hasattr(request, 'session'):
            session_data = {}
            for key in request.session.keys():
                # Don't log sensitive data
                if key not in ['_auth_user_id', 'password']:
                    session_data[key] = request.session[key]
            
            logger.debug(f"Session data for {view_func.__name__}: {session_data}")
        
        return view_func(request, *args, **kwargs)
    return wrapped