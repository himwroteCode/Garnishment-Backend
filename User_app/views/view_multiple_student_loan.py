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


class get_multiple_student_loan_case_data(APIView):
    def get(self, request, employer_id,employee_id):
        employees = multiple_student_loan_data.objects.filter(employer_id=employer_id,employee_id=employee_id).order_by('-timestamp')[0:1]
        if employees.exists():
            try:
                serializer = multiple_student_loan_data_Serializer(employees,many=True)
                response_data = {
                    'success': True,
                    'message': 'Data retrieved successfully',
                    'status code': status.HTTP_200_OK,
                    'data': serializer.data
                }
                return JsonResponse(response_data)
            except federal_loan_case_data.DoesNotExist:
                return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
        else:
            return JsonResponse({'message': 'Employee ID not found', 'status code': status.HTTP_404_NOT_FOUND})


class get_multiple_student_loan_data_and_result(APIView):
    def get(self, request, employer_id,employee_id):
        employees = multiple_student_loan_data_and_result.objects.filter(employer_id=employer_id,employee_id=employee_id).order_by('-timestamp')[0:1]
        if employees.exists():
            try:
                serializer = multiple_student_loan_data_and_result_Serializer(employees,many=True)
                response_data = {
                    'success': True,
                    'message': 'Data retrieved successfully',
                    'status code': status.HTTP_200_OK,
                    'data': serializer.data
                }
                return JsonResponse(response_data)
            except multiple_student_loan_data_and_result.DoesNotExist:
                return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
        else:
            return JsonResponse({'message': 'Employee ID not found', 'status code': status.HTTP_404_NOT_FOUND})



class get_multiple_student_loan_result(APIView):
    def get(self, request, employee_id, employer_id): 
        employees = multiple_student_loan_result.objects.filter(employee_id=employee_id, employer_id=employer_id)
        if employees.exists():
            try:
                employee= employees.order_by('-timestamp')[:1]
                serializer = MultipleStudentLoanSerializer(employee, many=True)
                response_data = {
                    'success': True,
                    'message': 'Data retrieved successfully',
                    'status code': status.HTTP_200_OK,
                    'data': serializer.data
                }
                return JsonResponse(response_data)
            except Employer_Profile.DoesNotExist:
                return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
        else:
            return JsonResponse({'message': 'Employer ID not found', 'status code': status.HTTP_404_NOT_FOUND})

class get_all_multiple_student_loan_result(APIView):
    def get(self, request, employer_id):
        employees = multiple_student_loan_result.objects.filter(employer_id=employer_id,)
        if employees.exists():
            try:
                serializer = MultipleStudentLoanSerializer(employees,many=True)
                response_data = {
                    'success': True,
                    'message': 'Multiple Student Loan Data retrieved successfully',
                    'status code': status.HTTP_200_OK,
                    'data': serializer.data
                }
                return JsonResponse(response_data)
            except multiple_student_loan_result.DoesNotExist:
                return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
        else:
            return JsonResponse({'message': 'Employee ID not found', 'status code': status.HTTP_404_NOT_FOUND})


@csrf_exempt
@api_view(['POST'])
def MultipleStudentLoanCalculationData(request):
    if request.method == 'POST':
        try:
            data = request.data
            required_fields = ['employee_name', 'garnishment_fees', 'earnings','order_id','federal_income_tax','social_and_security_tax','medicare_tax','state_tax','SDI_tax']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return Response({'error': f'Required fields are missing: {", ".join(missing_fields)}'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = multiple_student_loan_data.objects.create(**data)
                        
            # # Retrieve the employee, tax, and employer records
            # employee = Employee_Details.objects.get(employee_id=data['employee_id'], employer_id=data['employer_id'])
            # tax = Tax_details.objects.get(employer_id=data['employer_id'])
            # employer = Employer_Profile.objects.get(employer_id=data['employer_id'])
            # gdata = multiple_student_loan_data.objects.filter(employer_id=data['employer_id'], employee_id=data['employee_id']).order_by('-timestamp').first()

            # Extracting earnings and garnishment fees from gdata
            earnings = data['earnings']
            garnishment_fees = data['garnishment_fees']
            
            # Calculate the various taxes
            federal_income_tax_rate = data.get('federal_income_tax',0) 
            social_tax_rate = data.get('social_and_security_tax',0)
            medicare_tax_rate = data.get('medicare_tax',0)
            state_tax_rate = data.get('state_tax',0) 

            SDI_tax=data.get('SDI_tax',0) 
            total_tax = round(federal_income_tax_rate + social_tax_rate + medicare_tax_rate + state_tax_rate+SDI_tax,2)
            disposable_earnings = round(earnings - total_tax, 2)
            allowable_disposable_earning=round(disposable_earnings-garnishment_fees,2)
            twentyfive_percent_of_earning= round(allowable_disposable_earning*.25,2)
            fmw=7.25*30
            
            if allowable_disposable_earning<fmw:
                garnishment_amount=0
            else:
                garnishment_amount=twentyfive_percent_of_earning
            difference=round(disposable_earnings-fmw,2)
            if difference>garnishment_amount:
                garnishment_amount=garnishment_amount
            else:
                garnishment_amount=difference
            if garnishment_amount<0:
                garnishment_amount=0
            else:
                garnishment_amount=garnishment_amount
            print("garnishment_amount:",garnishment_amount)
            StudentLoanAmount1=round(allowable_disposable_earning*.15,2)
            StudentLoanAmount2=round(allowable_disposable_earning*.10,2)
            StudentLoanAmount3=round(allowable_disposable_earning*0,2)

            net_pay = round(disposable_earnings-garnishment_amount,2)
            
            # Create Calculation_data_results object
            multiple_student_loan_data_and_result.objects.create(
                employee_id=data['employee_id'],
                employer_id=data['employer_id'],
                federal_income_tax=federal_income_tax_rate,
                social_and_security_tax=social_tax_rate,
                medicare_tax=medicare_tax_rate,
                state_tax=state_tax_rate,
                SDI_tax=SDI_tax,
                earnings=earnings,
                garnishment_fees=garnishment_fees,
                total_tax=total_tax,
                disposable_earnings=disposable_earnings,
                allowable_disposable_earning=allowable_disposable_earning,
                twentyfive_percent_of_earning=twentyfive_percent_of_earning,
                fmw=fmw,
                garnishment_amount=garnishment_amount,
                studentloan1=StudentLoanAmount1,
                studentloan2=StudentLoanAmount2,
                studentloan3=StudentLoanAmount3,
                net_pay=net_pay
            )

            # Create CalculationResult object
            multiple_student_loan_result.objects.create(
                employee_id=data['employee_id'],
                employer_id=data['employer_id'],
                garnishment_amount=garnishment_amount,
                studentloan1=StudentLoanAmount1,
                studentloan2=StudentLoanAmount2,
                studentloan3=StudentLoanAmount3,
                net_pay=net_pay            
            )
            LogEntry.objects.create(
                action='Multiple Student Loan Calculation data Added',
                details=f'Multiple Student Loan Calculation data Added successfully with employer ID {user.employer_id} and employee ID {user.employee_id}'
            )
            return Response({'message': 'Multiple Student Loan Calculations Details Successfully Registered', "status code":status.HTTP_200_OK})
        except Employee_Details.DoesNotExist:
            return Response({"error": "Employee details not found"}, status=status.HTTP_404_NOT_FOUND)
        # except Tax_details.DoesNotExist:
        #     return Response({"error": "Tax details not found", "status code":status.HTTP_404_NOT_FOUND})
        except Employer_Profile.DoesNotExist:
            return Response({"error": "Employer profile not found", "status code":status.HTTP_404_NOT_FOUND})
        except Exception as e:
            return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return Response({'message': 'Please use POST method', "status_code":status.HTTP_400_BAD_REQUEST})

