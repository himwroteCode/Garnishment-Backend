from django.urls import path
from ..views import *
from ..views.views import *
from django.urls import include, path
from rest_framework import routers
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
    path('employee_details/', EmployeeDetails, name='employee_details'),
    path('employee_details/<int:employee_id>/',EmployeeDetailsUpdateAPIView.as_view(), name='Employee_Details_UpdateAPIView'),
    path('employer-profile/<int:employer_id>/',EmployerProfileEditView.as_view(),name='Employer_Profile_UpdateAPIView'),
    path('upload/<int:employer_id>', PDFFileUploadView, name='upload_pdf'),
    path('getemployeedetails/<int:employer_id>/', get_employee_by_employer_id, name='employee-by-employer-id'),
    path('getemployerdetails/<int:employer_id>/', get_employer_details, name='employer-detail-by-employer-id'),
    path('DashboardData',get_dashboard_data, name='iwo_dashboard'),
    path('IWO_Data',insert_iwo_detail, name='iwo_pdf_data'),
    path('Department',DepartmentViewSet, name='Department'),
    path('Location',LocationViewSet, name='Location'),  
    path('GetTaxDetails/<int:employer_id>/',get_Tax_details, name='GetTaxDetails'),  
    path('GetDepartmentDetails/<int:employer_id>/',get_Department_details, name='GetDepartmentDetails'), 
    path('GetLocationDetails/<int:employer_id>/',get_Location_details, name='Get-Location-Details'),    
    path('EmployeeDelete/<int:employee_id>/<int:employer_id>/',EmployeeDeleteAPIView.as_view(), name='Employee-Delete-APIView'),
    path('TaxDelete/<int:tax_id>/<int:employer_id>/',TaxDeleteAPIView.as_view(), name='Tax-Delete-APIView'),
    path('DepartmentDelete/<int:department_id>/<int:employer_id>/',DepartmentDeleteAPIView.as_view(), name='Department-Delete-APIView'),
    path('LocationDelete/<int:location_id>/<int:employer_id>/',LocationDeleteAPIView.as_view(), name='Department-Delete-APIView'),
    path('ExportEmployees/<int:employer_id>/', export_employee_data, name='export-employee-data'),
    # path('EmployeeImportView/<int:employer_id>/', EmployeeImportView.as_view(), name='Employee-Import-View'),
    path('TaxDetailsUpdate/<int:tax_id>/', TaxDetailsUpdateAPIView.as_view(), name='Tax-Details-Update-APIView'),
    path('DepartmentDetailsUpdate/<int:department_id>/', DepartmentDetailsUpdateAPIView.as_view(), name='Tax-Details-Update-APIView'),
    path('LocatiionDetailsUpdate/<int:location_id>/', LocatiionDetailsUpdateAPIView.as_view(), name='Department-Details-Update-APIView'),
    path('logdata', LastFiveLogsView.as_view(), name=' Garnishment Calculation'),
    path('GetAllemployerdetail', EmployerProfileList.as_view(), name='employer-profile-list'),
    path('GetAllEmplloyeeDetail', EmployeeDetailsList.as_view(), name='employer-profile-list'),
    path('GetAllTaxDetail', TaxDetailsList.as_view(), name='Get-All-Tax-Detail'),
    path('GetAllDepartmentDetail', DepartmentDetailsList.as_view(), name='employer-profile-list'),
    path('GetAllLocationDetail', LocationDetailsList.as_view(), name='employer-profile-list'),
    path('GetSingleEmployee/<int:employer_id>/<int:employee_id>/', get_single_employee_details, name='get-single-employee-details'),
    path('GetSingleTax/<int:employer_id>/<int:tax_id>/', get_single_tax_details, name='get_single_tax_details'),
    path('GetSingleLocation/<int:employer_id>/<int:location_id>/', get_single_location_details, name='get_single_location_details'),
    path('GetSingleDepartment/<int:employer_id>/<int:department_id>/', get_single_department_details, name='get_single_department_details'),
    path('password-reset', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset-confirm/<str:token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('setting/<int:employer_id>/',GETSettingDetails.as_view(), name='Get Setting'),
    path('POSTsetting/',SettingPostAPI, name='POST Setting'),
    path('GETallcalculationresult/<int:employer_id>/',GETallcalculationresult.as_view(), name='Get_Multiple_Student_Loan_Case_Data'),
    path('call-count/', APICallCountView.as_view(), name='api-call-count'),
    path('state_tax_case/',state_tax, name='state_tax_case'),
    path('multiple_garnishment_case/',multiple_case_calculation, name='state_tax_case'),
    path('multiple_garnishment_result/<str:employer_id>/<str:employee_id>/',get_multiple_garnishment_case_result.as_view(), name='state_tax_case')

]





