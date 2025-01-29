from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from User_app.models import *
from django.contrib.auth import  login as auth_login ,get_user_model
from rest_framework.response import Response
from ..serializers import *
from rest_framework.decorators import api_view
import csv
from rest_framework.views import APIView
from rest_framework import status


@csrf_exempt
@api_view(['POST'])
def federal_case(request):
    if request.method == 'POST':
        try:
            data = request.data
            batch_id = data.get("batch_id")
            rows = data.get("rows", [])
            
            # Validate batch number
            if not batch_id:
                return Response({"error": "batch_id is required"}, status=400)

            if not rows:
                return Response({"error": "No rows provided"}, status=400)

            # Process each result
            for record in rows:
                data = request.data        
                user = federal_loan_case_data.objects.create(**record)
    
                # Extracting earnings and garnishment fees from gdata
                garnishment_fees = data.get('garnishment_fees',0)
                
                # Calculate the various taxes
                # mexico_tax=data.get('mexico_tax',0)
                employee_id = record.get("employee_id")
                employer_id = record.get("employer_id")
                filing_status=record.get('filing_status')
                no_of_exception=record.get('no_of_exception',0)
                pay_period=record.get('pay_period')
                disposable_income=record.get('disposable_income',0)
    
                
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
    
                amount_deduct=round(disposable_income-exempt_amount,2)
    
                # net_pay=round(disposable_income-amount_deduct,2) 
                # if net_pay <0:
                #     net_pay=0
                # else:
                #     net_pay=net_pay
    
                # Create CalculationResult object
                federal_case_result.objects.create(
                    employee_id=employee_id,
                    employer_id=employer_id,
                    result=amount_deduct,
                    net_pay=net_pay,
                    batch_id=batch_id
                
                )
                federal_tax_data_and_result.objects.create(
                    employee_id=employee_id,
                    employer_id=employer_id,
                    garnishment_fees=garnishment_fees,
                    filing_status=filing_status,
                    no_of_exception=no_of_exception,
                    pay_period=pay_period,
                    disposable_income=disposable_income,
                    exempt_amount=exempt_amount,
                    amount_deduct=amount_deduct,
                    net_pay=net_pay,
                    batch_id=batch_id
                )
                LogEntry.objects.create(
                    action='Federal Tax Calculation data Added',
                    details=f'Federal Tax Calculation data Added successfully with employer ID {user.employer_id} and employee ID {user.employee_id}'
                )
                return Response({'message': 'Federal Tax Calculations Details Successfully Registered', "status code":status.HTTP_200_OK})

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
            # except Exception as e:
            #     return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
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
 
class FederalCaseBatchResult(APIView):
    def get(self, request, batch_id):
        employees = federal_case_result.objects.filter(batch_id=batch_id)
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
            return JsonResponse({'message': 'Batch ID not found', 'status code': status.HTTP_404_NOT_FOUND})

