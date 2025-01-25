from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from User_app.models import *
from User_app.serializers import *
from auth_project.garnishment_library.child_support import ChildSupport
import os
from auth_project import settings
import json

class StudentLoan():
    """ Calculate Student Loan garnishment amount based on the provided data."""

    def get_percentage(self, percentage,record):
        disposable_earning = record.get("gross_pay") if isinstance(record, dict) else record
        
        if disposable_earning is None and isinstance(record, dict):
            disposable_earning = ChildSupport().calculate_de(record) 

        
        return round(disposable_earning * percentage / 100  ,2) 
    
    def get_fmw(self,record):
      pay_period=record.get("pay_period")
      if pay_period.lower()=="weekly":
        return 7.25*30
      elif pay_period.lower()=="biweekly" or pay_period.lower()=="bi-weekly":
        return 7.25*60
      elif pay_period.lower()=="semimonthly" or pay_period.lower()=="semi-monthly":
        return 7.25*65
      elif pay_period.lower()=="monthly":
        return 7.25*130

  
    
    def  get_single_student_amount(self, record): 
        # Calculate disposable earnings
        disposable_earning = ChildSupport().calculate_de(record)


        # Calculate percentages earnings
        fifteen_percent_of_earning = disposable_earning*.15

        twentyfive_percent_of_earning = self.get_percentage(25,record)

        fmw =self.get_fmw(record)
        difference_of_de_and_fmw=disposable_earning-fmw
        
        if  fmw>=disposable_earning:
            loan_amt = "Student loan withholding cannot be applied because Disposable Earnings are less than or equal to $217.5, the exempt amount."
        elif fmw<disposable_earning:
            loan_amt=min(fifteen_percent_of_earning,twentyfive_percent_of_earning,difference_of_de_and_fmw)
        elif difference_of_de_and_fmw<0:
            loan_amt = 0
        

        return ({"student_loan_amt":round(loan_amt,2)})
    

    def get_multiple_student_amount(self, record):
        fmw = self.get_fmw(record)
        
        disposable_earning = ChildSupport().calculate_de(record)

        difference_of_de_and_fmw=disposable_earning-fmw

        if  fmw>=disposable_earning:
            student_loan_amt1 = "Student loan withholding cannot be applied because Disposable Earnings are less than or equal to $217.5, the exempt amount."
            student_loan_amt2 = "Student loan withholding cannot be applied because Disposable Earnings are less than or equal to $217.5, the exempt amount."
        elif difference_of_de_and_fmw<0:
            student_loan_amt1 = 0
            student_loan_amt2 = 0    
        elif disposable_earning>fmw:
            student_loan_amt1 = self.get_percentage(15,disposable_earning)
            student_loan_amt2 = self.get_percentage(10,disposable_earning)

        return ({"student_loan_amt1":round(student_loan_amt1,2),"student_loan_amt2":round(student_loan_amt2,2)})
    
class student_loan_calculate():
        
    def calculate(self, record):

        no_of_student_default_loan=record.get("no_of_student_default_loan")
        if no_of_student_default_loan==1:
            student_loan_amt=StudentLoan().get_single_student_amount(record)

        elif no_of_student_default_loan>1:
            student_loan_amt=StudentLoan().get_multiple_student_amount(record)


        return student_loan_amt
    
# record= {
#           "ee_id": "EE005791",
#           "gross_pay": 1200,
#           "state": "Pennsylvania",
#           "no_of_exemption_for_self": 2,
#           "pay_period": "Weekly",
#           "filing_status": "married_filing_separate Return",
#           "net_pay": 993.3,
#           "payroll_taxes": [
#             {
#               "federal_income_tax": 95
#             },
#             {
#               "social_security_tax": 58.9
#             },
#             {
#               "medicare_tax": 13.8
#             },
#             {
#               "state_tax": 29
#             },
#             {
#               "local_tax": 10
#             }
#           ],
#           "payroll_deductions": {
#             "medical_insurance": 0
#           },
#           "age": 26,
#           "is_blind": False,
#           "is_spouse_blind": False,
#           "spouse_age": 33,
#           "support_second_family": "Yes",
#           "no_of_student_default_loan": 1,
#           "arrears_greater_than_12_weeks": "Yes",
#           "garnishment_data": [
#             {
#               "type": "student default loan",
#               "data": [
#                 {
#                   "case_id": "C47930",
#                   "amount": 148.995,
#                   "arrear": 0
#                 }
#               ]
#             }
#           ]
#         }

# # print("get_percentages:",StudentLoan().get_percentage)
# print("get_single_student_amount",StudentLoan().get_single_student_amount(record))
# print("get_multiple_student_amount",StudentLoan().get_multiple_student_amount(record))
# print("student_loan",student_loan_calculate().calculate( record ))
