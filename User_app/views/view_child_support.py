from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from User_app.models import *
from rest_framework.response import Response
from ..serializers import *
from rest_framework.decorators import api_view
from rest_framework.views import APIView

@csrf_exempt
@api_view(['POST'])
def CalculationDataView(request):
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

                user = Garcalculation_data.objects.create(**record)
    
                # Retrieve the employee, tax, and employer records
                # employee = Employee_Details.objects.get(employee_id=data['employee_id'], employer_id=data['employer_id'])
                # tax = Tax_details.objects.get(employer_id=data['employer_id'])
                # employer = Employer_Profile.objects.get(employer_id=data['employer_id'])
                employee_id = record.get("employee_id")
                employer_id = record.get("employer_id")
                amount_to_withhold_child1 = record.get('amount_to_withhold_child1', 0)
                amount_to_withhold_child2 = record.get('amount_to_withhold_child2', 0)
                amount_to_withhold_child3 = record.get('amount_to_withhold_child3', 0)
                amount_to_withhold_child4 = record.get('amount_to_withhold_child4', 0)  # Using get to avoid KeyError
                amount_to_withhold_child5 = record.get('amount_to_withhold_child5', 0)
                arrears_amt_Child1 = record.get('arrears_amt_Child1', 0)
                arrears_amt_Child2 = record.get('arrears_amt_Child2', 0)
                arrears_amt_Child3 = record.get('arrears_amt_Child3', 0)
                arrears_amt_Child4 = record.get('arrears_amt_Child4', 0)
                arrears_amt_Child5 = record.get('arrears_amt_Child5', 0)
                arrears_greater_than_12_weeks = record.get('arrears_greater_than_12_weeks')
                support_second_family = record.get('support_second_family')
                number_of_child_support_order = record.get('number_of_child_support_order')
                number_of_arrear = record.get('number_of_arrear')
                garnishment_fees = record.get('garnishment_fees')
                pay_period=record.get('pay_period')
                state=record.get('state')
                disposable_income = record.get('disposable_income')
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
                allowable_disposable_earnings = round(disposable_income * ccpa_limit, 2)
                withholding_available = round(allowable_disposable_earnings - garnishment_fees, 2)
                other_garnishment_amount = round(disposable_income * 0.25, 2)
    
                # Federal Minimum Wage calculation
   
                if pay_period.lower()=="weekly":
                    fmw = 30 * 7.25
                elif pay_period.lower()=="biweekly":
                    fmw = 60 * 7.25
                
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
                    amount_to_withhold_child1 = allowed_amount_for_garnishment / number_of_child_support_order
                else:
                    amount_to_withhold_child1 = 0
    
                if (allowed_amount_for_garnishment - amount_to_withhold) >= 0:
                    amount_to_withhold_child2 = amount_to_withhold_child2
                elif allocation_method_for_garnishment == "Pro Rate":
                    ratio = amount_to_withhold_child2 / amount_to_withhold
                    amount_to_withhold_child2 = allowed_amount_for_garnishment * ratio
                elif amount_to_withhold_child2 > 0:
                    amount_to_withhold_child2 = allowed_amount_for_garnishment / number_of_child_support_order
                else:
                    amount_to_withhold_child2 = 0
    
                if (allowed_amount_for_garnishment - amount_to_withhold) >= 0:
                    amount_to_withhold_child3 = amount_to_withhold_child3
                elif allocation_method_for_garnishment == "Pro Rate":
                    ratio = amount_to_withhold_child3 / amount_to_withhold
                    amount_to_withhold_child3 = allowed_amount_for_garnishment * ratio
                elif amount_to_withhold_child3 > 0:
                    amount_to_withhold_child3 = allowed_amount_for_garnishment / number_of_child_support_order
                else:
                    amount_to_withhold_child3 = 0
                
                if (allowed_amount_for_garnishment - amount_to_withhold) >= 0:
                    amount_to_withhold_child4 = amount_to_withhold_child3
                elif allocation_method_for_garnishment == "Pro Rate":
                    ratio = amount_to_withhold_child4 / amount_to_withhold
                    amount_to_withhold_child4 = allowed_amount_for_garnishment * ratio
                elif amount_to_withhold_child4 > 0:
                    amount_to_withhold_child4 = allowed_amount_for_garnishment / number_of_child_support_order
                else:
                    amount_to_withhold_child3 = 0
    
                if (allowed_amount_for_garnishment - amount_to_withhold) >= 0:
                    amount_to_withhold_child5 = amount_to_withhold_child3
                elif allocation_method_for_garnishment == "Pro Rate":
                    ratio = amount_to_withhold_child5/ amount_to_withhold
                    amount_to_withhold_child5 = allowed_amount_for_garnishment * ratio
                elif amount_to_withhold_child5 > 0:
                    amount_to_withhold_child5= allowed_amount_for_garnishment / number_of_child_support_order
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
    
                net_pay=round(disposable_income-allowed_amount_for_other_garnishment,2)
    
                if net_pay <0:
                    net_pay=0
                else:
                    net_pay=net_pay
                # Create Calculation_data_results object
                # Calculation_data_results.objects.create(
                #     employee_id=data['employee_id'],
                #     employer_id=data['employer_id'],
                #     support_second_family=support_second_family,
                #     garnishment_fees=garnishment_fees,
                #     arrears_greater_than_12_weeks=arrears_greater_than_12_weeks,
                #     amount_to_withhold_child1=amount_to_withhold_child1,
                #     amount_to_withhold_child2=amount_to_withhold_child2,
                #     amount_to_withhold_child3=amount_to_withhold_child3,
                #     amount_to_withhold_child4=amount_to_withhold_child4,
                #     amount_to_withhold_child5=amount_to_withhold_child5,
                #     arrears_amt_Child1=arrears_amt_Child1,
                #     arrears_amt_Child2=arrears_amt_Child2,
                #     arrears_amt_Child3=arrears_amt_Child3,
                #     arrears_amt_Child4=arrears_amt_Child4,
                #     arrears_amt_Child5=arrears_amt_Child5,
                #     number_of_arrear=number_of_arrear,
                #     number_of_garnishment=number_of_garnishment,
                #     disposable_income=disposable_income,
                #     allowable_disposable_earnings=allowable_disposable_earnings,
                #     withholding_available=withholding_available,
                #     other_garnishment_amount=other_garnishment_amount,
                #     amount_left_for_arrears=amount_left_for_arrears,
                #     allowed_amount_for_other_garnishment=allowed_amount_for_other_garnishment
                # )
                # Create CalculationResult object
                CalculationResult.objects.create(
                    employee_id=employee_id,
                    employer_id=employer_id,
                    result=allowed_amount_for_other_garnishment,
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
                    net_pay=net_pay
                )
                LogEntry.objects.create(
                    action='Calculation data Added',
                    details=f'Calculation data Added successfully with employer ID {user.employer_id} and employee ID {user.employee_id}'
                )
                return Response({'message': 'Child Support Calculations Details Successfully Registered', "status code":status.HTTP_200_OK})
        except Employee_Details.DoesNotExist:
            return Response({"error": "Employee details not found"}, status=status.HTTP_404_NOT_FOUND)
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
  