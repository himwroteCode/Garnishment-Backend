from django.urls import path
from . import views
from .views import EmployerProfileEditView,TaxDetails,EmployeeDetailsUpdateAPIView,DepartmentViewSet,get_Tax_details,EmployeeDeleteAPIView,EmployeeImportView,TaxDetailsUpdateAPIView,LocatiionDetailsUpdateAPIView,DepartmentDetailsUpdateAPIView,Gcalculations,LastFiveLogsView,TaxDeleteAPIView,LocationDeleteAPIView,DepartmentDeleteAPIView,EmployerProfileList,EmployeeDetailsList,TaxDetailsList,DepartmentDetailsList,LocationDetailsList,PDFFileUploadView,PasswordResetRequestView,PasswordResetConfirmView
from django.urls import include, path
from rest_framework import routers


urlpatterns = [
    path("register", views.register, name="register"),
    path("login",views.login, name="login"),    
    path('employer-profile/', views.EmployerProfile, name='employer_profile'),
    path('TaxDetails/', views.TaxDetails, name='Tax_details'),
    path('employee_details/', views.EmployeeDetails, name='employee_details'),
    path('employee_details/<int:employee_id>/',EmployeeDetailsUpdateAPIView.as_view(), name='Employee_Details_UpdateAPIView'),
    path('employer-profile/<int:employer_id>/',EmployerProfileEditView.as_view(),name='Employer_Profile_UpdateAPIView'),
    path('upload/<int:employer_id>', views.PDFFileUploadView, name='upload_pdf'),
    path('getemployeedetails/<int:employer_id>/', views.get_employee_by_employer_id, name='employee-by-employer-id'),
    path('getemployerdetails/<int:employer_id>/', views.get_employer_details, name='employer-detail-by-employer-id'),
    path('DashboardData',views.get_dashboard_data, name='iwo_dashboard'),
    path('IWO_Data',views.insert_iwo_detail, name='iwo_pdf_data'),
    path('Department',views.DepartmentViewSet, name='Department'),
    path('Location',views.LocationViewSet, name='Location'),  
    path('GetTaxDetails/<int:employer_id>/',views.get_Tax_details, name='GetTaxDetails'),  
    path('GetDepartmentDetails/<int:employer_id>/',views.get_Department_details, name='GetDepartmentDetails'), 
    path('GetLocationDetails/<int:employer_id>/',views.get_Location_details, name='Get-Location-Details'),    
    path('EmployeeDelete/<int:employee_id>/<int:employer_id>/',EmployeeDeleteAPIView.as_view(), name='Employee-Delete-APIView'),
    path('TaxDelete/<int:tax_id>/<int:employer_id>/',TaxDeleteAPIView.as_view(), name='Tax-Delete-APIView'),
    path('DepartmentDelete/<int:department_id>/<int:employer_id>/',DepartmentDeleteAPIView.as_view(), name='Department-Delete-APIView'),
    path('LocationDelete/<int:location_id>/<int:employer_id>/',LocationDeleteAPIView.as_view(), name='Department-Delete-APIView'),
    path('ExportEmployees/<int:employer_id>/', views.export_employee_data, name='export-employee-data'),
    path('EmployeeImportView/<int:employer_id>/', EmployeeImportView.as_view(), name='Employee-Import-View'),
    path('TaxDetailsUpdate/<int:tax_id>/', TaxDetailsUpdateAPIView.as_view(), name='Tax-Details-Update-APIView'),
    path('DepartmentDetailsUpdate/<int:department_id>/', DepartmentDetailsUpdateAPIView.as_view(), name='Tax-Details-Update-APIView'),
    path('LocatiionDetailsUpdate/<int:location_id>/', LocatiionDetailsUpdateAPIView.as_view(), name='Department-Details-Update-APIView'),
    path('CalculationDataView', views.CalculationDataView, name='Calculation Data'),
    path('Gcalculations/<int:employer_id>/<int:employee_id>/', Gcalculations.as_view(), name='Gcalculations'),
    path('logdata', LastFiveLogsView.as_view(), name=' Garnishment Calculation'),
    path('GetAllemployerdetail', EmployerProfileList.as_view(), name='employer-profile-list'),
    path('GetAllEmplloyeeDetail', EmployeeDetailsList.as_view(), name='employer-profile-list'),
    path('GetAllTaxDetail', TaxDetailsList.as_view(), name='employer-profile-list'),
    path('GetAllDepartmentDetail', DepartmentDetailsList.as_view(), name='employer-profile-list'),
    path('GetAllLocationDetail', LocationDetailsList.as_view(), name='employer-profile-list'),
    path('GetSingleEmployee/<int:employer_id>/<int:employee_id>/', views.get_single_employee_details, name='get-single-employee-details'),
    path('GetSingleTax/<int:employer_id>/<int:tax_id>/', views.get_single_tax_details, name='get_single_tax_details'),
    path('GetSingleLocation/<int:employer_id>/<int:location_id>/', views.get_single_location_details, name='get_single_location_details'),
    path('GetSingleDepartment/<int:employer_id>/<int:department_id>/', views.get_single_department_details, name='get_single_department_details'),
    path('password-reset', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset-confirm/<str:token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

]



