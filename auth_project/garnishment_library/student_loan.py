from rest_framework import status
from django.contrib import messages
from auth_project.config import ccpa_limit
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from User_app.models import *
from django.contrib.auth import authenticate, login as auth_login ,get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from User_app.serializers import *
from rest_framework.decorators import api_view
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
import csv
from rest_framework.views import APIView
from auth_project.garnishment_library.child_support import ChildSupport



class studentloan():
    """ Calculate Student Loan garnishment amount based on the provided data."""
    
    def __init__(self):
        self.fmw = 7.25 * 30

    def get_de(self, record):
        gross_pay = record.get("gross_pay")

        de=ChildSupport().calculate_de(record)

        return(gross_pay-de)

    def get_percentage(self, percentage,allowable_disposable_earning):
        return round(allowable_disposable_earning*percentage / 100  ,2) 

    def get_single_student_amount(self, record):  
        # Calculate disposable earnings
        get_de = self.get_de(record)

        # Calculate percentages earnings
        fifteen_percent_of_earning = self.get_percentage(15,get_de)
        twentyfive_percent_of_earning = self.get_percentage(25,get_de)

        #Calculate student loan amount
        student_loan_amt= self.get_de(record)-self.fmw

        # Calculate garnishment amount
        student_loan_amt=max(0,student_loan_amt)
    
    def get_multiple_student_amount(self, record):
        # Calculate disposable earnings
        get_de = self.get_de(record)

        # Calculate percentages earnings
        fifteen_percent_of_earning = self.get_percentage(15,get_de)
        twentyfive_percent_of_earning = self.get_percentage(25,get_de)

        #Calculate student loan amount
        student_loan_amt= self.get_de(record)-self.fmw

        # Calculate garnishment amount
        student_loan_amt=max(0,student_loan_amt)
   
        
    def calculate(self, record):
        garnishment_fees = record.get("garnishment_fees", 0)
        disposable_income = record.get("disposable_income")  
        garnishment_type = record.get("garnishment_type")  
        
        # Save the record to the `single_student_loan_data` table
        # user = single_student_loan_data.objects.create(**record)  
        
        if garnishment_type == "single_student_loan":
            # Calculate garnishment amount
            garnishment_amount = self.get_percentage(15,disposable_income)
        elif garnishment_type == "multiple_student_loan":
            # Calculate garnishment amount
            allowable_disposable_earning = round(disposable_income - garnishment_fees, 2)
            twentyfive_percent_of_earning = round(allowable_disposable_earning * 0.25, 2)
            

            StudentLoanAmount1 = self.get_percentage(15,disposable_income)
            StudentLoanAmount2 = self.get_percentage(10,disposable_income)
            StudentLoanAmount3 = self.get_percentage(0,disposable_income)

            net_pay = max(0, round(disposable_income - garnishment_amount, 2))
            garnishment_amount = self.get_percentage(25,disposable_income)

        return garnishment_amount
    


