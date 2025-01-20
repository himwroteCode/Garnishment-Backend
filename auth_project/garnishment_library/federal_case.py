from django.http import JsonResponse
from User_app.models import *
from django.contrib.auth import  login as auth_login ,get_user_model
from rest_framework.response import Response
from User_app.serializers import *
from rest_framework.views import APIView
from rest_framework import status
import json
import os
from auth_project import settings
import re


class federal_tax_calculation():
    """ Calculate Federal Tax based on the given filing status and number of exceptions """

    def get_file_data(self, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data

    def get_total_exemption_self(self, request):
      age = request.get('age')
        
      blind = request.get('blind')
      number_of_exemption = 0

      if (age>=65 and blind==True) :
          number_of_exemption=2
      elif (age<65 and blind==True) :
          number_of_exemption=1
      elif(age>=65 and blind==False) :
          number_of_exemption=1
      return number_of_exemption

    def get_total_exemption_dependent(self, request):  

      dependent_age= request.get('dependent_age')
      dependent_disability = request.get('dependent_disability')
      number_of_exemption = 0
      if (dependent_age>=65 and dependent_disability==True) :
          number_of_exemption=2
      elif (dependent_age<65 and dependent_disability==True):
          number_of_exemption=1
      elif(dependent_age>=65 and dependent_disability==False):
          number_of_exemption=1
      return number_of_exemption  

    def get_additional_exempt_for_self(self, record):
        pay_period=record.get('pay_period').lower()
        filing_status=record.get('filing_status')
        no_of_exemption=self.get_total_exemption_self(record)

        file_path=os.path.join(settings.BASE_DIR, 'User_app', 'configuration files/additional_exempt_amount.json')
        age=record.get('age')
        blind=record.get('blind')
        result = 0
        with open(file_path, 'r') as file:
            data = json.load(file)
    
        
        data = data["additional_exempt_amt"]
        no_of_exemption_list=[]
        for item in data:
          if item.get("no_of_exemption") == no_of_exemption:
            no_of_exemption_list.append(item)
        single_filing_status_list=[]
        head_of_household_list=[]
        any_other_filing_status=[]
        for item in no_of_exemption_list:
          if "single_filing_status" == item.get("filing_status"):
            single_filing_status_list.append(item)
          elif "head_of_household" == item.get("filing_status"):
             head_of_household_list.append(item)
          else:
              any_other_filing_status.append(item)
    
        if filing_status == "single_filing_status":
          result = single_filing_status_list[0].get(pay_period)
          
        elif filing_status == "head_of_household":
          result = head_of_household_list[0].get(pay_period)
    
        else:
          result = any_other_filing_status[0].get(pay_period)
        return result
         


    def get_additional_exempt_for_dependent(self, record):
        pay_period=record.get('pay_period').lower()
        filing_status=record.get('filing_status')
        no_of_exemption=self.get_total_exemption_self(record)
        file_path=os.path.join(settings.BASE_DIR, 'User_app', 'configuration files/additional_exempt_amount.json')
        dependent_age=record.get('dependent_age')
        dependent_disability=record.get('dependent_disability')
        result = 0
        with open(file_path, 'r') as file:
            data = json.load(file)
    
        
        data = data["additional_exempt_amt"]
        no_of_exemption_list=[]
        for item in data:
          if item.get("no_of_exemption") ==no_of_exemption:
            no_of_exemption_list.append(item)
        single_filing_status_list=[]
        head_of_household_list=[]
        any_other_filing_status=[]
        for item in no_of_exemption_list:
          if "single_filing_status" == item.get("filing_status"):
            single_filing_status_list.append(item)
          elif "head_of_household" == item.get("filing_status"):
             head_of_household_list.append(item)
          else:
              any_other_filing_status.append(item)
    
        if filing_status == "single_filing_status":
          result = single_filing_status_list[0].get(pay_period)
          
        elif filing_status == "head_of_household":
          result = head_of_household_list[0].get(pay_period)
    
        else:
          result = any_other_filing_status[0].get(pay_period)
        return result
    

    def get_standard_exempt_amt(self, record):

        filing_status=record.get('filing_status')
        no_of_exception_for_Self=record.get('no_of_exception_for_Self')
        pay_period=record.get('pay_period')

        # Check if the number of exceptions is greater than 5
        exempt= 6 if no_of_exception_for_Self >5 else no_of_exception_for_Self

        file_path=os.path.join(settings.BASE_DIR, 'User_app', f'configuration files/{filing_status}.json')
        data = self.get_file_data(file_path)
        status_data = data.get(filing_status, [])


        # Accessing federal tax data
        if no_of_exception_for_Self <=5:
            semimonthly_data = next((item for item in status_data if item["Pay Period"].lower() == pay_period.lower()), None)
            exempt_amount = semimonthly_data.get(str(exempt))
        elif no_of_exception_for_Self >5:
            semimonthly_data = next((item for item in status_data if item["Pay Period"].lower() == pay_period.lower()), None)
            # print("semimonthly_data",semimonthly_data)
            exemp_amt = semimonthly_data.get(str(exempt))
            # print("exemp_amt",exemp_amt)
            exempt_amount  = re.findall(r'\d+\.?\d*',exemp_amt)
            exempt1=float(exempt_amount[0])
            exempt2=float(exempt_amount[1])
            exempt_amount=round((exempt1+(exempt2*no_of_exception_for_Self)),2)
            # print("Single exempt_amount",exempt_amount)
        return exempt_amount


class federal_tax(federal_tax_calculation):

    def calculate(self, record):

        net_pay = record.get('net_pay')

        exempt_amount_self=self.get_additional_exempt_for_self(record)
        # print("exempt_amount_self",exempt_amount_self)

        exempt_amount_dependent=self.get_additional_exempt_for_dependent(record)
        # print("dependent_exempt_amt",exempt_amount_dependent)


       #Calculate Standard exempt
        standard_exempt_amt=self.get_standard_exempt_amt(record)
        # print("standaerd_exmpt_amt",standard_exempt_amt)
        

        # Calculate the amount to deduct
        total_exempt_amt=standard_exempt_amt+exempt_amount_self+exempt_amount_dependent
        # print("total_exempt_amt",total_exempt_amt)

        amount_deduct = round((net_pay-total_exempt_amt), 2)
        # print("amount_deduct",amount_deduct)

        amount_deduct = amount_deduct if amount_deduct > 0 else 0
        return (amount_deduct)

        # except Exception as e:
        #     return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})