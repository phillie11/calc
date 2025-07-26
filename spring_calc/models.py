# spring_calc/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, DecimalValidator
from django.contrib.auth.models import User
from cars.models import Vehicle
from django.http import JsonResponse
from django.utils import timezone


class BaseCalculation(models.Model):
    """Abstract base class for all calculation models"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True

class SpringCalculation(BaseCalculation):
    """Model to store suspension calculations with validation"""
    # Tire type choices
    TIRE_CHOICES = [
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
    TRACK_CHOICES = [
        ('Fast', 'Fast Track'),
        ('Technical', 'Technical Track')
    ]
    
    # Input parameters
    performance_points = models.FloatField(
        null=True, blank=True, 
        validators=[MinValueValidator(0), MaxValueValidator(9999.99)],
        help_text="Performance Points (PP)"
    )
    
    front_tires = models.CharField(
        max_length=2, 
        choices=TIRE_CHOICES, 
        default='RM',
        help_text="Front tire type"
    )
    
    rear_tires = models.CharField(
        max_length=2, 
        choices=TIRE_CHOICES, 
        default='RM',
        help_text="Rear tire type"
    )
    
    arb_stiffness_multiplier = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.5), MaxValueValidator(2.0)], 
        help_text="ARB Stiffness multiplier"
    )
    
    vehicle_weight = models.IntegerField(
        validators=[MinValueValidator(500), MaxValueValidator(5000)],
        help_text="Vehicle weight in kg", 
        default=1400
    )
    
    front_weight_distribution = models.FloatField(
        validators=[MinValueValidator(25), MaxValueValidator(75)],
        help_text="Front weight distribution (%)", 
        default=50
    )
    
    front_ride_height = models.IntegerField(
        validators=[MinValueValidator(50), MaxValueValidator(200)],
        help_text="Front ride height in mm", 
        default=100
    )
    
    rear_ride_height = models.IntegerField(
        validators=[MinValueValidator(50), MaxValueValidator(200)],
        help_text="Rear ride height in mm", 
        default=100
    )
    
    front_downforce = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5000)],
        help_text="Front downforce", 
        default=0
    )
    
    rear_downforce = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10000)],
        help_text="Rear downforce", 
        default=0
    )
    
    track_type = models.CharField(
        max_length=20, 
        choices=TRACK_CHOICES,
        default="Fast"
    )
    
    tire_wear_multiplier = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        default=25
    )
    
    high_speed_stability = models.FloatField(
        validators=[MinValueValidator(-1.0), MaxValueValidator(1.0)],
        default=1.0
    )
    
    low_speed_stability = models.FloatField(
        validators=[MinValueValidator(-1.0), MaxValueValidator(1.0)],
        default=0.0
    )
    
    rotational_g_40mph = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        default=0.0
    )
    
    rotational_g_75mph = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        default=0.0
    )
    
    rotational_g_150mph = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
        default=0.0
    )
    
    roll_bar_multiplier = models.FloatField(
        validators=[MinValueValidator(0.5), MaxValueValidator(2.0)],
        default=1.0
    )
    
    base_camber = models.FloatField(default=0.0)
    
    stiffness_multiplier = models.FloatField(
        help_text="Stiffness multiplier", 
        validators=[MinValueValidator(0.5), MaxValueValidator(2.0)],
        default=1.0
    )
    
    spring_frequency_offset = models.IntegerField(
        help_text="Spring frequency offset (-5 to 6)", 
        validators=[MinValueValidator(-5), MaxValueValidator(6)],
        default=0
    )
    
    ou_adjustment = models.IntegerField(
        help_text="Oversteer/Understeer adjustment (-5 to 5)", 
        validators=[MinValueValidator(-5), MaxValueValidator(5)],
        default=0
    )
    
    corner_entry_adjustment = models.IntegerField(
        help_text="Corner entry adjustment (-5 to 5)",
        validators=[MinValueValidator(-5), MaxValueValidator(5)], 
        default=0
    )
    
    corner_exit_adjustment = models.IntegerField(
        help_text="Corner exit adjustment (-5 to 5)",
        validators=[MinValueValidator(-5), MaxValueValidator(5)], 
        default=0
    )
    
    # Results
    front_spring_rate = models.FloatField(
        help_text="Calculated front spring rate (N/mm)", 
        null=True, blank=True
    )
    
    rear_spring_rate = models.FloatField(
        help_text="Calculated rear spring rate (N/mm)", 
        null=True, blank=True
    )
    
    front_spring_frequency = models.FloatField(
        help_text="Front spring frequency (Hz)", 
        null=True, blank=True
    )
    
    rear_spring_frequency = models.FloatField(
        help_text="Rear spring frequency (Hz)", 
        null=True, blank=True
    )
    
    front_roll_bar = models.FloatField(null=True, blank=True)
    rear_roll_bar = models.FloatField(null=True, blank=True)
    front_camber = models.FloatField(null=True, blank=True)
    rear_camber = models.FloatField(null=True, blank=True)
    front_toe = models.FloatField(null=True, blank=True)
    rear_toe = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"Spring calculation for {self.vehicle.name}"
    
    @property
    def weight_ratio_front(self):
        """Return front weight ratio as a decimal (0.0-1.0)"""
        return self.front_weight_distribution / 100.0
        
    @property 
    def weight_ratio_rear(self):
        """Return rear weight ratio as a decimal (0.0-1.0)"""
        return 1.0 - self.weight_ratio_front
    
    class Meta:
        indexes = [
            models.Index(fields=['vehicle']),
            models.Index(fields=['created_at']),
        ]

class TireSizeCalculation(models.Model):
    """Model to store tire size calculation data"""
    speed = models.FloatField(
        help_text="Vehicle speed in km/h",
        validators=[MinValueValidator(0), MaxValueValidator(500)]
    )
    
    rpm = models.IntegerField(
        help_text="Engine RPM",
        validators=[MinValueValidator(1000), MaxValueValidator(12000)]
    )
    
    gear_ratio = models.FloatField(
        help_text="Current gear ratio",
        validators=[MinValueValidator(0.1), MaxValueValidator(5.0)]
    )
    
    final_drive = models.FloatField(
        help_text="Final drive ratio",
        validators=[MinValueValidator(2.0), MaxValueValidator(6.0)]
    )
    
    tire_size = models.FloatField(
        help_text="Calculated tire size in inches", 
        null=True, blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Tire Size Calculation ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
        ]

class GearCalculation(BaseCalculation):
    """Model to store gear ratio calculations with validation"""
    # Min corner gear choices
    MIN_CORNER_GEAR_CHOICES = [
        (1, '1st Gear'),
        (2, '2nd Gear'),
        (3, '3rd Gear'),
        (4, '4th Gear'),
    ]
    
    # Vehicle parameters
    top_speed_mph = models.IntegerField(
        help_text="Top speed on straight in mph", 
        validators=[MinValueValidator(50), MaxValueValidator(350)],
        default=180
    )
    
    min_corner_speed_mph = models.IntegerField(
        help_text="Minimum corner speed in mph", 
        validators=[MinValueValidator(20), MaxValueValidator(120)],
        default=60
    )
    
    tire_diameter_inches = models.FloatField(
        help_text="Tire diameter in inches",
        validators=[MinValueValidator(15), MaxValueValidator(35)], 
        null=True, blank=True
    )
    
    min_corner_gear = models.IntegerField(
        help_text="Minimum corner gear", 
        choices=MIN_CORNER_GEAR_CHOICES,
        default=1
    )
    
    # Engine specifications
    min_rpm = models.IntegerField(
        help_text="Minimum engine RPM", 
        validators=[MinValueValidator(500), MaxValueValidator(3000)],
        default=1000
    )
    
    max_rpm = models.IntegerField(
        help_text="Maximum engine RPM", 
        validators=[MinValueValidator(3000), MaxValueValidator(18000)],
        default=8000
    )
    
    power_hp = models.IntegerField(
        help_text="Engine power in HP", 
        validators=[MinValueValidator(2), MaxValueValidator(5000)],
        default=500
    )
    
    max_power_rpm = models.IntegerField(
        help_text="RPM at maximum power", 
        validators=[MinValueValidator(3000), MaxValueValidator(18000)],
        default=6500
    )
    
    torque_kgfm = models.FloatField(
        help_text="Engine torque in kg-fm", 
        validators=[MinValueValidator(1.0), MaxValueValidator(500.0)],
        default=50.0
    )
    
    # Transmission settings
    num_gears = models.IntegerField(
        help_text="Number of gears", 
        validators=[MinValueValidator(4), MaxValueValidator(9)],
        default=6
    )
    
    final_drive = models.FloatField(
        help_text="Final drive ratio", 
        validators=[MinValueValidator(2.0), MaxValueValidator(6.0)],
        default=3.7
    )
    
    # Calculated gear ratios (stored as JSON)
    gear_ratios = models.JSONField(
        blank=True, 
        null=True, 
        default=dict
    )
    
    # Store the torque curve data as a JSON array of [rpm, torque] pairs
    torque_curve = models.JSONField(
        blank=True, 
        null=True, 
        default=list, 
        help_text="Torque curve data as array of [rpm, torque] pairs"
    )
    
    # Calculated results
    top_speed_calculated = models.FloatField(
        help_text="Calculated top speed in mph", 
        null=True, blank=True
    )
    
    acceleration_estimate = models.FloatField(
        help_text="Estimated 0-60 time in seconds", 
        null=True, blank=True
    )
    
    def __str__(self):
        return f"Gear calculation for {self.vehicle.name}"
    
    class Meta:
        indexes = [
            models.Index(fields=['vehicle']),
            models.Index(fields=['created_at']),
        ]

class SavedSetup(models.Model):
    """Model to store saved vehicle setups"""
    name = models.CharField(
        max_length=100, 
        help_text="Setup name"
    )
    
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.CASCADE,
        related_name='setups'
    )
    
    spring_calculation = models.ForeignKey(
        SpringCalculation, 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        related_name='saved_setups'
    )
    
    gear_calculation = models.ForeignKey(
        GearCalculation, 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        related_name='saved_setups'
    )
    
    date_saved = models.DateTimeField(auto_now_add=True)
    
    # Optional user field for multi-user support
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        related_name='saved_setups'
    )
    
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.vehicle.name}"
    
    class Meta:
        ordering = ['-date_saved']
        indexes = [
            models.Index(fields=['vehicle']),
            models.Index(fields=['date_saved']),
            models.Index(fields=['user']),
        ]