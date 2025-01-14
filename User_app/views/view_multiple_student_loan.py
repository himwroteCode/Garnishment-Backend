from rest_framework import status
from django.http import JsonResponse
from User_app.models import *
from rest_framework.response import Response
from ..serializers import *
from django.db import transaction
from rest_framework.views import APIView
from django.db import transaction


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




from concurrent.futures import ThreadPoolExecutor
from django.db import transaction

class MultipleStudentLoanCalculationData(APIView):
    def post(self, request):
        data = request.data
        batch_id = data.get("batch_id")
        rows = data.get("rows", [])

        # Validate batch ID and rows
        if not batch_id:
            return Response({"error": "batch_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not rows:
            return Response({"error": "No rows provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with ThreadPoolExecutor(max_workers=1000) as executor:
                results = list(executor.map(self.process_record, rows, [batch_id] * len(rows)))

            return Response({
                "message": "Multiple Student Loan Calculations Details Successfully Registered",
                "status_code": status.HTTP_200_OK,
                "result": results
            })

        except Exception as e:
            return Response({"error": str(e), "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR})

    def process_record(self, record, batch_id):
        """
        Process a single record for calculation and database insertion.
        """
        try:
            # Extract values
            employee_id = record.get("employee_id")
            employer_id = record.get("employer_id")
            garnishment_fees = record.get("garnishment_fees", 0)
            disposable_income = record.get("disposable_income", 0)

            with transaction.atomic():
                # Save data to `multiple_student_loan_data`
                user = multiple_student_loan_data.objects.create(**record)

                # Perform calculations
                allowable_disposable_earning = round(disposable_income - garnishment_fees, 2)
                twentyfive_percent_of_earning = round(allowable_disposable_earning * 0.25, 2)
                fmw = 7.25 * 30
                garnishment_amount = self.calculate_garnishment_amount(
                    allowable_disposable_earning, twentyfive_percent_of_earning, fmw, disposable_income
                )
                StudentLoanAmount1 = round(allowable_disposable_earning * 0.15, 2)
                StudentLoanAmount2 = round(allowable_disposable_earning * 0.10, 2)
                StudentLoanAmount3 = round(allowable_disposable_earning * 0, 2)
                net_pay = max(0, round(disposable_income - garnishment_amount, 2))

                # Save results to `multiple_student_loan_data_and_result`
                multiple_student_loan_data_and_result.objects.create(
                    employee_id=employee_id,
                    employer_id=employer_id,
                    garnishment_fees=garnishment_fees,
                    disposable_income=disposable_income,
                    allowable_disposable_earning=allowable_disposable_earning,
                    twentyfive_percent_of_earning=twentyfive_percent_of_earning,
                    fmw=fmw,
                    garnishment_amount=garnishment_amount,
                    StudentLoanAmount1=StudentLoanAmount1,
                    StudentLoanAmount2=StudentLoanAmount2,
                    StudentLoanAmount3=StudentLoanAmount3,
                    net_pay=net_pay
                )

                # Save results to `multiple_student_loan_result`
                multiple_student_loan_result.objects.create(
                    employee_id=employee_id,
                    employer_id=employer_id,
                    garnishment_amount=garnishment_amount,
                    StudentLoanAmount1=StudentLoanAmount1,
                    StudentLoanAmount2=StudentLoanAmount2,
                    StudentLoanAmount3=StudentLoanAmount3,
                    net_pay=net_pay,
                    batch_id=batch_id
                )

                # Add log entry
                LogEntry.objects.create(
                    action="Multiple Student Loan Calculation data Added",
                    details=f"Multiple Student Loan Calculation data Added successfully with employer ID {user.employer_id} and employee ID {user.employee_id}"
                )

                return {
                    "employee_id": employee_id,
                    "batch_id": batch_id,
                    "result": garnishment_amount,
                    "StudentLoanAmount1": StudentLoanAmount1,
                    "StudentLoanAmount2": StudentLoanAmount2,
                    "StudentLoanAmount3": StudentLoanAmount3,
                    "net_pay": net_pay
                }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def calculate_garnishment_amount(allowable_disposable_earning, twentyfive_percent_of_earning, fmw, disposable_income):
        """
        Calculate garnishment amount based on provided values.
        """
        if allowable_disposable_earning < fmw:
            garnishment_amount = 0
        else:
            garnishment_amount = twentyfive_percent_of_earning

        difference = round(disposable_income - fmw, 2)
        if difference > garnishment_amount:
            garnishment_amount = garnishment_amount
        else:
            garnishment_amount = difference

        return max(0, garnishment_amount)


class MultipleStudentLoanBatchResult(APIView):
    def get(self, request, batch_id): 
        employees = multiple_student_loan_result.objects.filter(batch_id=batch_id)
        if employees.exists():
            try:
                employee= employees.order_by('-timestamp')      
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
