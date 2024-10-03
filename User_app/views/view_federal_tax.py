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
def federal_case(request):
    if request.method == 'POST':
        try:
            data = request.data
            required_fields = [ 'garnishment_fees','employee_name','no_of_exception','filing_status','pay_period', 'earnings']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return Response({'error': f'Required fields are missing: {", ".join(missing_fields)}'}, status=status.HTTP_400_BAD_REQUEST)           
            user = federal_loan_case_data.objects.create(**data)

            # # Retrieve the employee, tax, and employer records
            # employee = Employee_Details.objects.get(employee_id=data['employee_id'], employer_id=data['employer_id'])
            # tax = Tax_details.objects.get(employer_id=data['employer_id'])
            # employer = Employer_Profile.objects.get(employer_id=data['employer_id'])

            # Extracting earnings and garnishment fees from gdata
            earnings = data.get('earnings',0)
            garnishment_fees = data.get('garnishment_fees',0)
            
            # Calculate the various taxes
            # mexico_tax=data.get('mexico_tax',0)
            workers_compensation=data.get('workers_compensation',0)
            medical_insurance=data.get('medical_insurance',0)
            contribution=data.get('contribution',0)
            united_way_contribution=data.get('united_way_contribution',0)
            filing_status=data.get('filing_status',0)
            no_of_exception=data.get('no_of_exception',0)
            pay_period=data.get('pay_period',0)
            local_tax_rate=data.get('local_tax',0)
            social_tax_rate = data.get('social_and_security',0)
            medicare_tax_rate = data.get('medicare_tax',0)
            state_tax_rate = data.get('state_tax',0)
            federal_income_tax_rate=data.get('federal_income_tax',0)
            total_tax = round(federal_income_tax_rate+social_tax_rate+medicare_tax_rate+local_tax_rate+state_tax_rate+workers_compensation+medical_insurance+contribution+united_way_contribution,2)
            # print("total_tax:",total_tax)
            
            disposable_earnings = round(earnings - total_tax, 2)
            
            if filing_status.lower() == "single filing status":
                queryset = single_filing_status.objects.filter(pay_period=pay_period)
                obj = queryset.first()
                if obj is None:
                    return JsonResponse({"error": "No matching records found for the given pay period"}, status=404)
                fields = single_filing_status._meta.get_fields()
                if no_of_exception >=7:
                    total_exemption=7
                    column_name = next((field.name for field in fields if field.name.endswith(str(total_exemption))), None)
                    if not column_name:
                        return JsonResponse({"error": "Column not found"}, status=404)
                    exempt_amount = getattr(obj, column_name)
                    exempt_amount1=exempt_amount.split(" ")
                    exempt1=float(exempt_amount1[0])
                    exempt2=float(exempt_amount1[2])
                    exempt_amount=round((exempt1+(exempt2*no_of_exception)),2)
                else:
                    column_name = next((field.name for field in fields if field.name.endswith(str(no_of_exception))), None)
                    if not column_name:
                        return JsonResponse({"error": "Column not found"}, status=404)
                    exempt_amount = getattr(obj, column_name)

            elif filing_status.lower() == "married filing sepearte return":
                queryset = married_filing_sepearte_return.objects.filter(pay_period=pay_period)
                obj = queryset.first()

                if obj is None:
                    return JsonResponse({"error": "No matching records found for the given pay period"}, status=404)
                fields = single_filing_status._meta.get_fields()
                if no_of_exception >=7:
                    total_exemption=7
                    column_name = next((field.name for field in fields if field.name.endswith(str(total_exemption))), None)
                    if not column_name:
                        return JsonResponse({"error": "Column not found"}, status=404)
                    exempt_amount = getattr(obj, column_name)
                    exempt_amount1=exempt_amount.split(" ")
                    exempt1=float(exempt_amount1[0])
                    exempt2=float(exempt_amount1[2])
                    exempt_amount=round((exempt1+(exempt2*no_of_exception)),2)
                else:
                    column_name = next((field.name for field in fields if field.name.endswith(str(no_of_exception))), None)
                    if not column_name:
                        return JsonResponse({"error": "Column not found"}, status=404)
                    exempt_amount = getattr(obj, column_name)
 
            elif filing_status.lower() == "married filing joint return":
                queryset = married_filing_joint_return.objects.filter(pay_period=pay_period)
                obj = queryset.first()
                if obj is None:
                    return JsonResponse({"error": "No matching records found for the given pay period"}, status=404)
                fields = single_filing_status._meta.get_fields()
                column_name = next((field.name for field in fields if field.name.endswith(str(no_of_exception))), None)
                if no_of_exception >=7:
                    total_exemption=7
                    column_name = next((field.name for field in fields if field.name.endswith(str(total_exemption))), None)
                    if not column_name:
                        return JsonResponse({"error": "Column not found"}, status=404)
                    exempt_amount = getattr(obj, column_name)
                    exempt_amount1=exempt_amount.split(" ")
                    exempt1=float(exempt_amount1[0])
                    exempt2=float(exempt_amount1[2])
                    exempt_amount=round((exempt1+(exempt2*no_of_exception)),2)
                else:
                    column_name = next((field.name for field in fields if field.name.endswith(str(no_of_exception))), None)
                    if not column_name:
                        return JsonResponse({"error": "Column not found"}, status=404)
                    exempt_amount = getattr(obj, column_name)
            
            elif filing_status.lower() == "head of household":
                fields = head_of_household._meta.get_fields()
                queryset = head_of_household.objects.filter(pay_period=pay_period)
                obj = queryset.first()
                if obj is None:
                    return JsonResponse({"error": "No matching records found for the given pay period"}, status=404)
                fields = head_of_household._meta.get_fields()
                column_name = next((field.name for field in fields if field.name.endswith(str(no_of_exception))), None)
                if no_of_exception >=7:
                    total_exemption=7
                    column_name = next((field.name for field in fields if field.name.endswith(str(total_exemption))), None)
                    if not column_name:
                        return JsonResponse({"error": "Column not found"}, status=404)
                    exempt_amount = getattr(obj, column_name)
                    exempt_amount1=exempt_amount.split(" ")
                    exempt1=float(exempt_amount1[0])
                    exempt2=float(exempt_amount1[2])
                    exempt_amount=round((exempt1+(exempt2*no_of_exception)),2)
                else:
                    column_name = next((field.name for field in fields if field.name.endswith(str(no_of_exception))), None)
                    if not column_name:
                        return JsonResponse({"error": "Column not found"}, status=404)
                    exempt_amount = getattr(obj, column_name)
            else:
                return JsonResponse({"error": "Invalid filing status"}, status=400)

            amount_deduct=round(disposable_earnings-exempt_amount,2)

            net_pay=round(disposable_earnings-amount_deduct,2) 
            if net_pay <0:
                net_pay=0
            else:
                net_pay=net_pay

            # Create CalculationResult object
            federal_case_result.objects.create(
                employee_id=data['employee_id'],
                employer_id=data['employer_id'],
                result=amount_deduct,
                net_pay=net_pay
            
            )
            federal_tax_data_and_result.objects.create(
                employee_id=data['employee_id'],
                employer_id=data['employer_id'],
                fedral_income_tax=federal_income_tax_rate,
                social_and_security=social_tax_rate,
                medicare_tax=medicare_tax_rate,
                state_tax=state_tax_rate,
                earnings=earnings,
                local_tax=local_tax_rate,
                garnishment_fees=garnishment_fees,
                workers_compensation=workers_compensation,
                medical_insurance=medical_insurance,
                contribution=contribution,
                united_way_contribution=united_way_contribution,
                filing_status=filing_status,
                no_of_exception=no_of_exception,
                pay_period=pay_period,
                total_tax=total_tax,
                disposable_earnings=disposable_earnings,
                exempt_amount=exempt_amount,
                amount_deduct=amount_deduct,
                net_pay=net_pay
            )
            LogEntry.objects.create(
                action='Federal Tax Calculation data Added',
                details=f'Federal Tax Calculation data Added successfully with employer ID {user.employer_id} and employee ID {user.employee_id}'
            )
            return Response({'message': 'Federal Tax Calculations Details Successfully Registered', "status code":status.HTTP_200_OK})

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
    
class get_federal_case_result(APIView):
    def get(self, request, employer_id,employee_id):
        employees = federal_case_result.objects.filter(employer_id=employer_id,employee_id=employee_id).order_by('-timestamp')[0:1]
        if employees.exists():
            try:
                serializer = federal_case_result_Serializer(employees,many=True)
                response_data = {
                    'success': True,
                    'message': 'Data retrieved successfully',
                    'status code': status.HTTP_200_OK,
                    'data': serializer.data
                }
                return JsonResponse(response_data)
            except federal_case_result.DoesNotExist:
                return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
            except Exception as e:
                return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
        else:
            return JsonResponse({'message': 'Employee ID not found', 'status code': status.HTTP_404_NOT_FOUND})


class get_federal_case_data(APIView):
    def get(self, request, employer_id,employee_id):
        employees = federal_loan_case_data.objects.filter(employer_id=employer_id,employee_id=employee_id).order_by('-timestamp')[0:1]
        if employees.exists():
            try:
                serializer = federal_loan_data_Serializer(employees,many=True)
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

class get_federal_case_data_and_result(APIView):
    def get(self, request, employer_id,employee_id):
        employees = federal_tax_data_and_result.objects.filter(employer_id=employer_id,employee_id=employee_id).order_by('-timestamp')[0:1]
        if employees.exists():
            try:
                serializer = federal_case_result_and_data_Serializer(employees,many=True)
                response_data = {
                    'success': True,
                    'message': 'Data retrieved successfully',
                    'status code': status.HTTP_200_OK,
                    'data': serializer.data
                }
                return JsonResponse(response_data)
            except federal_tax_data_and_result.DoesNotExist:
                return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
            except Exception as e:
                return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
        else:
            return JsonResponse({'message': 'Employee ID not found', 'status code': status.HTTP_404_NOT_FOUND})

class get_all_federal_tax_result(APIView):
    def get(self, request, employer_id):
        employees = federal_case_result.objects.filter(employer_id=employer_id,)
        if employees.exists():
            try:
                serializer = federal_case_result_Serializer(employees,many=True)
                response_data = {
                    'success': True,
                    'message': 'Federal Case Result Data retrieved successfully',
                    'status code': status.HTTP_200_OK,
                    'data': serializer.data
                }
                return JsonResponse(response_data)
            except federal_case_result.DoesNotExist:
                return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
            except Exception as e:
                return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
        else:
            return JsonResponse({'message': 'Employee ID not found', 'status code': status.HTTP_404_NOT_FOUND})
 

