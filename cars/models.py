# cars/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Vehicle(models.Model):
    """Model for storing vehicle information"""
    
    # Drivetrain choices
    DRIVETRAIN_CHOICES = [
        ('4WD', '4-Wheel Drive'),
        ('FF', 'Front Engine, Front Wheel Drive'),
        ('FR', 'Front Engine, Rear Wheel Drive'),
        ('MR', 'Mid Engine, Rear Wheel Drive'),
        ('RR', 'Rear Engine, Rear Wheel Drive'),
    ]
    
    # Car type choices
    CAR_TYPE_CHOICES = [
        ('ROAD', 'Road Car'),
        ('GR4', 'Group 4 Racing'),
        ('GR3', 'Group 3 Racing'),
        ('RACE', 'Race Car'),
        ('VGT', 'Vision Gran Turismo'),
        ('FAN', 'Fantasy')
    ]
    
    # Basic information
    name = models.CharField(max_length=100, db_index=True)
    
    # Technical specifications
    drivetrain = models.CharField(
        max_length=3, 
        choices=DRIVETRAIN_CHOICES, 
        default='FR'
    )
    
    car_type = models.CharField(
        max_length=4, 
        choices=CAR_TYPE_CHOICES, 
        default='ROAD'
    )
    
    base_weight = models.IntegerField(
        validators=[MinValueValidator(500), MaxValueValidator(5000)],
        help_text="Base weight in kg",
        default=1400
    )
    
    base_power = models.IntegerField(
        validators=[MinValueValidator(50), MaxValueValidator(2000)],
        help_text="Base power in HP",
        default=300,
        null=True, blank=True
    )
    
    base_pp = models.FloatField(
        validators=[MinValueValidator(100), MaxValueValidator(1000)],
        help_text="Base Performance Points",
        null=True, blank=True
    )
    
    # Lever ratios - critical for suspension calculations
    lever_ratio_front = models.FloatField(
        validators=[MinValueValidator(0.1), MaxValueValidator(2.0)],
        help_text="Front suspension lever ratio",
        default=1.0
    )
    
    lever_ratio_rear = models.FloatField(
        validators=[MinValueValidator(0.1), MaxValueValidator(2.0)],
        help_text="Rear suspension lever ratio",
        default=1.0
    )
    
    # Additional fields
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='vehicles/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_drivetrain_display(self):
        """Get the display name of the drivetrain"""
        return dict(self.DRIVETRAIN_CHOICES).get(self.drivetrain, self.drivetrain)
    
    def get_car_type_display(self):
        """Get the display name of the car type"""
        return dict(self.CAR_TYPE_CHOICES).get(self.car_type, self.car_type)
    
    class Meta:
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['drivetrain']),
            models.Index(fields=['car_type']),
        ]