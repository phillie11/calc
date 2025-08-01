# Generated by Django 5.1.7 on 2025-04-15 07:07

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vehicle', models.CharField(db_index=True, max_length=100)),
                ('drivetrain', models.CharField(choices=[('4WD', '4-Wheel Drive'), ('FF', 'Front Engine, Front Wheel Drive'), ('FR', 'Front Engine, Rear Wheel Drive'), ('MR', 'Mid Engine, Rear Wheel Drive'), ('RR', 'Rear Engine, Rear Wheel Drive')], default='FR', max_length=3)),
                ('car_type', models.CharField(choices=[('ROAD', 'Road Car'), ('GR4', 'Group 4 Racing'), ('GR3', 'Group 3 Racing'), ('RACE', 'Race Car'), ('VGT', 'Vision Gran Turismo'), ('FAN', 'Fantasy')], default='ROAD', max_length=4)),
                ('base_weight', models.IntegerField(default=1400, help_text='Base weight in kg', validators=[django.core.validators.MinValueValidator(500), django.core.validators.MaxValueValidator(5000)])),
                ('base_power', models.IntegerField(blank=True, default=300, help_text='Base power in HP', null=True, validators=[django.core.validators.MinValueValidator(50), django.core.validators.MaxValueValidator(2000)])),
                ('base_pp', models.FloatField(blank=True, help_text='Base Performance Points', null=True, validators=[django.core.validators.MinValueValidator(100), django.core.validators.MaxValueValidator(1000)])),
                ('lever_ratio_front', models.FloatField(default=1.0, help_text='Front suspension lever ratio', validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(2.0)])),
                ('lever_ratio_rear', models.FloatField(default=1.0, help_text='Rear suspension lever ratio', validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(2.0)])),
                ('description', models.TextField(blank=True, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='vehicles/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Vehicle',
                'verbose_name_plural': 'Vehicles',
                'ordering': ['vehicle'],
                'indexes': [models.Index(fields=['vehicle'], name='cars_vehicl_vehicle_0eabf9_idx'), models.Index(fields=['drivetrain'], name='cars_vehicl_drivetr_128e59_idx'), models.Index(fields=['car_type'], name='cars_vehicl_car_typ_40948e_idx')],
            },
        ),
    ]
