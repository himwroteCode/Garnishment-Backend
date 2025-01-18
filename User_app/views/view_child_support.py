from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from User_app.models import *
from rest_framework.response import Response
from ..serializers import *
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from auth_project.garnishment_library import gar_resused_classes as gc
from django.utils.decorators import method_decorator



class ChildSupport:
    """
    This class contains utility functions to calculate various child support-related amounts.
    """
    PRORATE = "prorate"
    DEVIDEEQUALLY = "divide equally"
    CHILSUPPORT = "child_support"
    def calculate_de(self,record):
        gross_pay = record.get("gross_pay") 
        mandatory_deductions=record.get("mandatory_deductions")
        # Calculate disposable earnings
        return gross_pay - mandatory_deductions
    
    def get_list_supportAmt(self, record):
        child_support=record.get(self.self.CHILSUPPORT)

        return [
            value 
            for Amt_dict in child_support
            for key, value in Amt_dict.items() 
            if key.lower().startswith('amount')
        ]


    def get_list_support_arrearAmt(self, record):
        child_support=record.get(self.CHILSUPPORT)
        return [
            value
            for Amt_dict in child_support
            for key, value in Amt_dict.items() 
            if key.lower().startswith('arrear')
        ]


    def calculate_wl(self, record):

        # Extract necessary values from the record
        state = record.get("state")
        employee_id = record.get("employee_id")
        supports_2nd_family = record.get("support_second_family")
        arrears_of_more_than_12_weeks = record.get("arrears_of_more_than_12_weeks")

        # Determine the state rules
        state_rules = gc.WLIdentifier().get_state_rules(state)

        calculate_tcsa = len(self.get_list_supportAmt(record))
       
        # Calculate Disposable Earnings (DE)
        de = self.calculate_de(record)

        # Determine if DE > 145 and if there is more than one order
        de_gt_145 = "No" if de <= 145 or state_rules != "Rule_6" else "Yes"

        #Determine arrears_of_more_than_12_weeks
        arrears_of_more_than_12_weeks = "" if state_rules == "Rule_4" else "Yes"

        #Determine order_gt_one
        order_gt_one = "No" if calculate_tcsa > 1 or state_rules != "Rule_4" else "Yes"


        

        # Identify withholding limit using state rules
        wl_limit = gc.WLIdentifier().find_wl_value(de,state, employee_id, supports_2nd_family, arrears_of_more_than_12_weeks, de_gt_145, order_gt_one)

        return wl_limit

    def calculate_twa(self, record):
        
        tcsa = self.get_list_supportAmt(record)
        taa = self.get_list_support_arrearAmt(record)
        return sum(tcsa) + sum(taa)

    def calculate_ade(self, record):
        wl = self.calculate_wl(record)
        de = self.calculate_de(record)
        return wl * de

    def calculate_wa(self, record):
        tcsa = self.get_list_supportAmt(record)
        ade = self.calculate_ade(record)
        return min(ade, sum(tcsa))

    def calculate_each_child_support_amt(self, record):

        tcsa = self.get_list_supportAmt(record)
        return {f"child support amount{i+1}": amount for i, amount in enumerate(tcsa)}

    def calculate_each_arrears_amt(self, record):

        taa = self.get_list_support_arrearAmt(record)
        return {f"arrear amount{i+1}": amount for i, amount in enumerate(taa)}


class SingleChild(ChildSupport):
    def calculate(self, record):
        # Extract values from the record
        child_support_amount = self.get_list_supportAmt(record)[0]
        arrear_amount = self.get_list_support_arrearAmt(record)[0]

        # Calculate Adjusted Disposable Earnings (ADE) using a helper function
        ade = self.calculate_ade(record)
        # Determine the withholding amount and remaining arrear amount
        if ade > child_support_amount:
            # ADE is sufficient to cover the child support amount
            withholding_amount = child_support_amount
            amount_left_for_arrears = ade - child_support_amount

            if amount_left_for_arrears >= arrear_amount:
                # Remaining ADE can cover the arrear amount
                arrear_amount = arrear_amount
            else:
                # Remaining ADE is not sufficient to cover the arrear amount
                arrear_amount = amount_left_for_arrears
        else:
            # ADE is not sufficient to cover the child support amount
            withholding_amount = ade
            arrear_amount = 0

        return withholding_amount, arrear_amount

class MultipleChild(ChildSupport):
    """
    This class calculates the child support amounts and arrear amounts for multiple child support orders.
    """

    def calculate(self, record):

        # Extract necessary values and calculate required metrics
        ade = self.calculate_ade(record)
        tcsa = self.get_list_supportAmt(record)
        taa = self.get_list_support_arrearAmt(record)
        twa = self.calculate_twa(record)
        wa = self.calculate_wa(record)
        state = record.get("state")

        # Determine the allocation method for garnishment based on the state
        allocation_method_for_garnishment = gc.AllocationMethodIdentifiers(state).get_allocation_method()

        if ade > twa:
            # ADE is sufficient to cover the total withholding amount (TWA)
            child_support_amount = self.calculate_each_child_support_amt(record)
            arrear_amount = self.calculate_each_arrears_amt(record)
        else:
            # Apply the allocation method for garnishment
            if allocation_method_for_garnishment == "prorate":
                child_support_amount = {
                    f"child support amount {i+1}": (amount / twa) * ade for i, amount in enumerate(tcsa)
                }
                
                amount_left_for_arrears = wa - sum(tcsa)

                if amount_left_for_arrears <= 0:
                    arrear_amount = {f"arrear amount {i+1}": 0 for i, _ in enumerate(taa)}
                else:
                    if amount_left_for_arrears >=taa:
                        arrear_amount={f"arrear amount{i+1}": (amount/taa)*amount_left_for_arrears for i, amount in enumerate(taa)}
                    else:
                        arrear_amount=self.calculate_each_arrears_amt(record)
            
            elif allocation_method_for_garnishment == "divide equally":
                child_support_amount = {
                    f"child support amount {i+1}": ade / len(tcsa) for i, _ in enumerate(tcsa)
                }
                
                amount_left_for_arrears = ade - sum(tcsa)

                if amount_left_for_arrears <= 0:
                    arrear_amount = {f"arrear amount {i+1}": 0 for i, _ in enumerate(taa)}
                else:
                    if amount_left_for_arrears >=taa:
                        arrear_amount=self.calculate_each_arrears_amt(record)                       
                    else:
                        arrear_amount={f"arrear amount{i+1}": amount/len(taa)+1 for i, amount in enumerate(taa)}
            else:
                raise ValueError("Invalid allocation method for garnishment.")

        return child_support_amount, arrear_amount



@method_decorator(csrf_exempt, name='dispatch')
class CalculationDataView(APIView):
    """
    API View to handle Garnishment calculations and save data to the database.
    """

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            batch_id = data.get("batch_id")
            rows = data.get("rows", [])
            output = []

            # Validate batch number
            if not batch_id:
                return Response({"error": "batch_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate rows
            if not rows:
                return Response({"error": "No rows provided"}, status=status.HTTP_400_BAD_REQUEST)
            
            for record in rows:
                # Validate essential fields in each record
                required_fields = [
                    "employee_id", "employer_id", "gross_pay",  "mandatory_deductions", "state"
                ]
                missing_fields = [field for field in required_fields if field not in record]
                if missing_fields:
                    return Response(
                        {"error": f"Missing fields in record: {', '.join(missing_fields)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if "garnishment_type"==self.self.CHILSUPPORT:
                    # Validate child support fields
                    required_child_support_fields = [
                        self.CHILSUPPORT, "arrears_greater_than_12_weeks", "support_second_family","gross_pay","state"
                    ]
                    
                    missing_child_support_fields = [
                        field for field in required_child_support_fields if field not in record
                    ]
                    if missing_child_support_fields:
                        return Response(
                            {"error": f"Missing fields in record: {', '.join(missing_child_support_fields)}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )     
                    else:                   
                        
                        # Extract necessary values        
                        tcsa = ChildSupport().get_list_supportAmt(record)
        
                        # Perform calculations based on the number of child support orders
                        if len(tcsa) > 1:
                            result = MultipleChild().calculate(record)
                        else:
                            result = SingleChild().calculate(record)
        
                        # Save record to the database
                        # user = Garcalculation_data.objects.create(**record)
                        output.append({
                            "employee_id": record.get("employee_id"),
                            "employer_id": record.get("employer_id"),
                            "result": result
                        })
                    # Log the action
                    LogEntry.objects.create(
                        action="Calculation data added",
                        details=(
                            f"Calculation data added successfully with employer ID "
                            f"{record.get('employer_id')} and employee ID {record.get('employee_id')}"
                        )
                    )
                elif "garnishment_type"=="federal_tax":
                    # Validate federal tax fields
                    required_federal_tax_fields = [
                        "filing_status", "gross_pay", "state"
                    ]
                    missing_federal_tax_fields = [
                        field for field in required_federal_tax_fields if field not in record
                    ]
                    if missing_federal_tax_fields:
                        return Response(
                            {"error": f"Missing fields in record: {', '.join(missing_federal_tax_fields)}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    else:
                        # Extract necessary values
                        filing_status = record.get("filing_status")
                        gross_pay = record.get("gross_pay")
                        state = record.get("state")
        
                        # Perform calculations
                        result = gc.FederalTax().calculate_federal_tax(filing_status, gross_pay, state)
        
                        # Save record to the database
                        # user = Garcalculation_data.objects.create(**record)
                        output.append({
                            "employee_id": record.get("employee_id"),
                            "employer_id": record.get("employer_id"),
                            "result": result
                        })
        
                        # Log the action
                        LogEntry.objects.create(
                            action="Calculation data added",
                            details=(
                                f"Calculation data added successfully with employer ID "
                                f"{record.get('employer_id')} and employee ID {record.get('employee_id')}"
                            )
                        )
                elif "garnishment_type"=="student_loan":
                    # Validate student loan fields
                    required_student_loan_fields = [
                        "gross_pay", "state"
                    ]
                    missing_student_loan_fields = [
                        field for field in required_student_loan_fields if field not in record
                    ]
                    if missing_student_loan_fields:
                        return Response(
                            {"error": f"Missing fields in record: {', '.join(missing_student_loan_fields)}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    else:
                        # Extract necessary values
                        gross_pay = record.get("gross_pay")
                        state = record.get("state")
        
                        # Perform calculations
                        result = gc.StudentLoan().calculate_student_loan(gross_pay, state)
        
                        # Save record to the database
                        # user = Garcalculation_data.objects.create(**record)
                        output.append({
                            "employee_id": record.get("employee_id"),
                            "employer_id": record.get("employer_id"),
                            "result": result
                        })
        
                        # Log the action
                        LogEntry.objects.create(
                            action="Calculation data added",
                            details=(
                                f"Calculation data added successfully with employer ID "
                                f"{record.get('employer_id')} and employee ID {record.get('employee_id')}"
                            )
                        )

            return Response(
                {
                    "message": "Child Support Calculations Details Successfully Registered",
                    "status_code": status.HTTP_200_OK,
                    "results": output
                },
                status=status.HTTP_200_OK
            )
        except Employee_Details.DoesNotExist:
            return Response(
                {"error": "Employee details not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        # except Employer_Profile.DoesNotExist:
        #     return Response(
        #         {"error": "Employer profile not found"},
        #         status=status.HTTP_404_NOT_FOUND
        #     )
        except Exception as e:
            return Response(
                {"error": str(e), "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# record=   {
#       "employee_id": "EMP002",
#       "employer_id" :"EMP001",
#       "gross_pay": 400,
#       "employee_name": "Michael Johnson",
#       "garnishment_fees": 5,
#       "arrears_greater_than_12_weeks": "Yes",
#       "support_second_family": "No",
#       self.CHILSUPPORT : [ {"amount": 150, "arrear": 15}, {"amount": 100, "arrear": 0}],
#       "state": "Texas",
#       "arrears_amount1": 99,
#       "pay_period" : "weekly",
#       "mandatory_deductions":40
#     }   

# print("calculate_twa",ChildSupport().calculate_twa(record))
# print("calculate_wl",ChildSupport().calculate_wl(record))
# print("calculate_tcsa",ChildSupport().get_list_supportAmt(record))
# print("calculate_tcsa_sum",sum(ChildSupport().get_list_supportAmt(record)))
# print("calculate_taa",ChildSupport().get_list_support_arrearAmt(record))
# print("calculate_ade",ChildSupport().calculate_ade(record))
# print("calculate_wa",ChildSupport().calculate_wa(record))
# print("calculate_wa",MultipleChild().calculate(record))


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

class ChildSupportGarnishmentBatchResult(APIView):
    def get(self, request, batch_id):
        employees = CalculationResult.objects.filter(batch_id=batch_id)
        if employees.exists():
            try:
                employee= employees.order_by('-timestamp')
                serializer = ResultSerializer(employee, many=True)
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
  