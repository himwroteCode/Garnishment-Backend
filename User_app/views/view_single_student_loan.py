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



@csrf_exempt
@api_view(['POST'])
def StudentLoanCalculationData(request):
    if request.method == 'POST':
        try:
            data = request.data
            required_fields = ['employee_name', 'garnishment_fees', 'earnings','order_id']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return Response({'error': f'Required fields are missing: {", ".join(missing_fields)}'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = single_student_loan_data.objects.create(**data)

            # Retrieve the employee, tax, and employer records
            employee = Employee_Details.objects.get(employee_id=data['employee_id'], employer_id=data['employer_id'])
            tax = Tax_details.objects.get(employer_id=data['employer_id'])
            employer = Employer_Profile.objects.get(employer_id=data['employer_id'])
            gdata = single_student_loan_data.objects.filter(employer_id=data['employer_id'], employee_id=data['employee_id']).order_by('-timestamp').first()

            # Extracting earnings and garnishment fees from gdata
            earnings = data.get('earnings',0)
            garnishment_fees = data.get('garnishment_fees',0)
           
            # Calculate the various taxes
            federal_income_tax_rate = data.get('federal_income',0) 
            social_tax_rate = data.get('social_and_security_tax',0)
            medicare_tax_rate = data.get('medicare_tax',0)
            state_tax_rate = data.get('state_tax',0) 

            SDI_tax=data.get('SDI_tax',0) 
            # print(federal_income_tax_rate,social_tax_rate,medicare_tax_rate,state_tax_rate,)
            total_tax = round((federal_income_tax_rate + social_tax_rate + medicare_tax_rate + state_tax_rate+SDI_tax),2)
            # print("total_tax :" ,total_tax)
            disposable_earnings = round(earnings - total_tax, 2)
            # print("disposable_earnings :" ,disposable_earnings)
            allowable_disposable_earning=round(disposable_earnings-garnishment_fees,2)
            # print("allowable_disposable_earning :" ,allowable_disposable_earning)
            fifteen_percent_of_eraning= round(allowable_disposable_earning*.15,2)
            # print("fifteen_percent_of_eraning :" ,fifteen_percent_of_eraning)
            fmw=round(7.25*30,2)
            difference=round(disposable_earnings-fmw,2)
            if allowable_disposable_earning<fmw:
                garnishment_amount=0
            else:
                garnishment_amount=fifteen_percent_of_eraning
            if difference>garnishment_amount:
                garnishment_amount=garnishment_amount
            else:
                garnishment_amount=difference
            if garnishment_amount<0:
                garnishment_amount=0
            else:
                garnishment_amount=garnishment_amount
            print("garnishment_amount :" ,garnishment_amount)
            net_pay=round(disposable_earnings-garnishment_amount,2)
            # print("net_pay :" ,net_pay)
            
            # # Create Calculation_data_results object
            # single_student_loan_data_and_result.objects.create(
            #     employee_id=data
            #     employer_id=data.get('employer_id',0)
            #     federal_income_tax=data.get('federal_income_tax',0)
            #     social_and_security_tax=data.get('social_tax',0)
            #     medicare_tax=data.get('medicare_tax',0)
            #     state_tax=data.get('state_tax',0)
            #     SDI_tax=data.get('SDI_tax',0)
            #     earnings=data.get('earnings'),
            #     garnishment_fees=data.get('garnishment_fees',0)
            #     total_tax=data.get('total_tax',0)
            #     disposable_earnings=data.get('disposable_earnings',0)
            #     allowable_disposable_earning=data.get('allowable_disposable_earning',0)
            #     fifteen_percent_of_eraning=datafifteen_percent_of_eraning,
            #     fmw=fmw,
            #     garnishment_amount=garnishment_amount,
            #     difference=difference,
            #     net_pay=net_pay
            # )

            # Create CalculationResult object
            single_student_loan_result.objects.create(
                employee_id=data['employee_id'],
                employer_id=data['employer_id'],
                net_pay=net_pay,
                garnishment_amount=garnishment_amount
            )

            LogEntry.objects.create(
                action='Single Student Loan Calculation data Added',
                details=f'Single Student Loan Calculation data Added successfully with employer ID {user.employer_id} and employee ID {user.employee_id}'
            )

            return Response({'message': 'Single Student Loan Calculation Details Registered Successfully', "status code":status.HTTP_200_OK})

        except Employee_Details.DoesNotExist:
            return Response({"error": "Employee details not found"}, status=status.HTTP_404_NOT_FOUND)
        except Tax_details.DoesNotExist:
            return Response({"error": "Tax details not found", "status code":status.HTTP_404_NOT_FOUND})
        except Employer_Profile.DoesNotExist:
            return Response({"error": "Employer profile not found", "status code":status.HTTP_404_NOT_FOUND})
        except Exception as e:
            return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return Response({'message': 'Please use POST method', "status_code":status.HTTP_400_BAD_REQUEST})


class get_Single_Student_loan_result(APIView):
    def get(request,self, employee_id, employer_id): 
        employees = single_student_loan_result.objects.filter(employee_id=employee_id, employer_id=employer_id)
        if employees.exists():
            try:
                employee= employees.order_by('-timestamp')[:1]             
                serializer = SingleStudentLoanSerializer(employee,many=True)

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

class get_single_student_loan_data_and_result(APIView):
    def get(self, request, employer_id,employee_id):
        employees = single_student_loan_data_and_result.objects.filter(employer_id=employer_id,employee_id=employee_id).order_by('-timestamp')[0:1]
        if employees.exists():
            try:
                serializer = single_student_loan_data_and_result_Serializer(employees,many=True)
                response_data = {
                    'success': True,
                    'message': 'Data retrieved successfully',
                    'status code': status.HTTP_200_OK,
                    'data': serializer.data
                }
                return JsonResponse(response_data)
            except single_student_loan_data_and_result.DoesNotExist:
                return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
            except Exception as e:
                return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
        else:
            return JsonResponse({'message': 'Employee ID not found', 'status code': status.HTTP_404_NOT_FOUND})

class get_single_student_loan_case_data(APIView):
    def get(self, request, employer_id,employee_id):
        employees = single_student_loan_data.objects.filter(employer_id=employer_id,employee_id=employee_id).order_by('-timestamp')[0:1]
        if employees.exists():
            try:
                serializer = single_student_loan_data_Serializer(employees,many=True)
                response_data = {
                    'success': True,
                    'message': 'Data retrieved successfully',
                    'status code': status.HTTP_200_OK,
                    'data': serializer.data
                }
                return JsonResponse(response_data)
            except federal_loan_case_data.DoesNotExist:
                return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
            except Exception as e:
                return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
        else:
            return JsonResponse({'message': 'Employee ID not found', 'status code': status.HTTP_404_NOT_FOUND})

class get_all_Single_Student_loan_result(APIView):
    def get(self, request, employer_id):
        employees = single_student_loan_result.objects.filter(employer_id=employer_id,)
        if employees.exists():
            try:
                serializer = SingleStudentLoanSerializer(employees,many=True)
                response_data = {
                    'success': True,
                    'message': 'Single Student Loan Data retrieved successfully',
                    'status code': status.HTTP_200_OK,
                    'data': serializer.data
                }
                return JsonResponse(response_data)
            except single_student_loan_result.DoesNotExist:
                return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
            except Exception as e:
                return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
        else:
            return JsonResponse({'message': 'Employee ID not found', 'status code': status.HTTP_404_NOT_FOUND})

