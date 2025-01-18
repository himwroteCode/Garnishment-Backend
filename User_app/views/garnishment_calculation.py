from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from User_app.models import *
from rest_framework.response import Response
from ..serializers import *
from rest_framework.views import APIView
from auth_project.garnishment_library import gar_resused_classes as gc
from auth_project.garnishment_library.child_support import ChildSupport,MultipleChild,SingleChild as gc
from django.utils.decorators import method_decorator

from auth_project.garnishment_library.federal_case import federal_tax

@method_decorator(csrf_exempt, name='dispatch')
class CalculationDataView(APIView):

    """
    API View to handle Garnishment calculations and save data to the database.
    """
    CHILSUPPORT = "child_support"
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            batch_id = data.get("batch_id")
            state=data.get("state")
            rows = data.get("rows", [])
            output = []

            # Validate batch_id
            if not batch_id:
                return Response({"error": "batch_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate rows
            if not rows:
                return Response({"error": "No rows provided"}, status=status.HTTP_400_BAD_REQUEST)

            for record in rows:
                # Validate essential fields
                # required_fields = [
                #     "employee_id", "employer_id", "gross_pay", "state"
                # ]
                # missing_fields = [field for field in required_fields if field not in record]
                # if missing_fields:
                #     return Response(
                #         {"error": f"Missing fields in record: {', '.join(missing_fields)}"},
                #         status=status.HTTP_400_BAD_REQUEST
                #     )
                
                

                garnishment_type = record.get("garnishment_type")

                if garnishment_type == self.CHILSUPPORT:
                    # Validate child support fields
                    # required_child_support_fields = [
                    #     "child_support", "arrears_greater_than_12_weeks", "support_second_family", "gross_pay", "state"
                    # ]
                    # missing_child_support_fields = [
                    #     field for field in required_child_support_fields if field not in record
                    # ]
                    # if missing_child_support_fields:
                    #     return Response(
                    #         {"error": f"Missing fields in record: {', '.join(missing_child_support_fields)}"},
                    #         status=status.HTTP_400_BAD_REQUEST
                    #     )

                    # Perform calculations
                    tcsa = ChildSupport().get_list_supportAmt(record)
                    result = MultipleChild().calculate(record) if len(tcsa) > 1 else ChildSupport().calculate(record)

                elif garnishment_type == "federal_tax":
                    # Validate federal tax fields
                    required_federal_tax_fields = ["filing_status", "gross_pay", "no_of_exception_for_Self"]
                    missing_federal_tax_fields = [
                        field for field in required_federal_tax_fields if field not in record
                    ]
                    if missing_federal_tax_fields:
                        return Response(
                            {"error": f"Missing fields in record: {', '.join(missing_federal_tax_fields)}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    # Perform calculations
                    gross_pay = record.get("gross_pay")
                    state = record.get("state")
                    result = federal_tax().calculate(record)

                elif garnishment_type == "student_loan":
                    # Validate student loan fields
                    required_student_loan_fields = ["gross_pay", "state"]
                    missing_student_loan_fields = [
                        field for field in required_student_loan_fields if field not in record
                    ]
                    if missing_student_loan_fields:
                        return Response(
                            {"error": f"Missing fields in record: {', '.join(missing_student_loan_fields)}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Perform calculations
                    gross_pay = record.get("gross_pay")
                    state = record.get("state")
                    result = StudentLoan().calculate_student_loan(gross_pay, state)

                else:
                    return Response(
                        {"error": f"Unsupported garnishment_type: {garnishment_type}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Append result to output
                output.append({
                    "employee_id": record.get("employee_id"),
                    "employer_id": record.get("employer_id"),
                    "withhuolding_amt": result
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
                    "message": "Calculations successfully registered",
                    "status_code": status.HTTP_200_OK,
                    "results": output
                },
                status=status.HTTP_200_OK
            )

        except Employee_Detail.DoesNotExist:
            return Response(
                {"error": "Employee details not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e), "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# record=   {
#       "employee_id": "EMP009",
#       "employer_id" :"EMP001",
#       "gross_pay": 600,
#       "employee_name": "Michael Johnson",
#       "garnishment_fees": 5,
#       "arrears_greater_than_12_weeks": "Yes",
#       "support_second_family": "Yes",
#       "child_support" : [ {"amount": 200, "arrear": 6}, {"amount": 300, "arrear": 0}],
#       "taxs":[{"fit":200 },{"sst":10} ,{"mct":20}, {"st":10} , {"lt":5}],
#       "state": "Florida",
#       "arrears_amount1": 99,
#       "pay_period" : "weekly",
#       "mandatory_deductions":10.0,
#        "garnishment_type":"child_support"
# } 

# print("calculate_twa",ChildSupport().calculate_twa(record))
# print("calculate_de_rule",ChildSupport().calculate_de_rule(record))
# print("calculate_md",ChildSupport().calculate_md(record))
# print("calculate_wl",ChildSupport().calculate_wl(record))
# print("calculate_tcsa",ChildSupport().get_list_supportAmt(record))
# print("calculate_tcsa_sum",sum(ChildSupport().get_list_supportAmt(record)))
# print("calculate_taa",ChildSupport().get_list_support_arrearAmt(record))
# print("calculate_ade",ChildSupport().calculate_ade(record))
# print("calculate_wa",ChildSupport().calculate_wa(record))


