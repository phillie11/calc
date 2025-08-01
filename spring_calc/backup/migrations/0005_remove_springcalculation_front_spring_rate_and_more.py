# Generated by Django 5.1.7 on 2025-03-16 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spring_calc', '0004_alter_springcalculation_vehicle_weight'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='springcalculation',
            name='front_spring_rate',
        ),
        migrations.RemoveField(
            model_name='springcalculation',
            name='rear_spring_rate',
        ),
        migrations.AddField(
            model_name='springcalculation',
            name='base_camber',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='springcalculation',
            name='front_camber',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='springcalculation',
            name='front_roll_bar',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='springcalculation',
            name='front_toe',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='springcalculation',
            name='high_speed_stability',
            field=models.FloatField(default=1.0),
        ),
        migrations.AddField(
            model_name='springcalculation',
            name='rear_camber',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='springcalculation',
            name='rear_roll_bar',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='springcalculation',
            name='rear_toe',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='springcalculation',
            name='roll_bar_multiplier',
            field=models.FloatField(default=1.0),
        ),
        migrations.AddField(
            model_name='springcalculation',
            name='rotational_g_values',
            field=models.CharField(default='0.5,0.7,0.9', max_length=100),
        ),
        migrations.AddField(
            model_name='springcalculation',
            name='tire_wear_multiplier',
            field=models.IntegerField(default=25),
        ),
        migrations.AddField(
            model_name='springcalculation',
            name='track_type',
            field=models.CharField(default='Fast', max_length=20),
        ),
    ]
