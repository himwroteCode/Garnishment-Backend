from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from User_app.models import *
from User_app.serializers import *
from auth_project.garnishment_library.child_support import ChildSupport



class StudentLoan():
    """ Calculate Student Loan garnishment amount based on the provided data."""
    
    def __init__(self):
        self.fmw = 7.25 * 30

    def get_percentage(self, percentage,record):
        disposable_earning = ChildSupport().calculate_de(record)
        return round(disposable_earning*percentage / 100  ,2) 
    
    
    def  get_single_student_amount(self, record): 
        # Calculate disposable earnings
        disposable_earning = ChildSupport().calculate_de(record)
        garnishment_type=record.get("garnishment_type")


        # Calculate percentages earnings
        fifteen_percent_of_earning = self.get_percentage(15,record)
        twentyfive_percent_of_earning = self.get_percentage(25,record)
        fmw = 7.25 * 30
        difference_of_de_and_fmw=disposable_earning-fmw
        
        if difference_of_de_and_fmw<0:
            student_loan_amt = 0
 
        elif difference_of_de_and_fmw>0 :
            student_loan_amt = difference_of_de_and_fmw
            if len(garnishment_type)==0:
                loan_amt = fifteen_percent_of_earning
            elif len(garnishment_type)>0:
                if garnishment_type == "child_support":
                    difference_amt1 = disposable_earning - twentyfive_percent_of_earning
                    difference_amt2 = disposable_earning - student_loan_amt
                    loan_amt=min(fifteen_percent_of_earning,difference_amt1,difference_amt2)
                elif garnishment_type == "state_tax":
                    state_tax = StateTax().calculate_de(record)
                    difference_amt1 = state_tax - twentyfive_percent_of_earning
                    difference_amt2 = state_tax - student_loan_amt
                    loan_amt=min(fifteen_percent_of_earning,difference_amt1,difference_amt2)
            else:
                pass

        return ({"student_loan_amt":loan_amt})
    

    def get_multiple_student_amount(self, record):
        fmw = 7.25 * 30


        difference_of_de_and_fmw=disposable_earning-fmw
        
        if difference_of_de_and_fmw<0:
            student_loan_amt1 = 0
            student_loan_amt2 = 0

        elif difference_of_de_and_fmw>0 :
            disposable_earning = ChildSupport().calculate_de(record)
            # Calculate student loan amt.
            student_loan_amt1 = self.get_percentage(15,disposable_earning)
            student_loan_amt2 = self.get_percentage(10,disposable_earning)
        

        return ({"student_loan_amt1":student_loan_amt1,"student_loan_amt2":student_loan_amt2})
    
class student_loan_calculate():
        
    def calculate(self, record):
        garnishment_type = record.get("garnishment_type") 

        if len(garnishment_type)==0:
            student_loan_amt=StudentLoan().get_single_student_amount(record)
        elif len(garnishment_type)>0:
            student_loan_amt=StudentLoan().get_multiple_student_amount(record)

        return student_loan_amt
    


print("get_percentages:",StudentLoan().get_percentage)
print("get_single_student_amount",StudentLoan().get_single_student_amount)
print("get_multiple_student_amount",StudentLoan().get_multiple_student_amount)
print("student_loan",student_loan_calculate().calculate)
