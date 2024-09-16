from rest_framework import status
from django.contrib import messages
from auth_project.config import ccpa_limit
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from User_app.models import *
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
import csv
from rest_framework.views import APIView


@csrf_exempt
@api_view(['POST'])
def CalculationDataView(request):
    if request.method == 'POST':
        try:
            data = request.data
            required_fields = ['employer_id','employee_id',
                'earnings', 'employee_name', 'garnishment_fees',
                'arrears_greater_than_12_weeks', 'support_second_family', 'amount_to_withhold_child1'
                , 'state', 'number_of_arrears', 'order_id','federal_income_tax', 'social_tax','medicare_tax','state_tax']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return Response({'error': f'Required fields are missing_Done: {", ".join(missing_fields)}'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = Garcalculation_data.objects.create(**data)

            # Retrieve the employee, tax, and employer records
            employee = Employee_Details.objects.get(employee_id=data['employee_id'], employer_id=data['employer_id'])
            tax = Tax_details.objects.get(employer_id=data['employer_id'])
            employer = Employer_Profile.objects.get(employer_id=data['employer_id'])
            gdata = Garcalculation_data.objects.filter(employer_id=data['employer_id'], employee_id=data['employee_id']).order_by('-timestamp').first()

            # Extracting earnings and garnishment fees from gdata
            earnings = data['earnings']
            amount_to_withhold_child1 = data.get('amount_to_withhold_child1', 0)
            amount_to_withhold_child2 = data.get('amount_to_withhold_child2', 0)
            amount_to_withhold_child3 = data.get('amount_to_withhold_child3', 0)
            amount_to_withhold_child4 = data.get('amount_to_withhold_child4', 0)  # Using get to avoid KeyError
            amount_to_withhold_child5 = data.get('amount_to_withhold_child5', 0)
            arrears_amt_Child1 = data.get('arrears_amt_Child1', 0)
            arrears_amt_Child2 = data.get('arrears_amt_Child2', 0)
            arrears_amt_Child3 = data.get('arrears_amt_Child3', 0)
            arrears_amt_Child4 = data.get('arrears_amt_Child4', 0)
            arrears_amt_Child5 = data.get('arrears_amt_Child5', 0)
            arrears_greater_than_12_weeks = data['arrears_greater_than_12_weeks']
            support_second_family = data['support_second_family']
            number_of_garnishment = employee.number_of_garnishment
            number_of_arrears = data['number_of_arrears']
            garnishment_fees = data['garnishment_fees']
            federal_income_tax_rate=data['federal_income_tax']


            state=data['state']
            # Calculate the various taxes
            social_tax_rate = data['social_tax']
            medicare_tax_rate = data['medicare_tax']
            state_tax_rate = data['state_tax']
            total_tax = federal_income_tax_rate + social_tax_rate + medicare_tax_rate + state_tax_rate
            disposable_earnings = round(earnings - total_tax, 2)

            # ccpa_limit=ccpa_limit(support_second_family,arrears_greater_than_12_weeks)
            # Calculate ccpa_limit based on conditions
            if support_second_family and arrears_greater_than_12_weeks:
                ccpa_limit = 0.55
            elif not support_second_family and not arrears_greater_than_12_weeks:
                ccpa_limit = 0.60
            elif not support_second_family and arrears_greater_than_12_weeks:
                ccpa_limit = 0.65
            else:
                ccpa_limit = 0.50

            # Calculate allowable disposable earnings
            allowable_disposable_earnings = round(disposable_earnings * ccpa_limit, 2)
            withholding_available = round(allowable_disposable_earnings - garnishment_fees, 2)
            other_garnishment_amount = round(disposable_earnings * 0.25, 2)

            # Federal Minimum Wage calculation
            fmw = 30 * 7.25
            Disposable_Income_minus_Minimum_Wage_rule = round(earnings - fmw, 2)
            Minimum_amt = min(Disposable_Income_minus_Minimum_Wage_rule, withholding_available)

            # Determine allocation method for garnishment
            if state in ["Alabama", "Arizona", "Alaska", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Hawaii", "Florida", "Georgia", "Idaho", "Illinois", "Indiana", "Iowa", "Kentucky", "Louisiana", "Maine", "Montana", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "North Carolina", "North Dakota", "New York", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Utah", "Vermont", "Virginia", "West Virginia", "Wyoming", "Tennessee","Wisconsin", "Wyoming"]:
                allocation_method_for_garnishment = "Divide Equally"
            elif state in ["Kansas", "Texas", "Washington"]:
                allocation_method_for_garnishment = "Pro Rate"

            # Determine the allowable garnishment amount
            if Minimum_amt <= 0:
                allowed_amount_for_garnishment = 0
            else:
                allowed_amount_for_garnishment = Minimum_amt
            amount_to_withhold = amount_to_withhold_child1 + amount_to_withhold_child2 + amount_to_withhold_child3+amount_to_withhold_child4+amount_to_withhold_child5

            if (allowed_amount_for_garnishment - amount_to_withhold) >= 0:
                amount_to_withhold_child1 = amount_to_withhold_child1
            elif allocation_method_for_garnishment == "Pro Rate":
                ratio = amount_to_withhold_child1 / amount_to_withhold
                amount_to_withhold_child1 = allowed_amount_for_garnishment * ratio
            elif amount_to_withhold_child1 > 0:
                amount_to_withhold_child1 = allowed_amount_for_garnishment / number_of_garnishment
            else:
                amount_to_withhold_child1 = 0

            if (allowed_amount_for_garnishment - amount_to_withhold) >= 0:
                amount_to_withhold_child2 = amount_to_withhold_child2
            elif allocation_method_for_garnishment == "Pro Rate":
                ratio = amount_to_withhold_child2 / amount_to_withhold
                amount_to_withhold_child2 = allowed_amount_for_garnishment * ratio
            elif amount_to_withhold_child2 > 0:
                amount_to_withhold_child2 = allowed_amount_for_garnishment / number_of_garnishment
            else:
                amount_to_withhold_child2 = 0

            if (allowed_amount_for_garnishment - amount_to_withhold) >= 0:
                amount_to_withhold_child3 = amount_to_withhold_child3
            elif allocation_method_for_garnishment == "Pro Rate":
                ratio = amount_to_withhold_child3 / amount_to_withhold
                amount_to_withhold_child3 = allowed_amount_for_garnishment * ratio
            elif amount_to_withhold_child3 > 0:
                amount_to_withhold_child3 = allowed_amount_for_garnishment / number_of_garnishment
            else:
                amount_to_withhold_child3 = 0
            
            if (allowed_amount_for_garnishment - amount_to_withhold) >= 0:
                amount_to_withhold_child4 = amount_to_withhold_child3
            elif allocation_method_for_garnishment == "Pro Rate":
                ratio = amount_to_withhold_child4 / amount_to_withhold
                amount_to_withhold_child4 = allowed_amount_for_garnishment * ratio
            elif amount_to_withhold_child4 > 0:
                amount_to_withhold_child4 = allowed_amount_for_garnishment / number_of_garnishment
            else:
                amount_to_withhold_child3 = 0

            if (allowed_amount_for_garnishment - amount_to_withhold) >= 0:
                amount_to_withhold_child5 = amount_to_withhold_child3
            elif allocation_method_for_garnishment == "Pro Rate":
                ratio = amount_to_withhold_child5/ amount_to_withhold
                amount_to_withhold_child5 = allowed_amount_for_garnishment * ratio
            elif amount_to_withhold_child5 > 0:
                amount_to_withhold_child5= allowed_amount_for_garnishment / number_of_garnishment
            else:
                amount_to_withhold_child5 = 0

            amount_to_withhold = amount_to_withhold_child1 + amount_to_withhold_child2 + amount_to_withhold_child3+amount_to_withhold_child4+amount_to_withhold_child5

            # Calculate the amount left for arrears
            if allowed_amount_for_garnishment > 0 and (allowed_amount_for_garnishment - amount_to_withhold) > 0:
                amount_left_for_arrears = round(allowed_amount_for_garnishment - amount_to_withhold, 2)
            else:
                amount_left_for_arrears = 0
            
            allocation_method_for_arrears=allocation_method_for_garnishment
            
            # Determine allowed amount for other garnishment
            allowed_child_support_arrear = arrears_amt_Child1 + arrears_amt_Child2 + arrears_amt_Child3+amount_to_withhold_child4+amount_to_withhold_child5

            if (amount_left_for_arrears - allowed_child_support_arrear) >= 0:
                arrears_amt_Child1 = arrears_amt_Child1
            elif allocation_method_for_arrears == "Pro Rate":
                ratio = arrears_amt_Child1 / allowed_child_support_arrear
                arrears_amt_Child1 = amount_left_for_arrears * ratio
            elif amount_left_for_arrears > 0:
                arrears_amt_Child1 = amount_left_for_arrears / number_of_arrears
            else:
                arrears_amt_Child1 = 0

            if (amount_left_for_arrears - allowed_child_support_arrear) >= 0:
                arrears_amt_Child2 = arrears_amt_Child2
            elif allocation_method_for_arrears == "Pro Rate":
                ratio = arrears_amt_Child2 / allowed_child_support_arrear
                arrears_amt_Child2 = amount_left_for_arrears * ratio
            elif amount_left_for_arrears > 0:
                arrears_amt_Child2 = amount_left_for_arrears / number_of_arrears
            else:
                arrears_amt_Child2 = 0

            if (amount_left_for_arrears - allowed_child_support_arrear) >= 0:
                arrears_amt_Child3 = arrears_amt_Child3
            elif allocation_method_for_arrears == "Pro Rate":
                ratio = arrears_amt_Child3 / allowed_child_support_arrear
                arrears_amt_Child3 = amount_left_for_arrears * ratio
            elif amount_left_for_arrears > 0:
                arrears_amt_Child3 = amount_left_for_arrears / number_of_arrears
            else:
                arrears_amt_Child3 = 0
            
            if (amount_left_for_arrears - allowed_child_support_arrear) >= 0:
                arrears_amt_Child4 = arrears_amt_Child3
            elif allocation_method_for_arrears == "Pro Rate":
                ratio = arrears_amt_Child4 / allowed_child_support_arrear
                arrears_amt_Child3 = amount_left_for_arrears * ratio
            elif amount_left_for_arrears > 0:
                arrears_amt_Child4 = amount_left_for_arrears / number_of_arrears
            else:
                arrears_amt_Child4 = 0

            if (amount_left_for_arrears - allowed_child_support_arrear) >= 0:
                arrears_amt_Child5 = arrears_amt_Child3
            elif allocation_method_for_arrears == "Pro Rate":
                ratio = arrears_amt_Child5 / allowed_child_support_arrear
                arrears_amt_Child5 = amount_left_for_arrears * ratio
            elif amount_left_for_arrears > 0:
                arrears_amt_Child5 = amount_left_for_arrears / number_of_arrears
            else:
                arrears_amt_Child5 = 0

            if (amount_left_for_arrears - allowed_child_support_arrear) <= 0:
                allowed_amount_for_other_garnishment = 0
            else:
                allowed_amount_for_other_garnishment = round(amount_left_for_arrears - allowed_child_support_arrear, 2)

            # Create Calculation_data_results object
            Calculation_data_results.objects.create(
                employee_id=data['employee_id'],
                employer_id=data['employer_id'],
                fedral_income_tax=federal_income_tax_rate,
                social_and_security=social_tax_rate,
                medicare_tax=medicare_tax_rate,
                state_taxes=state_tax_rate,
                earnings=earnings,
                support_second_family=support_second_family,
                garnishment_fees=garnishment_fees,
                arrears_greater_than_12_weeks=arrears_greater_than_12_weeks,
                amount_to_withhold_child1=amount_to_withhold_child1,
                amount_to_withhold_child2=amount_to_withhold_child2,
                amount_to_withhold_child3=amount_to_withhold_child3,
                amount_to_withhold_child4=amount_to_withhold_child4,
                amount_to_withhold_child5=amount_to_withhold_child5,
                arrears_amt_Child1=arrears_amt_Child1,
                arrears_amt_Child2=arrears_amt_Child2,
                arrears_amt_Child3=arrears_amt_Child3,
                arrears_amt_Child4=arrears_amt_Child4,
                arrears_amt_Child5=arrears_amt_Child5,
                number_of_arrears=number_of_arrears,
                allowable_disposable_earnings=allowable_disposable_earnings,
                withholding_available=withholding_available,
                other_garnishment_amount=other_garnishment_amount,
                amount_left_for_arrears=amount_left_for_arrears,
                allowed_amount_for_other_garnishment=allowed_amount_for_other_garnishment
            )

            # Create CalculationResult object
            CalculationResult.objects.create(
                employee_id=data['employee_id'],
                employer_id=data['employer_id'],
                result=allowed_amount_for_other_garnishment
            )

            LogEntry.objects.create(
                action='Calculation data Added',
                details=f'Calculation data Added successfully with employer ID {user.employer_id} and employee ID {user.employee_id}'
            )

            return Response({'message': 'Calculations Details Successfully Registered', "status code":status.HTTP_200_OK})

        except Employee_Details.DoesNotExist:
            return Response({"error": "Employee details not found"}, status=status.HTTP_404_NOT_FOUND)
        except Tax_details.DoesNotExist:
            return Response({"error": "Tax details not found", "status code":status.HTTP_404_NOT_FOUND})
        except Employer_Profile.DoesNotExist:
            return Response({"error": "Employer profile not found", "status code":status.HTTP_404_NOT_FOUND})
        except Exception as e:
            return Response({"error":{str(e)}, "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return Response({'message': 'Please use POST method', "status_code":status.HTTP_400_BAD_REQUEST})

class SingleCalculationDetailView(APIView):
    def get(self, request, employer_id, employee_id):
        employees = CalculationResult.objects.filter(employer_id=employer_id, employee_id=employee_id).order_by('-timestamp')[0:1]
        if employees.exists():
            try:
                serializer = ResultSerializer(employees, many=True)
                response_data = {
                    'success': True,
                    'message': 'Data fetched successfully',
                    'status code': status.HTTP_200_OK,
                    'data': serializer.data
                }
                return JsonResponse(response_data)
            except CalculationResult.DoesNotExist:
                return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
            except Exception as e:
                return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
        else:
            return JsonResponse({'message': 'Employer ID not found', 'status code': status.HTTP_404_NOT_FOUND})


class AllGarnishmentResultDetailView(APIView):
    def get(self, request, employer_id):
        employees = CalculationResult.objects.filter(employer_id=employer_id).order_by('-timestamp')
        if employees.exists():
            try:
                serializer = ResultSerializer(employees, many=True)
                response_data = {
                    'success': True,
                    'message': 'Data retrieved successfully',
                    'status code': status.HTTP_200_OK,
                    'data': serializer.data
                }
                return JsonResponse(response_data)
            except CalculationResult.DoesNotExist:
                return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
            except Exception as e:
                return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
        else:
            return JsonResponse({'message': 'Employer ID not found', 'status code': status.HTTP_404_NOT_FOUND})

class get_child_garnishment_case_data_and_result(APIView):
    def get(self, request, employer_id,employee_id):
        employees = Calculation_data_results.objects.filter(employer_id=employer_id,employee_id=employee_id).order_by('-timestamp')[0:1]
        if employees.exists():
            try:
                serializer = Calculation_data_results_Serializer(employees,many=True)
                response_data = {
                    'success': True,
                    'message': 'Garnishment Result Data retrieved successfully',
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
  