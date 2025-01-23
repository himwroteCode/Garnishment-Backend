from django.urls import path
from ..views import *
from ..views.views import *
from django.urls import include, path
from ..views.view_state_tax import *
from ..views.view_multiple_garnishment import *

urlpatterns = [
    path('', include('User_app.urls.url_federal_tax')),
    path('', include('User_app.urls.url_child_support')),
    path('', include('User_app.urls.url_multiple_student_loan')),
    path('', include('User_app.urls.url_single_student_loan')),
    path('', include('User_app.urls.url_state_tax')),
    path('', include('User_app.urls.url_multiple_garnishment')),
    path("register", register, name="register"),
    path("login",login, name="login"),    
    path('employer-profile/', EmployerProfile, name='employer_profile'),
    path('TaxDetails/', TaxDetails, name='Tax_details'),
    path('employee_details/', EmployeeDetailsAPIView.as_view(), name='employee_details'),
    path('employee_details/<int:employee_id>/',EmployeeDetailsUpdateAPIView.as_view(), name='Employee_Details_UpdateAPIView'),
    path('employer-profile/<int:employer_id>/',EmployerProfileEditView.as_view(),name='Employer_Profile_UpdateAPIView'),
    path('upload/<int:employer_id>', PDFFileUploadView, name='upload_pdf'),
    path('getemployeedetails/<str:cid>/', get_employee_by_employer_id, name='employee-by-employer-id'),
    path('getemployerdetails/<int:employer_id>/', get_employer_details, name='employer-detail-by-employer-id'),
    path('DashboardData',get_dashboard_data, name='iwo_dashboard'),
    path('IWO_Data',insert_iwo_detail, name='iwo_pdf_data'),
    path('Department',DepartmentViewSet, name='Department'),
    path('Location',LocationViewSet, name='Location'),     
    path('EmployeeDelete/<int:employee_id>/<int:employer_id>/',EmployeeDeleteAPIView.as_view(), name='Employee-Delete-APIView'),
    path('TaxDelete/<int:tax_id>/<int:employer_id>/',TaxDeleteAPIView.as_view(), name='Tax-Delete-APIView'),
    path('DepartmentDelete/<int:department_id>/<int:employer_id>/',DepartmentDeleteAPIView.as_view(), name='Department-Delete-APIView'),
    path('LocationDelete/<int:location_id>/<int:employer_id>/',LocationDeleteAPIView.as_view(), name='Department-Delete-APIView'),
    path('ExportEmployees/<str:cid>/', export_employee_data, name='export-employee-data'),
    path('EmployeeImportView/<int:employer_id>/', EmployeeImportView.as_view(), name='Employee-Import-View'),
    path('logdata', LastFiveLogsView.as_view(), name=' Garnishment Calculation'),
    path('GetAllemployerdetail', EmployerProfileList.as_view(), name='employer-profile-list'),
    path('GetAllEmplloyeeDetail', EmployeeDetailsList.as_view(), name='employer-profile-list'),
    #path('GetSingleEmployee/<int:employer_id>/<int:employee_id>/', get_single_employee_details, name='get-single-employee-details'),
    path('password-reset', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset-confirm/<str:token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('setting/<int:employer_id>/',GETSettingDetails.as_view(), name='Get Setting'),
    path('POSTsetting/',SettingPostAPI, name='POST Setting'),
    path('call-count/', APICallCountView.as_view(), name='api-call-count'),
    path('state_tax_case/',StateTaxView.as_view(), name='state_tax_case'),
    path('multiple_garnishment_case/',multiple_case_calculation, name='state_tax_case'),
    path('multiple_garnishment_result/<str:employer_id>/<str:employee_id>/',get_multiple_garnishment_case_result.as_view(), name='state_tax_case'),
    #path('ChildSupportBatchResult/<str:batch_id>', ChildSupportGarnishmentBatchResult.as_view(), name='Calculation Data'),
    path('upsert-employees-details/', import_employees_api, name='import_employees_api'),
    path('upsert-company-details/', upsert_company_details_api, name='upsert_company_details_api')
    

]



