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
from auth_project.garnishment_library import garnishment_priority_order as gpo

@csrf_exempt
@api_view(['POST'])
def multiple_case_calculation(request):
    if request.method == 'POST':
        try:
            data = request.data
            required_fields = ['employer_id','employee_id'
            , 'employee_name', 'garnishment_fees',
                'arrears_greater_than_12_weeks', 'support_second_family', 'amount_to_withhold_child1'
                , 'state', 'number_of_arrear', 'order_id','disposable_income','no_of_exception','filing_status']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return Response({'error': f'Required fields are missing_Done: {", ".join(missing_fields)}'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = multiple_garnishment_data.objects.create(**data)

            amount_to_withhold_child1 = data.get('amount_to_withhold_child1', 0)
            amount_to_withhold_child2 = data.get('amount_to_withhold_child2', 0)
            amount_to_withhold_child3 = data.get('amount_to_withhold_child3', 0)
            amount_to_withhold_child4 = data.get('amount_to_withhold_child4', 0) 
            amount_to_withhold_child5 = data.get('amount_to_withhold_child5', 0)
            arrears_amt_Child1 = data.get('arrears_amt_Child1', 0)
            arrears_amt_Child2 = data.get('arrears_amt_Child2', 0)
            arrears_amt_Child3 = data.get('arrears_amt_Child3', 0)
            arrears_amt_Child4 = data.get('arrears_amt_Child4', 0)
            arrears_amt_Child5 = data.get('arrears_amt_Child5', 0)
            arrears_greater_than_12_weeks = data['arrears_greater_than_12_weeks']
            support_second_family = data['support_second_family']
            number_of_garnishment = data['number_of_garnishment']
            number_of_arrear = data['number_of_arrear']
            number_of_garnishment = data['number_of_garnishment']
            garnishment_fees = data['garnishment_fees']
            garnishment_order =data['garnishment_order']
            state=data['state']

            disposable_income = data['disposable_income']
            filing_status=data.get('filing_status',0)
            no_of_exception=data.get('no_of_exception',0)
            pay_period=data.get('pay_period')
            garnishment_order_name_list = [name.lower() for name in garnishment_order]
            result = [ state_priority for state_priority in gpo.state_priority_order(state) 
                        if state_priority in garnishment_order_name_list]

            if result[0]=="child support":
                if support_second_family and arrears_greater_than_12_weeks:
                   ccpa_limit = 0.55
                elif not support_second_family and not arrears_greater_than_12_weeks:
                    ccpa_limit = 0.60
                elif not support_second_family and arrears_greater_than_12_weeks:
                    ccpa_limit = 0.65
                else:
                    ccpa_limit = 0.50
    
                # Calculate allowable disposable earnings
                allowable_disposable_earnings = round(disposable_income * ccpa_limit, 2)
                withholding_available = round(allowable_disposable_earnings - garnishment_fees, 2)
                other_garnishment_amount = round(disposable_income * 0.25, 2)
    
                # Federal Minimum Wage calculation
                fmw = 30 * 7.25
                Disposable_Income_minus_Minimum_Wage_rule = round(disposable_income - fmw, 2)
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
                    arrears_amt_Child1 = amount_left_for_arrears / number_of_arrear
                else:
                    arrears_amt_Child1 = 0
                if (amount_left_for_arrears - allowed_child_support_arrear) >= 0:
                    arrears_amt_Child2 = arrears_amt_Child2
                elif allocation_method_for_arrears == "Pro Rate":
                    ratio = arrears_amt_Child2 / allowed_child_support_arrear
                    arrears_amt_Child2 = amount_left_for_arrears * ratio
                elif amount_left_for_arrears > 0:
                    arrears_amt_Child2 = amount_left_for_arrears / number_of_arrear
                else:
                    arrears_amt_Child2 = 0
    
                if (amount_left_for_arrears - allowed_child_support_arrear) >= 0:
                    arrears_amt_Child3 = arrears_amt_Child3
                elif allocation_method_for_arrears == "Pro Rate":
                    ratio = arrears_amt_Child3 / allowed_child_support_arrear
                    arrears_amt_Child3 = amount_left_for_arrears * ratio
                elif amount_left_for_arrears > 0:
                    arrears_amt_Child3 = amount_left_for_arrears / number_of_arrear
                else:
                    arrears_amt_Child3 = 0
                
                if (amount_left_for_arrears - allowed_child_support_arrear) >= 0:
                    arrears_amt_Child4 = arrears_amt_Child3
                elif allocation_method_for_arrears == "Pro Rate":
                    ratio = arrears_amt_Child4 / allowed_child_support_arrear
                    arrears_amt_Child3 = amount_left_for_arrears * ratio
                elif amount_left_for_arrears > 0:
                    arrears_amt_Child4 = amount_left_for_arrears / number_of_arrear
                else:
                    arrears_amt_Child4 = 0
    
                if (amount_left_for_arrears - allowed_child_support_arrear) >= 0:
                    arrears_amt_Child5 = arrears_amt_Child3
                elif allocation_method_for_arrears == "Pro Rate":
                    ratio = arrears_amt_Child5 / allowed_child_support_arrear
                    arrears_amt_Child5 = amount_left_for_arrears * ratio
                elif amount_left_for_arrears > 0:
                    arrears_amt_Child5 = amount_left_for_arrears / number_of_arrear
                else:
                    arrears_amt_Child5 = 0
                if (amount_left_for_arrears - allowed_child_support_arrear) <= 0:
                    allowed_amount_for_other_garnishment = 0
                else:
                    allowed_amount_for_other_garnishment = round(amount_left_for_arrears - allowed_child_support_arrear, 2)
                garnishment_amount=allowed_amount_for_other_garnishment
                garnishment_priority_order="child support"
                net_pay=round(disposable_income-allowed_amount_for_other_garnishment,2)
    
                if net_pay <0:
                    net_pay=0
                else:
                    net_pay=net_pay
                
            elif result[0]=="federal tax levies": 
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
                garnishment_amount= amount_deduct
                garnishment_priority_order="federal tax levies"
                net_pay=round(disposable_income-amount_deduct,2) 
                if net_pay <0:
                    net_pay=0
                else:
                    net_pay=net_pay
    
    
            elif result[0]=="student loans":
                allowable_disposable_earning=round(disposable_income-garnishment_fees,2)
                fifteen_percent_of_eraning= round(allowable_disposable_earning*.15,2)
                fmw=round(7.25*30,2)
                difference=round(disposable_income-fmw,2)
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
                
                garnishment_priority_order="federal tax levies"
                net_pay=round(disposable_income-garnishment_amount,2)

                if net_pay <0:
                    net_pay=0
                else:
                    net_pay=net_pay

            # Create CalculationResult object
            multiple_garnishment_case_result.objects.create(
                employee_id=data['employee_id'],
                employer_id=data['employer_id'],
                garnishment_priority_order=garnishment_priority_order,
                garnishment_amount=garnishment_amount,
                net_pay=net_pay
            
            )
            LogEntry.objects.create(
                action='Multiple Garnishment Case Data Added',
                details=f'Multiple Garnishment Case Data Added successfully with employer ID {user.employer_id} and employee ID {user.employee_id}'
            )
            return Response({'message': 'Multiple Garnishment Case Data Successfully Registered', "status code":status.HTTP_200_OK},)
        except Employee_Details.DoesNotExist:
            return Response({"error": "Employee details not found"}, status=status.HTTP_404_NOT_FOUND)
        except Employer_Profile.DoesNotExist:
            return Response({"error": "Employer profile not found", "status code":status.HTTP_404_NOT_FOUND})
        except Exception as e:
            return Response({"error":{str(e)}, "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return Response({'message': 'Please use POST method', "status_code":status.HTTP_400_BAD_REQUEST})



class get_multiple_garnishment_case_result(APIView):
    def get(self, request, employee_id, employer_id): 
        employees = multiple_garnishment_case_result.objects.filter(employee_id=employee_id, employer_id=employer_id)
        if employees.exists():
            try:
                employee= employees.order_by('-timestamp')[:1]
                serializer = multiple_garnishment_data_Serializer(employee, many=True)
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