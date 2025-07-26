# cars/management/commands/import_vehicle_data.py
import pandas as pd
from django.core.management.base import BaseCommand
from cars.models import Vehicle

class Command(BaseCommand):
    help = 'Import vehicle lever ratio data from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        self.stdout.write(self.style.SUCCESS(f'Importing data from {file_path}'))
        
        try:
            # Read the Excel file
            df = pd.read_excel(file_path)
            self.stdout.write(self.style.SUCCESS(f'Found {len(df)} entries in the Excel file'))
            
            # Track counts for reporting
            created = 0
            updated = 0
            errors = 0
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Use the correct column names from your Excel file
                    name = row.get('Vehicle name', None)
                    drivetrain = row.get('Drivetrain', None)
                    car_type = row.get('Car Type', None)
                    front_ratio = row.get('Front Lever Ratio', None)
                    rear_ratio = row.get('Rear Lever Ratio', None)
                    
                    # Skip rows without necessary data
                    if not name or pd.isna(name):
                        self.stdout.write(self.style.WARNING(f'Row {index+2}: Missing vehicle name, skipping'))
                        errors += 1
                        continue
                    
                    # Create or update the vehicle
                    vehicle, was_created = Vehicle.objects.update_or_create(
                        name=name,
                        defaults={
                            'lever_ratio_front': front_ratio,
                            'lever_ratio_rear': rear_ratio,
                            'drivetrain': drivetrain,
                            'car_type': car_type,
                        }
                    )
                    
                    if was_created:
                        created += 1
                        self.stdout.write(f'Created: {name}')
                    else:
                        updated += 1
                        self.stdout.write(f'Updated: {name}')
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error on row {index+2}: {str(e)}'))
                    errors += 1
            
            # Report results
            self.stdout.write(self.style.SUCCESS(
                f'Import completed: {created} vehicles created, {updated} updated, {errors} errors'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Import failed: {str(e)}'))