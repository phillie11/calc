# spring_calc/views/__init__.py

from .calculation_views import calculate_springs, calculate_tire_diameter
from .gear_views import calculate_gears
from .setup_views import (
    complete_setup, 
    saved_setups, 
    delete_setup, 
    save_setup, 
    reset_calculations,  # This is missing in setup_views.py
    reset_all_data
)
from .upload_views import upload_screenshot, home

__all__ = [
    'calculate_springs',
    'calculate_gears',
    'calculate_tire_diameter',
    'complete_setup',
    'saved_setups',
    'delete_setup',
    'save_setup',
    'reset_calculations',
    'reset_all_data',
    'upload_screenshot',
    'home',
]