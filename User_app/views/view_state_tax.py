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
import json
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from rest_framework.generics import DestroyAPIView ,RetrieveUpdateAPIView
from rest_framework import viewsets ,generics
from ..serializers import *
from django.http import HttpResponse
from ..forms import PDFUploadForm
from django.db import transaction
from rest_framework.decorators import api_view
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken ,AccessToken, TokenError
import csv
from rest_framework.views import APIView
from auth_project.garnishment_library import state_tax as st

@csrf_exempt
@api_view(['POST'])
def state_tax(request):
    if request.method == 'POST':
        try:
            data = request.data
            required_fields =     ['gross_income','state','debt','garnishment_fees','employee_name','employer_id','employee_id']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return Response({'error': f'Required fields are missing: {", ".join(missing_fields)}'}, status=status.HTTP_400_BAD_REQUEST)           
            user = State_tax_data.objects.create(**data)

            # Extracting earnings and garnishment fees from gdata
            gross_income = data.get('gross_income',0)
            garnishment_fees = data.get('garnishment_fees',0)           
            # Calculate the various taxes
            union_due=data.get('union_due',0)     
            credit_union=data.get('credit_union',0)
            workers_compensation=data.get('workers_compensation',0)
            medical_insurance=data.get('medical_insurance',0)
            employee_name=data.get('employee_name',0)
            united_way_contribution=data.get('united_way_contribution',0)
            filing_status=data.get('filing_status',0)
            no_of_exception=data.get('no_of_exception',0)
            pay_period=data.get('pay_period',0)
            local_tax_rate=data.get('local_tax',0)
            social_tax_rate = data.get('social_and_security',0)
            medicare_tax_rate = data.get('medicare_tax',0)
            SDI = data.get('SDI',0)
            debt=data.get('debt',0)
            state_tax_rate = data.get('state_tax',0)
            state=data.get('state')

            federal_income_tax_rate=data.get('federal_income_tax',0)

            total_deductions = round(federal_income_tax_rate+social_tax_rate+medicare_tax_rate+SDI+credit_union+local_tax_rate+state_tax_rate+union_due+workers_compensation+medical_insurance,2)

            twenty_five_percentage_grp_state=['arkansas','california','georgia','indiana','montana','new mexico','utah']
            if state.lower() in twenty_five_percentage_grp_state:
                monthly_garnishment_amount= st.cal_x_disposible_income(gross_income,total_deductions)
                duration_of_levies= debt/monthly_garnishment_amount

            net_pay=round(duration_of_levies,2) 
            if net_pay <0:
                net_pay=0
            else:
                net_pay=net_pay                
            print(monthly_garnishment_amount)

            LogEntry.objects.create(
                action='State Tax Calculation data Added',
                details=f'State Tax Calculation data Added successfully with employer ID {user.employer_id} and employee ID {user.employee_id}'
            )
            return Response({'message': 'State Tax Calculations Details Successfully Registered', "status code":status.HTTP_200_OK})

        except Employee_Details.DoesNotExist:
            return Response({"error": "Employee details not found"}, status=status.HTTP_404_NOT_FOUND)
        except Employer_Profile.DoesNotExist:
            return Response({"error": "Employer profile not found", "status code":status.HTTP_404_NOT_FOUND})
        except Exception as e:
           return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return Response({'message': 'Please use POST method', "status_code":status.HTTP_400_BAD_REQUEST}) 
   