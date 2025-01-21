from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from User_app.models import *
from rest_framework.response import Response
from User_app.serializers import *
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from auth_project.garnishment_library import gar_resused_classes as gc
from django.utils.decorators import method_decorator
import os
import json 
from django.conf import settings

class ChildSupport:
    """
    This class contains utility functions to calculate various child support-related amounts.
    """
    PRORATE = "prorate"
    DEVIDEEQUALLY = "divide equally"
    CHILDSUPPORT = "child_support"
    
    def __init__(self):
        self.de_rules_file  = os.path.join(settings.BASE_DIR, 'User_app', 'configuration files/disposable earning rules.json')
        self.ccpa_rules_file = os.path.join(settings.BASE_DIR, 'User_app', 'configuration files/ccpa_rules.json')

    def _load_json_file(self, file_path):
        """
        Helper method to load a JSON file.
        """
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            raise Exception(f"File not found: {file_path}")
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON format in file: {file_path}")

    def calculate_de_rule(self, record):
        """
        Calculate the Disposable Earnings (DE) rule based on the state.
        """
        state = record.get("state")
        if not state:
            raise ValueError("State information is missing in the record.")

        data = self._load_json_file(self.de_rules_file)
        de_rules = data.get("de", [])

        # Find matching state in DE rules
        for rule in de_rules:
            if rule['State'].lower() == state.lower():
                return rule['Disposable Earnings']

        raise ValueError(f"No DE rule found for state: {state}")



    def calculate_md(self, record):
        """
        Calculate mandatory deductions based on state and tax rules.
        """
        gross_pay = record.get("gross_pay")
        state = record.get("state")
        taxes = record.get("taxes")

        if gross_pay is None or state is None or taxes is None:
            raise ValueError("Record must include 'gross_pay', 'state', and 'tax' fields.")

        de_rule = self.calculate_de_rule(record)

        data = self._load_json_file(self.ccpa_rules_file)
        ccpa_rules = data.get("CCPA_Rules", {})

        # Calculate mandatory deductions
        mandatory_deductions = 0
        if de_rule.lower() == "ccpa":
            mandatory_tax_keys = ccpa_rules.get("Mandatory_deductions", [])
            tax_amt = [tax.get(k, 0) for tax in taxes for k in mandatory_tax_keys if k in tax]
            mandatory_deductions = sum(tax_amt)


        return mandatory_deductions
    


    def calculate_de(self,record):
        gross_pay = record.get("gross_pay") 
        mandatory_deductions=self.calculate_md(record)
        # Calculate disposable earnings
        return gross_pay - mandatory_deductions
    
    def get_list_supportAmt(self, record):
        child_support=record.get(self.CHILDSUPPORT)

        return [
            value 
            for Amt_dict in child_support
            for key, value in Amt_dict.items() 
            if key.lower().startswith('amount')
        ]


    def get_list_support_arrearAmt(self, record):
        child_support=record.get(self.CHILDSUPPORT)
        return [
            value
            for Amt_dict in child_support
            for key, value in Amt_dict.items() 
            if key.lower().startswith('arrear')
        ]


    def calculate_wl(self, record):

        # Extract necessary values from the record
        state = record.get("state")
        employee_id = record.get("employee_id")
        supports_2nd_family = record.get("support_second_family")
        arrears_of_more_than_12_weeks = record.get("arrears_of_more_than_12_weeks")

        # Determine the state rules
        state_rules = gc.WLIdentifier().get_state_rules(state)

        calculate_tcsa = len(self.get_list_supportAmt(record))
       
        # Calculate Disposable Earnings (DE)
        de = self.calculate_de(record)

        # Determine if DE > 145 and if there is more than one order
        de_gt_145 = "No" if de <= 145 or state_rules != "Rule_6" else "Yes"

        #Determine arrears_of_more_than_12_weeks
        arrears_of_more_than_12_weeks = "" if state_rules == "Rule_4" else "Yes"

        #Determine order_gt_one
        order_gt_one = "No" if calculate_tcsa > 1 or state_rules != "Rule_4" else "Yes"
        
        # Identify withholding limit using state rules
        wl_limit = gc.WLIdentifier().find_wl_value(de,state, employee_id, supports_2nd_family, arrears_of_more_than_12_weeks, de_gt_145, order_gt_one)

        return wl_limit

    def calculate_twa(self, record):
        
        tcsa = self.get_list_supportAmt(record)
        taa = self.get_list_support_arrearAmt(record)
        return sum(tcsa) + sum(taa)

    def calculate_ade(self, record):
        wl = self.calculate_wl(record)
        de = self.calculate_de(record)
        return wl * de

    def calculate_wa(self, record):
        tcsa = self.get_list_supportAmt(record)
        ade = self.calculate_ade(record)
        return min(ade, sum(tcsa))

    def calculate_each_child_support_amt(self, record):

        tcsa = self.get_list_supportAmt(record)
        return {f"child support amount{i+1}": amount for i, amount in enumerate(tcsa)}

    def calculate_each_arrears_amt(self, record):

        taa = self.get_list_support_arrearAmt(record)
        return {f"arrear amount{i+1}": amount for i, amount in enumerate(taa)}


class SingleChild(ChildSupport):
    def calculate(self, record):
        # Extract values from the record
        child_support_amount = self.get_list_supportAmt(record)[0]
        arrear_amount = self.get_list_support_arrearAmt(record)[0]

        # Calculate Adjusted Disposable Earnings (ADE) using a helper function
        ade = self.calculate_ade(record)
        # Determine the withholding amount and remaining arrear amount
        if ade > child_support_amount:
            # ADE is sufficient to cover the child support amount
            withholding_amount = child_support_amount
            amount_left_for_arrears = ade - child_support_amount

            if amount_left_for_arrears >= arrear_amount:
                # Remaining ADE can cover the arrear amount
                arrear_amount = arrear_amount
            else:
                # Remaining ADE is not sufficient to cover the arrear amount
                arrear_amount = amount_left_for_arrears
        else:
            # ADE is not sufficient to cover the child support amount
            withholding_amount = ade
            arrear_amount = 0

        return withholding_amount, arrear_amount

class MultipleChild(ChildSupport):
    """
    This class calculates the child support amounts and arrear amounts for multiple child support orders.
    """

    def calculate(self, record):

        # Extract necessary values and calculate required metrics
        ade = self.calculate_ade(record)
        tcsa = self.get_list_supportAmt(record)
        taa = self.get_list_support_arrearAmt(record)
        twa = self.calculate_twa(record)
        wa = self.calculate_wa(record)
        state = record.get("state")

        # Determine the allocation method for garnishment based on the state
        allocation_method_for_garnishment = gc.AllocationMethodIdentifiers(state).get_allocation_method()

        if ade > twa:
            # ADE is sufficient to cover the total withholding amount (TWA)
            child_support_amount = self.calculate_each_child_support_amt(record)
            arrear_amount = self.calculate_each_arrears_amt(record)
        else:
            # Apply the allocation method for garnishment
            if allocation_method_for_garnishment == "prorate":
                child_support_amount = {
                    f"child support amount {i+1}": (amount / twa) * ade for i, amount in enumerate(tcsa)
                }
                
                amount_left_for_arrears = wa - sum(tcsa)

                if amount_left_for_arrears <= 0:
                    arrear_amount = {f"arrear amount {i+1}": 0 for i, _ in enumerate(taa)}
                else:
                    if amount_left_for_arrears >=taa:
                        arrear_amount={f"arrear amount{i+1}": (amount/taa)*amount_left_for_arrears for i, amount in enumerate(taa)}
                    else:
                        arrear_amount=self.calculate_each_arrears_amt(record)
            
            elif allocation_method_for_garnishment == "divide equally":
                child_support_amount = {
                    f"child support amount {i+1}": ade / len(tcsa) for i, _ in enumerate(tcsa)
                }
                
                amount_left_for_arrears = ade - sum(tcsa)

                if amount_left_for_arrears <= 0:
                    arrear_amount = {f"arrear amount {i+1}": 0 for i, _ in enumerate(taa)}
                else:
                    if amount_left_for_arrears >=taa:
                        arrear_amount=self.calculate_each_arrears_amt(record)                       
                    else:
                        arrear_amount={f"arrear amount{i+1}": amount/len(taa)+1 for i, amount in enumerate(taa)}
            else:
                raise ValueError("Invalid allocation method for garnishment.")

        return child_support_amount, arrear_amount
    
# record=   {
#       "employee_id": "EMP002",
#       "employer_id" :"EMP001",
#       "gross_pay": 400,
#       "employee_name": "Michael Johnson",
#       "garnishment_fees": 5,
#       "arrears_greater_than_12_weeks": "Yes",
#       "support_second_family": "No",
#       "child_support" : [ {"amount": 150, "arrear": 15}, {"amount": 100, "arrear": 0}],
#       "state": "Texas",
#       "arrears_amount1": 99,
#       "pay_period" : "weekly",
#       "mandatory_deductions":40,
#       "garnishment_type":"child_support"
#     }   

    
# tcsa = ChildSupport().get_list_supportAmt(record)
# result = MultipleChild().calculate(record) if len(tcsa) > 1 else ChildSupport().calculate(record)

