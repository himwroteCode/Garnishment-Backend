from django.urls import path
from ..views.view_single_student_loan import *
from ..views import *

urlpatterns = [
    path('StudentLoanCalculationData/',StudentLoanCalculationData, name='Student-Loan-Calculation-Data'),
    path('SingleStudentLoanDataAndResult/<int:employer_id>/<int:employee_id>/',get_single_student_loan_data_and_result.as_view(), name='Student-Loan-Calculation-Data-And-Result'),
    path('GetAllSingleStudentLoanResult/<int:employer_id>/',get_all_Single_Student_loan_result.as_view(), name='GetAllSingleStudentLoanResult'),
    path('GetSingleStudentLoanResult/<int:employer_id>/<int:employee_id>/',get_Single_Student_loan_result.as_view(), name='Get_Single_Student_Loan_Result'),
    path('GetSingleStudentLoanData/<int:employer_id>/<int:employee_id>/',get_single_student_loan_case_data.as_view(), name='Get_Single_Student_Loan_Data'),

]