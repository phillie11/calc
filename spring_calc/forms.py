# spring_calc/forms.py
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from cars.models import Vehicle
from .models import SpringCalculation, TireSizeCalculation, GearCalculation, SavedSetup

class BaseForm(forms.ModelForm):
    """Base form with common functionality"""
    
    def __init__(self, *args, **kwargs):
        # Initialize the form
        super().__init__(*args, **kwargs)
        
        # Apply Bootstrap classes to all form fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.EmailInput, forms.URLInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})

# Define tire type choices
TIRE_TYPE_CHOICES = [
    ('CH', 'Comfort: Hard'),
    ('CM', 'Comfort: Medium'),
    ('CS', 'Comfort: Soft'),
    ('SH', 'Sport: Hard'),
    ('SM', 'Sport: Medium'),
    ('SS', 'Sport: Soft'),
    ('RH', 'Racing: Hard'),
    ('RM', 'Racing: Medium'),
    ('RS', 'Racing: Soft'),
    ('RI', 'Racing: Intermediate'),
    ('RW', 'Racing: Heavy Wet'),
]

# Track type choices
TRACK_TYPE_CHOICES = [
    ('Fast', 'Fast Track'),
    ('Technical', 'Technical Track')
]

# Spring frequency offset choices
SPRING_FREQUENCY_OFFSET_CHOICES = [
    (-5, '-5'),
    (-4, '-4'),
    (-3, '-3'),
    (-2, '-2'),
    (-1, '-1'),
    (0, '0 (Neutral)'),
    (1, '+1'),
    (2, '+2'),
    (3, '+3'),
    (4, '+4'),
    (5, '+5'),
    (6, '+6')
]

# Oversteer/Understeer choices
OVERSTEER_UNDERSTEER_CHOICES = [
    (-5, '-5 (Understeer)'),
    (-4, '-4'),
    (-3, '-3'),
    (-2, '-2'),
    (-1, '-1'),
    (0, '0 (Neutral)'),
    (1, '+1'),
    (2, '+2'),
    (3, '+3'),
    (4, '+4'),
    (5, '+5 (Oversteer)')
]

# Corner adjustment choices
CORNER_ADJUSTMENT_CHOICES = [
    (-5, '-5'),
    (-4, '-4'),
    (-3, '-3'),
    (-2, '-2'),
    (-1, '-1'),
    (0, '0 (Neutral)'),
    (1, '+1'),
    (2, '+2'),
    (3, '+3'),
    (4, '+4'),
    (5, '+5'),
]

class SpringCalculatorForm(BaseForm):
    """Form for spring calculator with input validation"""
    
    # Fields with custom validation
    performance_points = forms.FloatField(
        label="Performance Points (PP)",
        min_value=0,
        max_value=9999.99,
        required=False,
        help_text="Leave blank if unknown"
    )
    
    front_tires = forms.ChoiceField(
        label="Front Tires",
        choices=TIRE_TYPE_CHOICES,
        initial='RM',  # Default to Racing: Medium
    )
    
    rear_tires = forms.ChoiceField(
        label="Rear Tires",
        choices=TIRE_TYPE_CHOICES,
        initial='RM',  # Default to Racing: Medium
    )
    
    arb_stiffness_multiplier = forms.FloatField(
        label="ARB Stiffness",
        initial=1.0,
        min_value=0.5,
        max_value=2.0,
        help_text="Anti-roll bar stiffness multiplier (0.5 to 2.0)"
    )

    # Form fields
    ou_adjustment = forms.IntegerField(
        label="Oversteer/Understeer Adjustment",
        initial=0,
        widget=forms.Select(choices=OVERSTEER_UNDERSTEER_CHOICES),
        help_text="Adjust handling balance (-5 Understeer to +5 Oversteer)"
    )
    
    corner_entry_adjustment = forms.IntegerField(
        label="Corner Entry Adjustment",
        initial=0,
        widget=forms.Select(choices=CORNER_ADJUSTMENT_CHOICES),
        help_text="Adjust corner entry handling (-5 to +5)"
    )
    
    corner_exit_adjustment = forms.IntegerField(
        label="Corner Exit Adjustment",
        initial=0,
        widget=forms.Select(choices=CORNER_ADJUSTMENT_CHOICES),
        help_text="Adjust corner exit handling (-5 to +5)"
    )
    
    vehicle_weight = forms.IntegerField(
        label="Vehicle Weight (kg)",
        initial=0,
        min_value=500,
        max_value=5000,
        help_text="Enter the weight of your vehicle in kg"
    )

    front_ride_height = forms.IntegerField(
        label="Front Ride Height (mm)",
        min_value=50,
        max_value=200,
        initial=100,
        help_text="Front suspension ride height in mm"
    )

    rear_ride_height = forms.IntegerField(
        label="Rear Ride Height (mm)",
        min_value=50,
        max_value=200,
        initial=100,
        help_text="Rear suspension ride height in mm"
    )
    
    front_weight_distribution = forms.IntegerField(
        label="Front Weight Distribution (%)",
        initial=50,  # Set default to 50%
        min_value=25,
        max_value=75,
        help_text="Front weight distribution percentage (25-75%)"
    )

    # Fields for alignment calculations
    track_type = forms.ChoiceField(
        label="Track Type", 
        choices=TRACK_TYPE_CHOICES,
        initial='Fast',
        help_text="Track type affects alignment calculations"
    )

    tire_wear_multiplier = forms.IntegerField(
        label="Tire Wear Multiplier",
        initial=25,
        min_value=0,
        max_value=50,
        help_text="Higher values reduce camber for better tire life"
    )

    low_speed_stability = forms.FloatField(
        label="Low Speed Stability",
        initial=0.00,
        min_value=-1.00,
        max_value=1.00,
        help_text="Values from -1.00 to +1.00"
    )

    high_speed_stability = forms.FloatField(
        label="High Speed Stability",
        initial=1.00,
        min_value=-1.00,
        max_value=1.00,
        help_text="Values from -1.00 to +1.00"
    )

    # Rotational G fields
    rotational_g_40mph = forms.FloatField(
        label="Rotational G @ 40 mph",
        initial=0.00,
        min_value=0.00,
        max_value=9.00,
        help_text="Cornering G-force at 40 mph"
    )

    rotational_g_75mph = forms.FloatField(
        label="Rotational G @ 75 mph",
        initial=0.00,
        min_value=0.00,
        max_value=9.00,
        help_text="Cornering G-force at 75 mph"
    )

    rotational_g_150mph = forms.FloatField(
        label="Rotational G @ 150 mph",
        initial=0.00,
        min_value=0.00,
        max_value=9.00,
        help_text="Cornering G-force at 150 mph"
    )

    # Main form definition
    class Meta:
        model = SpringCalculation
        fields = [
            'vehicle', 
            'vehicle_weight', 
            'front_weight_distribution', 
            'front_ride_height', 
            'rear_ride_height',
            'front_downforce', 
            'rear_downforce', 
            'stiffness_multiplier', 
            'spring_frequency_offset',
            'performance_points',
            'front_tires',
            'rear_tires',
            'arb_stiffness_multiplier',
            'ou_adjustment',
            'corner_entry_adjustment',
            'corner_exit_adjustment',
            'track_type',
            'tire_wear_multiplier',
            'low_speed_stability',
            'high_speed_stability',
            'rotational_g_40mph',
            'rotational_g_75mph',
            'rotational_g_150mph'
        ]
        
        widgets = {
            'vehicle': forms.Select(),
            'front_downforce': forms.NumberInput(attrs={'min': '0', 'max': '5000'}),
            'rear_downforce': forms.NumberInput(attrs={'min': '0', 'max': '10000'}),
            'stiffness_multiplier': forms.NumberInput(attrs={'min': '0.5', 'max': '2.0', 'step': '0.05'}),
            'spring_frequency_offset': forms.Select(choices=SPRING_FREQUENCY_OFFSET_CHOICES),
        }
        
    def clean(self):
        """
        Custom validation for interdependent fields
        """
        cleaned_data = super().clean()
       
        if not cleaned_data.get('vehicle'):
            # Raise a validation error for missing vehicle
            raise forms.ValidationError({
                'vehicle': 'Please select a vehicle before proceeding.'
            })
            
        # Validate ride height difference
        front_height = cleaned_data.get('front_ride_height')
        rear_height = cleaned_data.get('rear_ride_height')
        
        if front_height and rear_height:
            # Check if the height difference is too extreme
            if abs(front_height - rear_height) > 100:
                raise forms.ValidationError(
                    "Front and rear ride height difference should not exceed 100mm for optimal handling"
                )
       
        # Validate rotational G values are reasonable
        g_40mph = cleaned_data.get('rotational_g_40mph', 0)
        g_75mph = cleaned_data.get('rotational_g_75mph', 0)
        g_150mph = cleaned_data.get('rotational_g_150mph', 0)
        
        if g_40mph > g_75mph and g_40mph > 1.0 and g_75mph > 1.0:
            self.add_warning('rotational_g_40mph', 
                            'G-force at 40mph is higher than at 75mph, which is unusual')
            
        if g_75mph > g_150mph and g_75mph > 1.0 and g_150mph > 1.0:
            self.add_warning('rotational_g_75mph', 
                            'G-force at 75mph is higher than at 150mph, which is unusual')
            
        # Auto-populate vehicle weight from model if not set
        vehicle = cleaned_data.get('vehicle')
        vehicle_weight = cleaned_data.get('vehicle_weight')
        
        if vehicle and (not vehicle_weight or vehicle_weight == 0):
            cleaned_data['vehicle_weight'] = vehicle.base_weight
            self.cleaned_data['vehicle_weight'] = vehicle.base_weight
       
        return cleaned_data
    
    def add_warning(self, field, message):
        """
        Add a warning message to the form's non-field errors
        """
        if not hasattr(self, 'warnings'):
            self.warnings = []
        
        self.warnings.append({
            'field': field,
            'message': message
        })


class TireSizeCalculatorForm(forms.Form):
    """Form for calculating tire size based on speed, RPM, gear ratio and final drive"""
    
    speed = forms.FloatField(
        label="Speed (km/h)",
        min_value=0,
        max_value=500,
        widget=forms.NumberInput(attrs={'step': '0.1'}),
        help_text="Enter the current speed in km/h"
    )
    
    rpm = forms.IntegerField(
        label="Engine RPM",
        min_value=1000,
        max_value=12000,
        widget=forms.NumberInput(attrs={'step': '1'}),
        help_text="Enter the current engine RPM"
    )
    
    gear_ratio = forms.FloatField(
        label="Gear Ratio",
        min_value=0.1,
        max_value=5,
        widget=forms.NumberInput(attrs={'step': '0.001'}),
        help_text="Enter the current gear ratio"
    )
    
    final_drive = forms.FloatField(
        label="Final Drive Ratio",
        min_value=2,
        max_value=6,
        widget=forms.NumberInput(attrs={'step': '0.001'}),
        help_text="Enter the final drive ratio"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput)):
                field.widget.attrs.update({'class': 'form-control'})

class GearCalculatorForm(BaseForm):
    """Form for gear ratio calculator with improved validation"""
    
    # Track parameters
    top_speed_mph = forms.IntegerField(
        label="Top Speed on Straight (mph)",
        min_value=50,
        max_value=350,
        initial=180,
        help_text="Maximum speed achievable on the longest straight"
    )
    
    min_corner_speed_mph = forms.IntegerField(
        label="Min Corner Speed (mph)",
        min_value=20,
        max_value=120,
        initial=60,
        help_text="Minimum speed in the tightest corner"
    )
    
    # Corner gear choices
    MIN_CORNER_GEAR_CHOICES = [
        (1, '1st Gear'),
        (2, '2nd Gear'),
        (3, '3rd Gear'),
        (4, '4th Gear'),
    ]
    
    min_corner_gear = forms.ChoiceField(
        label="Min Corner Gear",
        choices=MIN_CORNER_GEAR_CHOICES,
        initial=1,
        help_text="Preferred gear for the tightest corner"
    )
    
    tire_diameter_inches = forms.FloatField(
        widget=forms.NumberInput(attrs={'min': '15', 'max': '35', 'step': '0.01'}),
        required=False,
        help_text="Enter tire diameter in inches (click 'Calculate Tire Size' if unknown)"
    )
    
    # Engine parameters
    power_hp = forms.IntegerField(
        label="Power (HP)",
        min_value=2,
        max_value=5000,
        initial=500,
        help_text="Engine horsepower"
    )
    
    min_rpm = forms.IntegerField(
        label="Min RPM",
        min_value=500,
        max_value=3000,
        initial=1000,
        help_text="Minimum usable engine RPM"
    )
    
    max_rpm = forms.IntegerField(
        label="Max RPM",
        min_value=3000,
        max_value=18000,
        initial=8000,
        help_text="Maximum engine RPM (redline)"
    )
    
    max_power_rpm = forms.IntegerField(
        label="RPM @ Max Power",
        min_value=3000,
        max_value=18000,
        initial=6500,
        help_text="RPM at which maximum power is produced"
    )
    
    torque_kgfm = forms.FloatField(
        label="Torque (kg-fm)",
        min_value=1.0,
        max_value=500.0,
        initial=50.0,
        help_text="Maximum engine torque in kg-fm"
    )
    
    num_gears = forms.IntegerField(
        label="Number of Gears",
        min_value=4,
        max_value=9,
        initial=6,
        help_text="Number of transmission gears"
    )
    
    class Meta:
        model = GearCalculation
        fields = [
            'vehicle', 'top_speed_mph', 'min_corner_speed_mph', 
            'tire_diameter_inches', 'power_hp', 'min_rpm', 'max_rpm', 
            'max_power_rpm', 'torque_kgfm', 'num_gears', 'min_corner_gear'
        ]
    
    def __init__(self, *args, **kwargs):
        vehicle_id = kwargs.pop('vehicle_id', None)
        super().__init__(*args, **kwargs)
        
        if vehicle_id:
            # If vehicle_id is provided, set it as the initial value
            self.fields['vehicle'].initial = vehicle_id
            
            try:
                # Make vehicle field hidden if already selected
                self.fields['vehicle'].widget = forms.HiddenInput()
            except Vehicle.DoesNotExist:
                pass
    
    def clean(self):
        """Custom validation for gear calculator form"""
        cleaned_data = super().clean()
        
        # Validate vehicle
        if not cleaned_data.get('vehicle'):
            raise forms.ValidationError({
                'vehicle': 'Please select a vehicle before proceeding.'
            })
        
        # Validate RPM values
        min_rpm = cleaned_data.get('min_rpm')
        max_rpm = cleaned_data.get('max_rpm')
        max_power_rpm = cleaned_data.get('max_power_rpm')
        
        if min_rpm and max_rpm and min_rpm >= max_rpm:
            raise forms.ValidationError({
                'min_rpm': 'Minimum RPM must be less than maximum RPM.'
            })
        
        if max_power_rpm and max_rpm and max_power_rpm > max_rpm:
            raise forms.ValidationError({
                'max_power_rpm': 'Maximum power RPM cannot be greater than maximum RPM.'
            })
            
        if max_power_rpm and min_rpm and max_power_rpm < min_rpm:
            raise forms.ValidationError({
                'max_power_rpm': 'Maximum power RPM cannot be less than minimum RPM.'
            })
        
        # Validate tire diameter
        tire_diameter = cleaned_data.get('tire_diameter_inches')
        if not tire_diameter:
            # Default tire diameter for GT7 cars
            cleaned_data['tire_diameter_inches'] = 26.0
        
        # Validate corner speed
        top_speed = cleaned_data.get('top_speed_mph')
        min_corner_speed = cleaned_data.get('min_corner_speed_mph')
        
        if top_speed and min_corner_speed and min_corner_speed >= top_speed:
            raise forms.ValidationError({
                'min_corner_speed_mph': 'Corner speed must be less than top speed.'
            })
        
        return cleaned_data

class SavedSetupForm(BaseForm):
    """Form for saving and managing vehicle setups"""
    
    name = forms.CharField(
        label="Setup Name",
        max_length=100,
        help_text="Give your setup a memorable name"
    )
    
    notes = forms.CharField(
        label="Notes",
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Any additional notes about this setup"
    )
    
    class Meta:
        model = SavedSetup
        fields = ['name', 'notes']
        
    def __init__(self, *args, **kwargs):
        # Get spring_calculation_id and gear_calculation_id from kwargs
        self.spring_calculation_id = kwargs.pop('spring_calculation_id', None)
        self.gear_calculation_id = kwargs.pop('gear_calculation_id', None)
        self.vehicle_id = kwargs.pop('vehicle_id', None)
        
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        """Override save to handle calculation references"""
        instance = super().save(commit=False)
        
        # Set vehicle
        if self.vehicle_id:
            try:
                instance.vehicle = Vehicle.objects.get(id=self.vehicle_id)
            except Vehicle.DoesNotExist:
                raise forms.ValidationError("Selected vehicle does not exist.")
        
        # Set spring calculation
        if self.spring_calculation_id:
            try:
                instance.spring_calculation = SpringCalculation.objects.get(id=self.spring_calculation_id)
            except SpringCalculation.DoesNotExist:
                instance.spring_calculation = None
        
        # Set gear calculation
        if self.gear_calculation_id:
            try:
                instance.gear_calculation = GearCalculation.objects.get(id=self.gear_calculation_id)
            except GearCalculation.DoesNotExist:
                instance.gear_calculation = None
        
        # Validate that at least one calculation is set
        if not instance.spring_calculation and not instance.gear_calculation:
            raise forms.ValidationError("At least one calculation (suspension or gears) must be saved.")
        
        # If vehicle not set from calculations, try to infer from calculations
        if not instance.vehicle:
            if instance.spring_calculation:
                instance.vehicle = instance.spring_calculation.vehicle
            elif instance.gear_calculation:
                instance.vehicle = instance.gear_calculation.vehicle
        
        if commit:
            instance.save()
        
        return instance