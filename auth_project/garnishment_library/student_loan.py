from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from User_app.models import *
from User_app.serializers import *
from auth_project.garnishment_library.child_support import ChildSupport
import os
import json 
from django.conf import settings

print("ddddd",ChildSupport().calculate_de(record))

class StudentLoan():
    """ Calculate Student Loan garnishment amount based on the provided data."""

    
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

    def get_single_student_amount(self, record):
        # Calculate disposable earnings
        disposable_earning = ChildSupport().calculate_de(record)
        print(disposable_earning, "111disposable_earning")

        # Calculate percentages earnings
        fifteen_percent_of_earning = disposable_earning *.15
        print("fifteen_percent_of_earning", fifteen_percent_of_earning)
        twentyfive_percent_of_earning =disposable_earning*.25
        print(twentyfive_percent_of_earning, "twentyfive_percent_of_earning")
        fmw =self.get_fmw(record)
        difference_of_de_and_fmw=disposable_earning-fmw
        
        if  fmw>=disposable_earning:
            loan_amt = "Student loan withholding cannot be applied because Disposable Earnings are less than or equal to $217.5, the exempt amount."
        elif fmw<disposable_earning:
            loan_amt=min(fifteen_percent_of_earning,twentyfive_percent_of_earning,difference_of_de_and_fmw)
        elif difference_of_de_and_fmw<0:
            loan_amt = 0
        
        print("loan_amt",loan_amt)

        return ({"student_loan_amt":loan_amt})
    

    def get_multiple_student_amount(self, record):
        fmw = self.get_fmw(record)
        disposable_earning = ChildSupport().calculate_de(record)

        difference_of_de_and_fmw = disposable_earning - fmw
        print("difference_of_de_and_fmw", difference_of_de_and_fmw)

        if fmw >= disposable_earning:
            student_loan_amt1 = "Student loan withholding cannot be applied because Disposable Earnings are less than or equal to $217.5, the exempt amount."
            student_loan_amt2 = "Student loan withholding cannot be applied because Disposable Earnings are less than or equal to $217.5, the exempt amount."
        elif difference_of_de_and_fmw < 0:
            student_loan_amt1 = 0
            student_loan_amt2 = 0
        elif disposable_earning > fmw:
            student_loan_amt1 = .15* disposable_earning
            student_loan_amt2 = .10* disposable_earning

        return ({"student_loan_amt1": student_loan_amt1, "student_loan_amt2": student_loan_amt2})
    
class student_loan_calculate():
        
    def calculate(self, record):

        no_of_student_default_loan=record.get("no_of_student_default_loan")
        if no_of_student_default_loan==1:
            student_loan_amt=StudentLoan().get_single_student_amount(record)

        elif no_of_student_default_loan>1:
            student_loan_amt=StudentLoan().get_multiple_student_amount(record)


        return student_loan_amt



# record={
#           "ee_id": "EE005114",
#           "gross_pay": 1000,
#           "state": "Alabama",
#           "no_of_exemption_for_self": 1,
#           "pay_period": "Weekly",
#           "filing_status": "Single Filing Status",
#           "net_pay": 858.8,
#           "payroll_taxes": [
#             {
#               "federal_income_tax": 80
#             },
#             {
#               "social_security_tax": 49.6
#             },
#             {
#               "medicare_tax": 11.6
#             },
#             {
#               "state_tax": 0
#             },
#             {
#               "local_tax": 0
#             }
#           ],
#           "payroll_deductions": {
#             "medical_insurance": 0
#           },
#           "age": 50,
#           "is_is_blind": True,
#           "is_spouse_is_blind": True,
#           "spouse_age": 39,
#           "support_second_family": "Yes",
#           "no_of_student_default_loan": 1,
#           "arrears_greater_than_12_weeks": "No",
#           "garnishment_data": [
#             {
#               "type": "student default loan",
#               "data": [
#                 {
#                   "case_id": "C13278",
#                   "amount": 128.82,
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




    
record= {
          "ee_id": "EE005114",
          "gross_pay": 1000,
          "state": "Texas",
          "no_of_exemption_for_self": 1,
          "pay_period": "Weekly",
          "filing_status": "single_filing_status",
          "net_pay": 858.8,
          "payroll_taxes": [
            {
              "federal_income_tax": 80
            },
            {
              "social_security_tax": 49.6
            },
            {
              "medicare_tax": 11.6
            },
            {
              "state_tax": 0
            },
            {
              "local_tax": 0
            }
          ],
          "payroll_deductions": {
            "medical_insurance": 0
          },
          "age": 50,
          "is_blind": True,
          "is_spouse_blind": True,
          "spouse_age": 39,
          "support_second_family": "Yes",
          "no_of_student_default_loan": 1,
          "arrears_greater_than_12_weeks": "No",
          "garnishment_data": [
            {
              "type": "student default loan",
              "data": [
                {
                  "case_id": "C13278",
                  "amount": 128.82,
                  "arrear": 0
                }
              ]
            }
          ]
}

# print("get_percentages:",StudentLoan().get_percentage)
print("get_single_student_amount",StudentLoan().get_single_student_amount(record))
print("get_multiple_student_amount",StudentLoan().get_multiple_student_amount(record))
print("student_loan",student_loan_calculate().calculate( record ))
