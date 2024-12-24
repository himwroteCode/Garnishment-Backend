import json
import os
from django.contrib.staticfiles import finders
from django.conf import settings 

class DisposableIncomeCalculator:
    def __init__(self, x=0.25):
        self.x = x

    def calculate(self, gross_income):
        disposable_earnings = round(gross_income, 2)
        monthly_garnishment_amount = disposable_earnings * self.x
        return monthly_garnishment_amount

class StateMethodIdentifiers:
    def __init__(self, state):
        self.state = state.lower()  

    def get_allocation_method(self):

        file_path = os.path.join(settings.BASE_DIR, 'User_app', 'child_support_provisions.json')

        # Reading the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)
        # Accessing child support data
        child_support_data = data.get("States", [])
        
        # Searching for the matching state
        for record in child_support_data:
            if record['State'].lower() == self.state.lower():
                return record['AllocationMethod']
        
        # # If no matching record is found
        # return f"No allocation method found for the state: {self.state.capitalize()}."

