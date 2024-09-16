from django.urls import path
from ..views.view_federal_tax import *

urlpatterns = [
    path('FederalCaseData/', federal_case, name='federal_case_data'),
    path('GetAllFederalTaxResult/<int:employer_id>/', get_all_federal_tax_result.as_view(), name='get_all_federal_tax_result'),
    path('FederalCaseResult/<int:employer_id>/<int:employee_id>/', get_federal_case_result.as_view(), name='get_federal_case_result'),
    path('FederalCaseDataAndResult/<int:employer_id>/<int:employee_id>/', get_federal_case_data_and_result.as_view(), name='get_federal_case_data_and_result'),
    path('GetFederalCaseData/<int:employer_id>/<int:employee_id>/', get_federal_case_data.as_view(), name='get_federal_case_data'),
]
