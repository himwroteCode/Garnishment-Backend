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
    def calculate_de(self,record):
        gross_pay = record.get("gross_pay") 
        mandatory_deductions=record.get("mandatory_deductions")
        # Calculate disposable earnings
        return gross_pay - mandatory_deductions

    def calculate_wl(self, record):

        # Extract necessary values from the record
        state = record.get("state")
        employee_id = record.get("employee_id")
        no_of_child_support_order = record.get("no_of_child_support_order", 0)
        rule_name = record.get("rule_name")
        supports_2nd_family = record.get("supports_2nd_family")
        arrears_of_more_than_12_weeks = record.get("arrears_of_more_than_12_weeks")


        # Calculate Disposable Earnings (DE)
        de = self.calculate_de(record)

        # Determine if DE > 145 and if there is more than one order
        de_gt_145 = "Yes" if de > 145 else "No"
        order_gt_one = "Yes" if no_of_child_support_order > 1 else "No"

        # Identify withholding limit using state rules
        wl_limit = gc.WLIdentifier(
            state, de, employee_id, rule_name, supports_2nd_family, 
            arrears_of_more_than_12_weeks, de_gt_145, order_gt_one
        ).get_state_rules()

        return wl_limit

    def calculate_tcsa(self, record):

        return [
            value for rec in record 
            for key, value in rec.items() 
            if key.lower().startswith('amount_to_withhold_child')
        ]

    def calculate_taa(self, record):

        return [
            value for rec in record 
            for key, value in rec.items() 
            if key.lower().startswith('arrear_amount')
        ]

    def calculate_twa(self, record):
        
        tcsa = self.calculate_tcsa(record)
        taa = self.calculate_taa(record)
        return sum(tcsa) + sum(taa)

    def calculate_ade(self, record):
        wl = self.calculate_wl(record)
        de = self.calculate_de(record)
        return wl * de

    def calculate_wa(self, record):

        tcsa = self.calculate_tcsa(record)
        ade = self.calculate_ade(record)
        return min(ade, tcsa)

    def calculate_each_child_support_amt(self, record):

        tcsa = self.calculate_tcsa(record)
        return {f"child support amount{i+1}": amount for i, amount in enumerate(tcsa)}

    def calculate_each_arrears_amt(self, record):

        taa = self.calculate_taa(record)
        return {f"arrear amount{i+1}": amount for i, amount in enumerate(taa)}


class SingleChild(ChildSupport):
    def calculate(self, record):
        # Extract values from the record
        child_support_amount = record.get("child_support_amount", 0)
        arrear_amount = record.get("arrear_amount", 0)

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

class MultipleChild:
    """
    This class calculates the child support amounts and arrear amounts for multiple child support orders.
    """

    def calculate(self, record, mandatory_deductions, gross_pay):

        # Extract necessary values and calculate required metrics
        ade = self.calculate_ade(record)
        tcsa = self.calculate_tcsa(record)
        taa = self.calculate_taa(record)
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
            if allocation_method_for_garnishment == self.PRORATE:
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
            
            elif allocation_method_for_garnishment == self.DIVIDEEQUALLY :
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
    API View to handle child support calculations and save data to the database.
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

                # Extract necessary values
                gross_pay = record.get("gross_pay")
                mandatory_deductions = record.get("mandatory_deductions")
                tcsa = self.calculate_tcsa(record)

                # Perform calculations based on the number of child support orders
                if tcsa > 1:
                    result = MultipleChild().calculate(record, mandatory_deductions, gross_pay)
                else:
                    result = SingleChild().calculate(record, mandatory_deductions, gross_pay)

                # Save record to the database
                user = Garcalculation_data.objects.create(**record)
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

        # except Employee_Details.DoesNotExist:
        #     return Response(
        #         {"error": "Employee details not found"},
        #         status=status.HTTP_404_NOT_FOUND
        #     )
        except Employer_Profile.DoesNotExist:
            return Response(
                {"error": "Employer profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        # except Exception as e:
        #     return Response(
        #         {"error": str(e), "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
        #     )
