# cars/management/commands/analyze_excel_file.py
import pandas as pd
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Analyze Excel file structure'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        self.stdout.write(self.style.SUCCESS(f'Analyzing file: {file_path}'))
        
        try:
            # Read the Excel file
            df = pd.read_excel(file_path)
            
            # Print the shape of the dataframe
            self.stdout.write(self.style.SUCCESS(f'DataFrame shape: {df.shape} (rows, columns)'))
            
            # Print the column names
            self.stdout.write(self.style.SUCCESS('Column names:'))
            for i, col in enumerate(df.columns):
                self.stdout.write(f'  {i}: {col}')
            
            # Print first few rows to understand structure
            self.stdout.write(self.style.SUCCESS('\nFirst 5 rows:'))
            for i, row in df.head(5).iterrows():
                self.stdout.write(f'Row {i+1}:')
                for col in df.columns:
                    self.stdout.write(f'  {col}: {row[col]}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Analysis failed: {str(e)}'))