from django.urls import path
from ..views.view_multiple_student_loan import *
from ..views import *

urlpatterns = [
    path('MultipleStudentLoanDataAndResult/<int:employer_id>/<int:employee_id>/',get_multiple_student_loan_data_and_result.as_view(), name='Multiple_Student_Loan_Data_and_Result'),
    path('MiltipleStudentLoanCalculationData/',MultipleStudentLoanCalculationData, name='Multiple-Student-Loan-Calculation-Data'),
    path('GetAllMultipleStudentLoanResult/<int:employer_id>/',get_all_multiple_student_loan_result.as_view(), name='GetAllSingleStudentLoanResult'),
    path('GetMultipleStudentLoanResult/<int:employer_id>/<int:employee_id>/',get_multiple_student_loan_result.as_view(), name='get_MultipleStudentLoanResult'),
    path('GetMultipleStudentLoanData/<int:employer_id>/<int:employee_id>/',get_multiple_student_loan_case_data.as_view(), name='Get_Multiple_Student_Loan_Case_Data'),
    path('MultipleStudentLoanBatchResult/<str:batch_id>/',MultipleStudentLoanBatchResult.as_view(), name='GetAllSingleStudentLoanResult'),

]