from django.urls import path
from .views.setup_views import dashboard
from .views.upload_views import home, upload_screenshot
from .views.calculation_views import calculate_springs, calculate_tire_diameter
from .views.gear_views import calculate_gears
from .views.setup_views import (
    complete_setup, 
    saved_setups, 
    delete_setup, 
    save_setup, 
    reset_calculations, 
    reset_all_data
)

urlpatterns = [
    # Home and upload views
    path('', home, name='home'),
    path('upload-screenshot/', upload_screenshot, name='upload_screenshot'),
    path('dashboard/', dashboard, name='dashboard'),

    # Calculator views
    path('spring-calculator/', calculate_springs, name='calculate_springs'),
    path('gear-calculator/', calculate_gears, name='calculate_gears'),
    path('tire-calculator/', calculate_tire_diameter, name='calculate_tire_diameter'),
    
    # Setup management views
    path('complete-setup/', complete_setup, name='complete_setup'),
    path('saved-setups/', saved_setups, name='saved_setups'),
    path('delete-setup/', delete_setup, name='delete_setup'),
    path('save-setup/', save_setup, name='save_setup'),
    path('reset-calculations/', reset_calculations, name='reset_calculations'),
    
    # Data management views
    path('reset-calculations/', reset_calculations, name='reset_calculations'),
    path('reset-all-data/', reset_all_data, name='reset_all_data'),
]
