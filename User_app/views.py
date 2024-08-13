from rest_framework import status
from django.contrib import messages
from auth_project.config import ccpa_limit
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Employer_Profile,federal_case_result,Employee_Details,married_filing_sepearte_return,married_filing_joint_return,head_of_household,Tax_details,single_filing_status,federal_loan_case_data,Department,student_loan_data,Location,single_student_loan_result,multiple_student_loan_result,Garcalculation_data,CalculationResult,LogEntry,IWO_Details_PDF,IWOPDFFile,Calculation_data_results,application_activity
from django.contrib.auth import authenticate, login as auth_login ,get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Count
from django.shortcuts import get_object_or_404
import json
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
import pandas as pd
from django.contrib.auth.hashers import make_password
from rest_framework.generics import DestroyAPIView ,RetrieveUpdateAPIView
from rest_framework import viewsets ,generics
from .serializers import EmployerProfileSerializer ,ResultSerializer,federal_case_result_Serializer,GetEmployerDetailsSerializer,SingleStudentLoanSerializer,MultipleStudentLoanSerializer,EmployeeDetailsSerializer,DepartmentSerializer, LocationSerializer,TaxSerializer,LogSerializer,PDFFileSerializer,PasswordResetConfirmSerializer,PasswordResetRequestSerializer
from django.http import HttpResponse
from .forms import PDFUploadForm
from django.db import transaction
from rest_framework.decorators import api_view
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken ,AccessToken, TokenError
import csv
from rest_framework.views import APIView

@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON',
                'status code': status.HTTP_400_BAD_REQUEST
            })

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return JsonResponse({
                'success': False,
                'message': 'Email and password are required',
                'status code': status.HTTP_400_BAD_REQUEST
            })

        try:
            user = Employer_Profile.objects.get(email=email)
        except Employer_Profile.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials',
                'status code': status.HTTP_400_BAD_REQUEST
            })

        if check_password(password, user.password):
            auth_login(request, user)
            user_data = {
                'employer_id': user.employer_id,
                'username': user.username,
                'name': user.employer_name,
                'email': user.email,
            }
            try:
                refresh = RefreshToken.for_user(user)

                employee = get_object_or_404(Employer_Profile, employer_name=user.employer_name, employer_id=user.employer_id)
                application_activity.objects.create(
                action='Employer Login',
                details=f'Employer {employee.employer_name} Login successfully with ID {employee.employer_id}. '
            )
                response_data = {
                    'success': True,
                    'message': 'Login successful',
                    'user_data': user_data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'expire_time' : refresh.access_token.payload['exp'],
                    'status code': status.HTTP_200_OK,
                }
                return JsonResponse(response_data)
            except AttributeError as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error generating tokens: {str(e)}',
                    'status code': status.HTTP_500_INTERNAL_SERVER_ERROR
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials',
                'status code': status.HTTP_400_BAD_REQUEST
            })
    else:
        return JsonResponse({
            'message': 'Please use POST method for login',
            'status code': status.HTTP_400_BAD_REQUEST
        })


@csrf_exempt
def register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON', 'status code': status.HTTP_400_BAD_REQUEST})

        employer_name = data.get('name')
        username = data.get('username')
        email = data.get('email')
        password1 = data.get('password1')
        password2 = data.get('password2')
        street_name = data.get('street_name')
        federal_employer_identification_number = data.get('federal_employer_identification_number')
        city = data.get('city')
        state = data.get('state')
        country = data.get('country')
        zipcode = data.get('zipcode')
        number_of_employees = data.get('number_of_employees')
        department = data.get('department')
        location = data.get('location')

        if not all([employer_name, username, email, password1, password2]):
            return JsonResponse({'error': 'All required fields are mandatory', 'status_code': status.HTTP_400_BAD_REQUEST})

        if password1 != password2:
            return JsonResponse({'error': 'Passwords do not match', 'status_code': status.HTTP_400_BAD_REQUEST})

        if not (len(password1) >= 8 and any(c.isupper() for c in password1) and any(c.islower() for c in password1) and any(c.isdigit() for c in password1) and any(c in '!@#$%^&*()_+' for c in password1)):
            return JsonResponse({'error': 'Password must meet complexity requirements', 'status code': status.HTTP_400_BAD_REQUEST})

        User = get_user_model()
        if Employer_Profile.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already used', 'status code': status.HTTP_400_BAD_REQUEST})
        if Employer_Profile.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email taken', 'status code': status.HTTP_400_BAD_REQUEST})

        try:
            user = Employer_Profile.objects.create(
                employer_name=employer_name, 
                email=email, 
                username=username, 
                password=make_password(password1),  # Hash the password
                federal_employer_identification_number=federal_employer_identification_number,
                street_name=street_name, 
                city=city, 
                state=state, 
                country=country, 
                zipcode=zipcode, 
                number_of_employees=number_of_employees, 
                department=department, 
                location=location
            )
            user.save()

            employee = get_object_or_404(Employer_Profile, employer_id=user.employer_id)
            application_activity.objects.create(
                action='Employer Register',
                details=f'Employer {employee.employer_name} registered successfully with ID {employee.employer_id}.'
            )
            return JsonResponse({'message': 'Successfully registered', 'status code': status.HTTP_201_CREATED})
        except Exception as e:
            return JsonResponse({'error': str(e), 'status code': status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return JsonResponse({'message': 'Please use POST method for registration', 'status code': status.HTTP_400_BAD_REQUEST})
    

@csrf_exempt
def EmployerProfile(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if len(str(data['federal_employer_identification_number'])) != 9:
                return JsonResponse({'error': 'Federal Employer Identification Number must be exactly 9 characters long', 'status_code':status.HTTP_400_BAD_REQUEST})
            
            if Employer_Profile.objects.filter(email=data['email']).exists():
                return JsonResponse({'error': 'Email already registered', 'status_code':status.HTTP_400_BAD_REQUEST})
            
            user = Employer_Profile.objects.create(**data)

            employee = get_object_or_404(Employer_Profile, employer_id=user.employer_id)
            LogEntry.objects.create(
                action='Employer details added',
                details=f'Employer details with ID {employee.employer_id}'
            )
            return JsonResponse({'message': 'Employer Detail Successfully Registered', "status code" :status.HTTP_201_CREATED})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
    else:
        return JsonResponse({'message': 'Please use POST method','status code':status.HTTP_400_BAD_REQUEST})


@csrf_exempt
def EmployeeDetails(request):
    if request.method == 'POST' :
        try:
            data = json.loads(request.body)
            required_fields = ['employee_name','department', 'pay_cycle', 'number_of_garnishment', 'location']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            
            if missing_fields:
                return JsonResponse({'error': f'Required fields are missing: {", ".join(missing_fields)}', 'status_code':status.HTTP_400_BAD_REQUEST})
            
            # if Employee_Details.objects.filter(employee_id=data['employee_id']).exists():
            #     return JsonResponse({'error': 'Employee ID already exists', 'status_code':status.HTTP_400_BAD_REQUEST})
 
            user=Employee_Details.objects.create(**data)
            user.save()

            employee = get_object_or_404(Employee_Details, employee_id=user.employee_id)
            LogEntry.objects.create(
                action='Employee details added',
                details=f'Employee details added successfully with employee ID {employee.employee_id}'
            )
            return JsonResponse({'message': 'Employee Details Successfully Registered', 'status code':status.HTTP_201_CREATED})
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format','status code':status.HTTP_400_BAD_REQUEST})
        
        except Exception as e:
            return JsonResponse({'error': str(e), "status code":status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return JsonResponse({'message': 'Please use POST method ', 'status code':status.HTTP_400_BAD_REQUEST})



@csrf_exempt
def TaxDetails(request):
    if request.method == 'POST' :
        try:
            data = json.loads(request.body)
            required_fields = ['state_tax','employer_id','fedral_income_tax','social_and_security','medicare_tax']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            
            if missing_fields:
                return JsonResponse({'error': f'Required fields are missing: {", ".join(missing_fields)}', 'status code':status.HTTP_400_BAD_REQUEST})
            
            user=Tax_details.objects.create(**data)
            user.save()
            # employee = get_object_or_404(Tax_details, tax_id=user.tax_id)
            LogEntry.objects.create(
                action='Tax details added',
                details=f'Tax details added successfully for tax ID {user.tax_id}'
            )
            return JsonResponse({'message': 'Tax Details Successfully Registered', 'status code':status.HTTP_200_OK})
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format','status code':status.HTTP_400_BAD_REQUEST})
        
        except Exception as e:
            return JsonResponse({'error': str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return JsonResponse({'message': 'Please use POST method ', 'status code':status.HTTP_400_BAD_REQUEST})


@api_view(['GET'])
def get_Location_Deatils(request, employer_id):
    employees=LocationSerializer.objects.filter(employer_id=employer_id)
    if employees.exists():
        try:
            serializer = LocationSerializer(employees, many=True)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'status code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)


        except Tax_details.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status code':status.HTTP_404_NOT_FOUND})



#for Updating the Employer Profile data
class EmployerProfileEditView(RetrieveUpdateAPIView):
    queryset = Employer_Profile.objects.all()
    serializer_class = EmployerProfileSerializer
    lookup_field = 'employer_id'
    @csrf_exempt
    def put(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data
    
            # Check for missing fields
            required_fields = ['employer_name', 'street_name', 'federal_employer_identification_number', 'city', 'state', 'country', 'zipcode', 'email', 'number_of_employees', 'department', 'location']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return JsonResponse({'error': f'Required fields are missing: {", ".join(missing_fields)}', 'status_code':status.HTTP_400_BAD_REQUEST})
    
            # Validate length of federal_employer_identification_number
            if 'federal_employer_identification_number' in data and len(str(data['federal_employer_identification_number'])) != 9:
                return JsonResponse({'error': 'Federal Employer Identification Number must be exactly 9 characters long', 'status_code':status.HTTP_400_BAD_REQUEST})
    
            # Validate email if it's being updated
            if 'email' in data and Employer_Profile.objects.filter(email=data['email']).exclude(employer_id=instance.employer_id).exists():
                return JsonResponse({'error': 'Email already registered', 'status_code':status.HTTP_400_BAD_REQUEST})
    
            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            LogEntry.objects.create(
                    action='Employer details Updated',
                    details=f'Employer details Updated successfully with ID {instance.employer_id}'
                )
    
            response_data = {
                'success': True,
                'message': 'Data Updated successfully',
                'status code': status.HTTP_200_OK
            }
        except Exception as e:
            return JsonResponse({'error': str(e), "status code":status.HTTP_500_INTERNAL_SERVER_ERROR}) 
        return JsonResponse(response_data)
    
#update employee Details
@method_decorator(csrf_exempt, name='dispatch')
class EmployeeDetailsUpdateAPIView(RetrieveUpdateAPIView):
    queryset = Employee_Details.objects.all()
    serializer_class = EmployeeDetailsSerializer
    lookup_field = 'employee_id'  
    def put(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            LogEntry.objects.create(
            action='Employee details Updated',
            details=f'Employee details Updated successfully for Employee ID {instance.employee_id}'
                )
            response_data = {
                    'success': True,
                    'message': 'Data Updated successfully',
                    'status code': status.HTTP_200_OK}
        except Exception as e:
            return JsonResponse({'error': str(e), "status code":status.HTTP_500_INTERNAL_SERVER_ERROR}) 
        return JsonResponse(response_data)


#update Tax Details
@method_decorator(csrf_exempt, name='dispatch')
class TaxDetailsUpdateAPIView(RetrieveUpdateAPIView):
    queryset = Tax_details.objects.all()
    serializer_class = TaxSerializer
    lookup_field = 'tax_id'  
    def put(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            response_data = {
                    'success': True,
                    'message': 'Data Updated successfully',
                    'status code': status.HTTP_200_OK}
            LogEntry.objects.create(
            action='Tax details Updated',
            details=f'Tax details Updated successfully for tax ID {instance.tax_id}'
                )
        except Exception as e:
            return JsonResponse({'error': str(e), "status code":status.HTTP_500_INTERNAL_SERVER_ERROR}) 
        return JsonResponse(response_data)


#update Location Details
@method_decorator(csrf_exempt, name='dispatch')
class LocatiionDetailsUpdateAPIView(RetrieveUpdateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    lookup_field = 'location_id'  
    def put(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            LogEntry.objects.create(
            action='Location details Updated',
            details=f'LOcation details Updated successfully added for Location ID {instance.location_id}'
                )
            response_data = {
                    'success': True,
                    'message': 'Data Updated successfully',
                    'status code': status.HTTP_200_OK}
        except Exception as e:
            return JsonResponse({'error': str(e), "status code":status.HTTP_500_INTERNAL_SERVER_ERROR}) 
        return JsonResponse(response_data)
    

#update Department Details
@method_decorator(csrf_exempt, name='dispatch')
class DepartmentDetailsUpdateAPIView(RetrieveUpdateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    lookup_field = 'department_id'  
    def put(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            LogEntry.objects.create(
            action='Department details Updated',
            details=f'Department details has been successfully Updated for Department ID {instance.department_id}')
            response_data = {
                    'success': True,
                    'message': 'Data Updated successfully',
                    'status code': status.HTTP_200_OK}
        except Exception as e:
            return JsonResponse({'error': str(e), "status code":status.HTTP_500_INTERNAL_SERVER_ERROR}) 
        return JsonResponse(response_data)


#PDF upload view
@transaction.atomic
def PDFFileUploadView(request, employer_id):
    try:
        if request.method == 'POST':
            form = PDFUploadForm(request.POST, request.FILES)
            if form.is_valid():
                pdf_file = form.cleaned_data['pdf_file']
                pdf_name = pdf_file.name
    
                # Store PDF file data in the database with the correct model fields
                pdf_record = IWOPDFFile(pdf_name=pdf_name, pdf=pdf_file, employer_id=employer_id)
                pdf_record.save()
                LogEntry.objects.create(
                action='IWO PDF file Uploaded',
                details=f'IWO PDF file has been successfully Uploaded for Employer ID {employer_id}')
                return HttpResponse("File uploaded successfully.")      
        else:
            form = PDFUploadForm()
    except Exception as e:
        return JsonResponse({'error': str(e), status:status.HTTP_500_INTERNAL_SERVER_ERROR})  
    
    return render(request, 'upload_pdf.html', {'form': form})



#Get Employer Details on the bases of Employer_ID
@api_view(['GET'])
def get_employee_by_employer_id(self, employer_id):
    employees=Employee_Details.objects.filter(employer_id=employer_id)
    instance = self.get_object()
    if employees.exists():
        try:
            serializer = EmployeeDetailsSerializer(employees, many=True)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'status code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)

        except Employee_Details.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status code':status.HTTP_404_NOT_FOUND})



@api_view(['GET'])
def get_Tax_details(request,employer_id):
    employees=Tax_details.objects.filter(employer_id=employer_id)
    if employees.exists():
        try:
            serializer = TaxSerializer(employees, many=True)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'status code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)

        except Tax_details.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status code':status.HTTP_404_NOT_FOUND})


@api_view(['GET'])
def get_Location_details(request, employer_id):
    employees=Location.objects.filter(employer_id=employer_id)
    if employees.exists():
        try:
            serializer = LocationSerializer(employees)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'status code': status.HTTP_200_OK,
                    'data' : serializer.data}
            return JsonResponse(response_data)
        except Tax_details.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status code':status.HTTP_404_NOT_FOUND})


@api_view(['GET'])
def get_Department_details(request, employer_id):
    employees=Department.objects.filter(employer_id=employer_id)
    if employees.exists():
        try:
            serializer = DepartmentSerializer(employees, many=True)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'status code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)
        except Tax_details.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status code':status.HTTP_404_NOT_FOUND})



@api_view(['GET'])
def get_employee_by_employer_id(request, employer_id):
    employees=Employee_Details.objects.filter(employer_id=employer_id)
    if employees.exists():
        try:
            serializer = EmployeeDetailsSerializer(employees, many=True)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'status code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)
        except Employee_Details.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status code':status.HTTP_404_NOT_FOUND})


#Get Employer Details from employer ID
@api_view(['GET'])
def get_employer_details(request, employer_id):
    employees=Employer_Profile.objects.filter(employer_id=employer_id)
    if employees.exists():
        try:
            serializer = GetEmployerDetailsSerializer(employees, many=True)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'status code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)
        except Employer_Profile.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status code':status.HTTP_404_NOT_FOUND})
    


@csrf_exempt
def insert_iwo_detail(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            employer_id = data.get('employer_id')
            employee_id = data.get('employee_id')
            IWO_Status = data.get('IWO_Status')

            # Validate required fields
            if employer_id is None or employee_id is None or IWO_Status is None:
                return JsonResponse({'error': 'Missing required fields','code':status.HTTP_400_BAD_REQUEST})

            # Create a new IWO_Details_PDF instance and save it to the database
            iwo_detail = IWO_Details_PDF(
                employer_id=employer_id,
                employee_id=employee_id,
                IWO_Status=IWO_Status
            )
            iwo_detail.save()
            return JsonResponse({'message': 'IWO detail inserted successfully', 'code' :status.HTTP_201_CREATED})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON', 'status_code':status.HTTP_400_BAD_REQUEST})
        except Exception as e:
            return JsonResponse({'error': str(e),'status code': status.HTTP_500_INTERNAL_SERVER_ERROR})

    return JsonResponse({'error': 'Invalid request method', 'status code': status.HTTP_405_METHOD_NOT_ALLOWED})


@csrf_exempt
def get_dashboard_data(request):
    try:
        total_iwo = IWO_Details_PDF.objects.count()
    
        employees_with_single_iwo = IWO_Details_PDF.objects.values('employee_id').annotate(iwo_count=Count('employee_id')).filter(iwo_count=1).count()
    
        employees_with_multiple_iwo = IWO_Details_PDF.objects.values('employee_id').annotate(iwo_count=Count('employee_id')).filter(iwo_count__gt=1).count()
    
        active_employees = IWO_Details_PDF.objects.filter(IWO_Status='active').count()
    
        data = {
            'Total_IWO': total_iwo,
            'Employees_with_Single_IWO': employees_with_single_iwo,
            'Employees_with_Multiple_IWO': employees_with_multiple_iwo,
            'Active_employees': active_employees,
        }
    except Exception as e:
        return JsonResponse({'error': str(e), "status code":status.HTTP_500_INTERNAL_SERVER_ERROR}) 
    response_data = {
        'success': True,
        'message': 'Data Get successfully',
        'status code': status.HTTP_200_OK,
        'data' : data}
    return JsonResponse(response_data)


@csrf_exempt
def DepartmentViewSet(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            required_fields = ['department_name', 'employer_id']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return JsonResponse({'error': f'Required fields are missing: {", ".join(missing_fields)}','status_code':status.HTTP_400_BAD_REQUEST})
            if Department.objects.filter(department_name=data['department_name']).exists():
                 return JsonResponse({'error': 'Department already exists', 'status_code':status.HTTP_400_BAD_REQUEST})            
            user = Department.objects.create(**data)
            LogEntry.objects.create(
            action='Department details added',
            details=f'Department details added successfully for Department ID{user.department_id}'
            ) 
            return JsonResponse({'message': 'Department Details Successfully Registered'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return JsonResponse({'error': str(e), "status code":status.HTTP_500_INTERNAL_SERVER_ERROR}) 
    else:
        return JsonResponse({'message': 'Please use POST method','status code':status.HTTP_400_BAD_REQUEST})



@csrf_exempt
def LocationViewSet(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            required_fields = ['employer_id','state','city']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return JsonResponse({'error': f'Required fields are missing: {", ".join(missing_fields)}','status_code':status.HTTP_400_BAD_REQUEST})
            user = Location.objects.create(**data)
            LogEntry.objects.create(
            action='Location details added',
            details=f'Location details added successfully for Location ID{user.location_id}'
            ) 
            return JsonResponse({'message': 'Location Details Successfully Registered', "status code" :status.HTTP_201_CREATED})
        except Exception as e:
            return JsonResponse({'error': str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR}) 
    else:
        return JsonResponse({'message': 'Please use POST method','status code':status.HTTP_400_BAD_REQUEST})
    


# For  Deleting the Employee Details
@method_decorator(csrf_exempt, name='dispatch')
class EmployeeDeleteAPIView(DestroyAPIView):
    queryset = Employee_Details.objects.all()
    lookup_field = 'employee_id'

    def get_object(self):
        employee_id = self.kwargs.get('employee_id')
        employer_id = self.kwargs.get('employer_id')
        return Employee_Details.objects.get(employee_id=employee_id, employer_id=employer_id)
    
    @csrf_exempt
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        LogEntry.objects.create(
            action='Employee details Deleted',
            details=f'Employee details Deleted successfully with Employee ID {instance.employee_id} and Employer ID {instance.employer_id}'
        )
        response_data = {
            'success': True,
            'message': 'Location Data Deleted successfully',
            'status code': status.HTTP_200_OK
        }
        return JsonResponse(response_data)

        
   
# For Deleting the Tax Details
@method_decorator(csrf_exempt, name='dispatch')
class TaxDeleteAPIView(DestroyAPIView):
    queryset = Tax_details.objects.all()
    lookup_field = 'tax_id'
    @csrf_exempt
    def get_object(self):
        tax_id = self.kwargs.get('tax_id')
        employer_id = self.kwargs.get('employer_id')
        return Tax_details.objects.get(tax_id=tax_id, employer_id=employer_id)
    
    @csrf_exempt
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        LogEntry.objects.create(
        action='Tax details Deleted',
        details=f'Tax details Deleted successfully with ID {instance.tax_id} and Employer ID {instance.employer_id}'
            ) 
        response_data = {
                'success': True,
                'message': 'Tax Data Deleted successfully',
                'status code': status.HTTP_200_OK}
        return JsonResponse(response_data)
    

    

# For Deleting the Location Details
@method_decorator(csrf_exempt, name='dispatch')
class LocationDeleteAPIView(DestroyAPIView):
    queryset = Location.objects.all()
    lookup_field = 'location_id'
    @csrf_exempt
    def get_object(self):
        location_id = self.kwargs.get('location_id')
        employer_id = self.kwargs.get('employer_id')  
        return self.queryset.filter(location_id=location_id, employer_id=employer_id).first()  

    @csrf_exempt
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        LogEntry.objects.create(
            action='Location details Deleted',
            details=f'Location details Deleted successfully with ID {instance.location_id} and Employer ID {instance.employer_id}'
        )
        response_data = {
            'success': True,
            'message': 'Location Data Deleted successfully',
            'status code': status.HTTP_200_OK
        }
        return JsonResponse(response_data)


# For Deleting the Department Details
@method_decorator(csrf_exempt, name='dispatch')
class DepartmentDeleteAPIView(DestroyAPIView):
    queryset = Department.objects.all()
    lookup_field = 'department_id' 

    def get_object(self):
        department_id = self.kwargs.get('department_id')
        employer_id = self.kwargs.get('employer_id')  
        return self.queryset.filter(department_id=department_id, employer_id=employer_id).first()  
    
    @csrf_exempt
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        LogEntry.objects.create(
        action='Department details Deleted',
        details=f'Department details Deleted successfully with ID {instance.department_id} and Employer ID {instance.employer_id}'
            ) 
        response_data = {
                'success': True,
                'message': 'Department Data Deleted successfully',
                'status code': status.HTTP_200_OK}
        return JsonResponse(response_data)
    

# Export employee details into the csv
@api_view(['GET'])
def export_employee_data(request, employer_id):
    try:
        employees = Employee_Details.objects.filter(employer_id=employer_id)
        if not employees.exists():
            return JsonResponse({'detail': 'No employees found for this employer ID', 'status': status.HTTP_404_NOT_FOUND})

        serializer = EmployeeDetailsSerializer(employees, many=True)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="employees_{employer_id}.csv"'

        writer = csv.writer(response)
        writer.writerow(['employer_id', 'employee_id', 'employee_name', 'department', 'net_pay', 'minimun_wages', 'pay_cycle', 'number_of_garnishment', 'location'])

        for employee in serializer.data:
            writer.writerow([
                employee.get('employer_id', ''),
                employee.get('employee_id', ''),
                employee.get('employee_name', ''),
                employee.get('department', ''),
                employee.get('net_pay', ''),
                employee.get('minimum_wages', ''),
                employee.get('pay_cycle', ''),
                employee.get('number_of_garnishment ', ''),
                employee.get('location', '')
            ])
        return response
    except Exception as e:
        return JsonResponse({'detail': str(e), 'status code ': status.HTTP_500_INTERNAL_SERVER_ERROR})



#Import employee details using the Excel file
class EmployeeImportView(APIView):
    def post(self, request, employer_id):
        try:
            if 'file' not in request.FILES:
                return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
            
            file = request.FILES['file']
            file_name = file.name
    
            # Check the file extension
            if file_name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file_name.endswith(('.xlsx','.xls', '.xlsm', '.xlsb', '.odf', '.ods','.odt')):
                df = pd.read_excel(file)
            else:
                return Response({"error": "Unsupported file format. Please upload a CSV or Excel file."}, status=status.HTTP_400_BAD_REQUEST)
            df['employer_id'] = employer_id        
            employees = []
            for _, row in df.iterrows():
                employee_data={
                'employee_name':row['employee_name'],
                'department':row['department'],
                'pay_cycle':row['pay_cycle'],
                'number_of_garnishment':row['number_of_garnishment'],
                'location':row['location'],
                'employer_id': row['employer_id'] 
                }
                # employer = get_object_or_404(Employee_Details, employer_id=employer_id)
    
                serializer = EmployeeDetailsSerializer(data=employee_data)
                if serializer.is_valid():
                    employees.append(serializer.save())   
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
            LogEntry.objects.create(
            action='Employee details Imported',
            details=f'Employee details Imported successfully using excel file with empployer ID {employer_id}')
        except Exception as e:
            return JsonResponse({'error': str(e), "status code":status.HTTP_500_INTERNAL_SERVER_ERROR}) 
        
        return Response({"message": "File processed successfully", "status code" :status.HTTP_201_CREATED})



@csrf_exempt
@api_view(['POST'])
def CalculationDataView(request):
    if request.method == 'POST':
        try:
            data = request.data
            required_fields = [
                'earnings', 'employee_name', 'garnishment_fees', 'minimum_wages', 'earnings',
                'arrears_greater_than_12_weeks', 'support_second_family', 'amount_to_withhold_child1'
                , 'arrears_amt_Child1'
                , 'state', 'number_of_arrears', 'order_id' ]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return Response({'error': f'Required fields are missing: {", ".join(missing_fields)}'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = Garcalculation_data.objects.create(**data)

            # Retrieve the employee, tax, and employer records
            employee = Employee_Details.objects.get(employee_id=data['employee_id'], employer_id=data['employer_id'])
            tax = Tax_details.objects.get(employer_id=data['employer_id'])
            employer = Employer_Profile.objects.get(employer_id=data['employer_id'])
            gdata = Garcalculation_data.objects.filter(employer_id=data['employer_id'], employee_id=data['employee_id']).order_by('-timestamp').first()

            # Extracting earnings and garnishment fees from gdata
            earnings = gdata.earnings
            garnishment_fees = gdata.garnishment_fees
            amount_to_withhold_child1 = gdata.amount_to_withhold_child1
            amount_to_withhold_child2 = gdata.amount_to_withhold_child2
            amount_to_withhold_child3 = gdata.amount_to_withhold_child3
            amount_to_withhold_child4 = gdata.amount_to_withhold_child4
            amount_to_withhold_child5 = gdata.amount_to_withhold_child5
            arrears_amt_Child1 = gdata.arrears_amt_Child1
            arrears_amt_Child2 = gdata.arrears_amt_Child2
            arrears_amt_Child3 = gdata.arrears_amt_Child3
            arrears_amt_Child3 = gdata.arrears_amt_Child4
            arrears_amt_Child3 = gdata.arrears_amt_Child5
            arrears_greater_than_12_weeks = gdata.arrears_greater_than_12_weeks
            support_second_family = gdata.support_second_family
            number_of_garnishment = employee.number_of_garnishment
            number_of_arrears = gdata.number_of_arrears
            state=gdata.state
            # Calculate the various taxes
            federal_income_tax_rate = tax.fedral_income_tax
            social_tax_rate = tax.social_and_security
            medicare_tax_rate = tax.medicare_tax
            state_tax_rate = tax.state_tax
            total_tax = federal_income_tax_rate + social_tax_rate + medicare_tax_rate + state_tax_rate
            disposable_earnings = round(earnings - total_tax, 2)

            # ccpa_limit=ccpa_limit(support_second_family,arrears_greater_than_12_weeks)
            # Calculate ccpa_limit based on conditions
            if support_second_family and arrears_greater_than_12_weeks:
                ccpa_limit = 0.55
            elif not support_second_family and not arrears_greater_than_12_weeks:
                ccpa_limit = 0.60
            elif not support_second_family and arrears_greater_than_12_weeks:
                ccpa_limit = 0.65
            else:
                ccpa_limit = 0.50

            # Calculate allowable disposable earnings
            allowable_disposable_earnings = round(disposable_earnings * ccpa_limit, 2)
            withholding_available = round(allowable_disposable_earnings - garnishment_fees, 2)
            other_garnishment_amount = round(disposable_earnings * 0.25, 2)

            # Federal Minimum Wage calculation
            fmw = 30 * 7.25
            Disposable_Income_minus_Minimum_Wage_rule = round(earnings - fmw, 2)
            Minimum_amt = min(Disposable_Income_minus_Minimum_Wage_rule, withholding_available)

            # Determine allocation method for garnishment
            if state in ["Alabama", "Arizona", "California", "Colorado", "Connecticut", "Florida", "Georgia", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"]:
                allocation_method_for_garnishment = "Divide Equally"
            elif state in ["Alaska", "Arkansas", "Delaware", "Hawaii", "Montana", "New York", "North Dakota", "South Dakota", "Wyoming"]:
                allocation_method_for_garnishment = "Pro Rate"

            # Determine the allowable garnishment amount
            if Minimum_amt <= 0:
                allowed_amount_for_garnishment = 0
            else:
                allowed_amount_for_garnishment = Minimum_amt
            amount_to_withhold = amount_to_withhold_child1 + amount_to_withhold_child2 + amount_to_withhold_child3

            if (allowed_amount_for_garnishment - amount_to_withhold) >= 0:
                amount_to_withhold_child1 = amount_to_withhold_child1
            elif allocation_method_for_garnishment == "Pro Rate":
                ratio = amount_to_withhold_child1 / amount_to_withhold
                amount_to_withhold_child1 = allowed_amount_for_garnishment * ratio
            elif amount_to_withhold_child1 > 0:
                amount_to_withhold_child1 = allowed_amount_for_garnishment / number_of_garnishment
            else:
                amount_to_withhold_child1 = 0

            if (allowed_amount_for_garnishment - amount_to_withhold) >= 0:
                amount_to_withhold_child2 = amount_to_withhold_child2
            elif allocation_method_for_garnishment == "Pro Rate":
                ratio = amount_to_withhold_child2 / amount_to_withhold
                amount_to_withhold_child2 = allowed_amount_for_garnishment * ratio
            elif amount_to_withhold_child2 > 0:
                amount_to_withhold_child2 = allowed_amount_for_garnishment / number_of_garnishment
            else:
                amount_to_withhold_child2 = 0

            if (allowed_amount_for_garnishment - amount_to_withhold) >= 0:
                amount_to_withhold_child3 = amount_to_withhold_child3
            elif allocation_method_for_garnishment == "Pro Rate":
                ratio = amount_to_withhold_child3 / amount_to_withhold
                amount_to_withhold_child3 = allowed_amount_for_garnishment * ratio
            elif amount_to_withhold_child3 > 0:
                amount_to_withhold_child3 = allowed_amount_for_garnishment / number_of_garnishment
            else:
                amount_to_withhold_child3 = 0
            
            if (allowed_amount_for_garnishment - amount_to_withhold) >= 0:
                amount_to_withhold_child4 = amount_to_withhold_child3
            elif allocation_method_for_garnishment == "Pro Rate":
                ratio = amount_to_withhold_child4 / amount_to_withhold
                amount_to_withhold_child4 = allowed_amount_for_garnishment * ratio
            elif amount_to_withhold_child4 > 0:
                amount_to_withhold_child4 = allowed_amount_for_garnishment / number_of_garnishment
            else:
                amount_to_withhold_child3 = 0

            if (allowed_amount_for_garnishment - amount_to_withhold) >= 0:
                amount_to_withhold_child5 = amount_to_withhold_child3
            elif allocation_method_for_garnishment == "Pro Rate":
                ratio = amount_to_withhold_child5/ amount_to_withhold
                amount_to_withhold_child5 = allowed_amount_for_garnishment * ratio
            elif amount_to_withhold_child5 > 0:
                amount_to_withhold_child5= allowed_amount_for_garnishment / number_of_garnishment
            else:
                amount_to_withhold_child5 = 0

            amount_to_withhold = amount_to_withhold_child1 + amount_to_withhold_child2 + amount_to_withhold_child3+amount_to_withhold_child4+amount_to_withhold_child5

            # Calculate the amount left for arrears
            if allowed_amount_for_garnishment > 0 and (allowed_amount_for_garnishment - amount_to_withhold) > 0:
                amount_left_for_arrears = round(allowed_amount_for_garnishment - amount_to_withhold, 2)
            else:
                amount_left_for_arrears = 0
            
            allocation_method_for_arrears=allocation_method_for_garnishment
            
            # Determine allowed amount for other garnishment
            allowed_child_support_arrear = arrears_amt_Child1 + arrears_amt_Child2 + arrears_amt_Child3+amount_to_withhold_child4+amount_to_withhold_child5

            if (amount_left_for_arrears - allowed_child_support_arrear) >= 0:
                arrears_amt_Child1 = arrears_amt_Child1
            elif allocation_method_for_arrears == "Pro Rate":
                ratio = arrears_amt_Child1 / allowed_child_support_arrear
                arrears_amt_Child1 = amount_left_for_arrears * ratio
            elif amount_left_for_arrears > 0:
                arrears_amt_Child1 = amount_left_for_arrears / number_of_arrears
            else:
                arrears_amt_Child1 = 0

            if (amount_left_for_arrears - allowed_child_support_arrear) >= 0:
                arrears_amt_Child2 = arrears_amt_Child2
            elif allocation_method_for_arrears == "Pro Rate":
                ratio = arrears_amt_Child2 / allowed_child_support_arrear
                arrears_amt_Child2 = amount_left_for_arrears * ratio
            elif amount_left_for_arrears > 0:
                arrears_amt_Child2 = amount_left_for_arrears / number_of_arrears
            else:
                arrears_amt_Child2 = 0

            if (amount_left_for_arrears - allowed_child_support_arrear) >= 0:
                arrears_amt_Child3 = arrears_amt_Child3
            elif allocation_method_for_arrears == "Pro Rate":
                ratio = arrears_amt_Child3 / allowed_child_support_arrear
                arrears_amt_Child3 = amount_left_for_arrears * ratio
            elif amount_left_for_arrears > 0:
                arrears_amt_Child3 = amount_left_for_arrears / number_of_arrears
            else:
                arrears_amt_Child3 = 0
            
            if (amount_left_for_arrears - allowed_child_support_arrear) >= 0:
                arrears_amt_Child4 = arrears_amt_Child3
            elif allocation_method_for_arrears == "Pro Rate":
                ratio = arrears_amt_Child4 / allowed_child_support_arrear
                arrears_amt_Child3 = amount_left_for_arrears * ratio
            elif amount_left_for_arrears > 0:
                arrears_amt_Child4 = amount_left_for_arrears / number_of_arrears
            else:
                arrears_amt_Child4 = 0

            if (amount_left_for_arrears - allowed_child_support_arrear) >= 0:
                arrears_amt_Child5 = arrears_amt_Child3
            elif allocation_method_for_arrears == "Pro Rate":
                ratio = arrears_amt_Child5 / allowed_child_support_arrear
                arrears_amt_Child5 = amount_left_for_arrears * ratio
            elif amount_left_for_arrears > 0:
                arrears_amt_Child5 = amount_left_for_arrears / number_of_arrears
            else:
                arrears_amt_Child5 = 0

            if (amount_left_for_arrears - allowed_child_support_arrear) <= 0:
                allowed_amount_for_other_garnishment = 0
            else:
                allowed_amount_for_other_garnishment = round(amount_left_for_arrears - allowed_child_support_arrear, 2)

            # Create Calculation_data_results object
            Calculation_data_results.objects.create(
                employee_id=data['employee_id'],
                employer_id=data['employer_id'],
                fedral_income_tax=federal_income_tax_rate,
                social_and_security=social_tax_rate,
                medicare_tax=medicare_tax_rate,
                state_taxes=state_tax_rate,
                earnings=earnings,
                support_second_family=support_second_family,
                garnishment_fees=garnishment_fees,
                arrears_greater_than_12_weeks=arrears_greater_than_12_weeks,
                amount_to_withhold_child1=amount_to_withhold_child1,
                amount_to_withhold_child2=amount_to_withhold_child2,
                amount_to_withhold_child3=amount_to_withhold_child3,
                arrears_amt_Child1=arrears_amt_Child1,
                arrears_amt_Child2=arrears_amt_Child2,
                arrears_amt_Child3=arrears_amt_Child3,
                number_of_arrears=number_of_arrears,
                allowable_disposable_earnings=allowable_disposable_earnings,
                withholding_available=withholding_available,
                other_garnishment_amount=other_garnishment_amount,
                amount_left_for_arrears=amount_left_for_arrears,
                allowed_amount_for_other_garnishment=allowed_amount_for_other_garnishment
            )

            # Create CalculationResult object
            CalculationResult.objects.create(
                employee_id=data['employee_id'],
                employer_id=data['employer_id'],
                result=allowed_amount_for_other_garnishment
            )

            LogEntry.objects.create(
                action='Calculation data Added',
                details=f'Calculation data Added successfully with employer ID {user.employer_id} and employee ID {user.employee_id}'
            )

            return Response({'message': 'Calculations Details Successfully Registered', "status code":status.HTTP_200_OK})

        except Employee_Details.DoesNotExist:
            return Response({"error": "Employee details not found"}, status=status.HTTP_404_NOT_FOUND)
        except Tax_details.DoesNotExist:
            return Response({"error": "Tax details not found", "status code":status.HTTP_404_NOT_FOUND})
        except Employer_Profile.DoesNotExist:
            return Response({"error": "Employer profile not found", "status code":status.HTTP_404_NOT_FOUND})
        except Exception as e:
            return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return Response({'message': 'Please use POST method', "status_code":status.HTTP_400_BAD_REQUEST})



@csrf_exempt
@api_view(['POST'])
def StudentLoanCalculationData(request):
    if request.method == 'POST':
        try:
            data = request.data
            required_fields = [
                'employee_name', 'garnishment_fees', 'minimum_wages', 'earnings','order_id'
            ]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return Response({'error': f'Required fields are missing: {", ".join(missing_fields)}'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = student_loan_data.objects.create(**data)

            # Retrieve the employee, tax, and employer records
            employee = Employee_Details.objects.get(employee_id=data['employee_id'], employer_id=data['employer_id'])
            tax = Tax_details.objects.get(employer_id=data['employer_id'])
            employer = Employer_Profile.objects.get(employer_id=data['employer_id'])
            gdata = student_loan_data.objects.filter(employer_id=data['employer_id'], employee_id=data['employee_id']).order_by('-timestamp').first()

            # Extracting earnings and garnishment fees from gdata
            earnings = gdata.earnings
            garnishment_fees = gdata.garnishment_fees
            
            # Calculate the various taxes
            federal_income_tax_rate = tax.fedral_income_tax
            social_tax_rate = tax.social_and_security
            medicare_tax_rate = tax.medicare_tax
            state_tax_rate = tax.state_tax
            SDI_tax=tax.state_tax
            total_tax = federal_income_tax_rate + social_tax_rate + medicare_tax_rate + state_tax_rate+SDI_tax
            disposable_earnings = round(earnings - total_tax, 2)
            allowable_disposable_earning=disposable_earnings-garnishment_fees
            fifteen_percent_of_eraning= allowable_disposable_earning*.15
            fmw=7.25*30
            difference=disposable_earnings-fmw
            if allowable_disposable_earning<fmw:
                garnishment_amount=0
            else:
                garnishment_amount=fifteen_percent_of_eraning

            net_pay=disposable_earnings-garnishment_amount
            
            # # Create Calculation_data_results object
            # Calculation_data_results.objects.create(
            #     employee_id=data['employee_id'],
            #     employer_id=data['employer_id'],
            #     fedral_income_tax=federal_income_tax_rate,
            #     social_and_security=social_tax_rate,
            #     medicare_tax=medicare_tax_rate,
            #     state_taxes=state_tax_rate,
            #     earnings=earnings,
            #     support_second_family=support_second_family,
            #     garnishment_fees=garnishment_fees,
            #     arrears_greater_than_12_weeks=arrears_greater_than_12_weeks,
            #     amount_to_withhold_child1=amount_to_withhold_child1,
            #     amount_to_withhold_child2=amount_to_withhold_child2,
            #     amount_to_withhold_child3=amount_to_withhold_child3,
            #     arrears_amt_Child1=arrears_amt_Child1,
            #     arrears_amt_Child2=arrears_amt_Child2,
            #     arrears_amt_Child3=arrears_amt_Child3,
            #     number_of_arrears=number_of_arrears,
            #     allocation_method_for_garnishment=allocation_method_for_garnishment,
            #     allocation_method_for_arrears=allocation_method_for_arrears,
            #     allowable_disposable_earnings=allowable_disposable_earnings,
            #     withholding_available=withholding_available,
            #     allowed_amount_for_garnishment=allowed_amount_for_garnishment,
            #     other_garnishment_amount=other_garnishment_amount,
            #     amount_left_for_arrears=amount_left_for_arrears,
            #     allowed_amount_for_other_garnishment=allowed_amount_for_other_garnishment
            # )
            # Create CalculationResult object
            single_student_loan_result.objects.create(
                employee_id=data['employee_id'],
                employer_id=data['employer_id'],
                net_pay=net_pay,
                garnishment_amount=garnishment_amount
            )

            LogEntry.objects.create(
                action='Student Loan Calculation data Added',
                details=f'Student Loan Calculation data Added successfully with employer ID {user.employer_id} and employee ID {user.employee_id}'
            )

            return Response({'message': 'Student Loan Calculation Details Registered Successfully', "status code":status.HTTP_200_OK})

        except Employee_Details.DoesNotExist:
            return Response({"error": "Employee details not found"}, status=status.HTTP_404_NOT_FOUND)
        except Tax_details.DoesNotExist:
            return Response({"error": "Tax details not found", "status code":status.HTTP_404_NOT_FOUND})
        except Employer_Profile.DoesNotExist:
            return Response({"error": "Employer profile not found", "status code":status.HTTP_404_NOT_FOUND})
        except Exception as e:
            return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return Response({'message': 'Please use POST method', "status_code":status.HTTP_400_BAD_REQUEST})


@csrf_exempt
@api_view(['POST'])
def MiltipleStudentLoanCalculationData(request):
    if request.method == 'POST':
        try:
            data = request.data
            required_fields = [
                'employee_name', 'garnishment_fees', 'minimum_wages', 'earnings','order_id'
            ]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return Response({'error': f'Required fields are missing: {", ".join(missing_fields)}'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = student_loan_data.objects.create(**data)
            
            # Retrieve the employee, tax, and employer records
            employee = Employee_Details.objects.get(employee_id=data['employee_id'], employer_id=data['employer_id'])
            tax = Tax_details.objects.get(employer_id=data['employer_id'])
            employer = Employer_Profile.objects.get(employer_id=data['employer_id'])
            gdata = student_loan_data.objects.filter(employer_id=data['employer_id'], employee_id=data['employee_id']).order_by('-timestamp').first()

            # Extracting earnings and garnishment fees from gdata
            earnings = gdata.earnings
            garnishment_fees = gdata.garnishment_fees
            
            # Calculate the various taxes
            federal_income_tax_rate = tax.fedral_income_tax
            social_tax_rate = tax.social_and_security
            medicare_tax_rate = tax.medicare_tax
            state_tax_rate = tax.state_tax
            SDI_tax=tax.state_tax
            total_tax = federal_income_tax_rate + social_tax_rate + medicare_tax_rate + state_tax_rate+SDI_tax
            disposable_earnings = round(earnings - total_tax, 2)
            allowable_disposable_earning=disposable_earnings-garnishment_fees
            twentyfifth_percent_of_eraning= allowable_disposable_earning*.25
            fmw=7.25*30
            
            if allowable_disposable_earning<fmw:
                garnishment_amount=0
            else:
                garnishment_amount=twentyfifth_percent_of_eraning


            studentloan1=allowable_disposable_earning*.15
            studentloan2=allowable_disposable_earning*.10
            studentloan3=allowable_disposable_earning*0

            net_pay=disposable_earnings-garnishment_amount
            
            # # Create Calculation_data_results object
            # Calculation_data_results.objects.create(
            #     employee_id=data['employee_id'],
            #     employer_id=data['employer_id'],
            #     fedral_income_tax=federal_income_tax_rate,
            #     social_and_security=social_tax_rate,
            #     medicare_tax=medicare_tax_rate,
            #     state_taxes=state_tax_rate,
            #     earnings=earnings,
            #     support_second_family=support_second_family,
            #     garnishment_fees=garnishment_fees,
            #     arrears_greater_than_12_weeks=arrears_greater_than_12_weeks,
            #     amount_to_withhold_child1=amount_to_withhold_child1,
            #     amount_to_withhold_child2=amount_to_withhold_child2,
            #     amount_to_withhold_child3=amount_to_withhold_child3,
            #     arrears_amt_Child1=arrears_amt_Child1,
            #     arrears_amt_Child2=arrears_amt_Child2,
            #     arrears_amt_Child3=arrears_amt_Child3,
            #     number_of_arrears=number_of_arrears,
            #     allocation_method_for_garnishment=allocation_method_for_garnishment,
            #     allocation_method_for_arrears=allocation_method_for_arrears,
            #     allowable_disposable_earnings=allowable_disposable_earnings,
            #     withholding_available=withholding_available,
            #     allowed_amount_for_garnishment=allowed_amount_for_garnishment,
            #     other_garnishment_amount=other_garnishment_amount,
            #     amount_left_for_arrears=amount_left_for_arrears,
            #     allowed_amount_for_other_garnishment=allowed_amount_for_other_garnishment
            # )
            # Create CalculationResult object
            multiple_student_loan_result.objects.create(
                employee_id=data['employee_id'],
                employer_id=data['employer_id'],
                garnishment_amount=twentyfifth_percent_of_eraning,
                net_pay=net_pay
            
            )
            LogEntry.objects.create(
                action='Student Loan Calculation data Added',
                details=f'Student Loan Calculation data Added successfully with employer ID {user.employer_id} and employee ID {user.employee_id}'
            )
            return Response({'message': 'Student Loan Calculations Details Successfully Registered', "status code":status.HTTP_200_OK})

        except Employee_Details.DoesNotExist:
            return Response({"error": "Employee details not found"}, status=status.HTTP_404_NOT_FOUND)
        except Tax_details.DoesNotExist:
            return Response({"error": "Tax details not found", "status code":status.HTTP_404_NOT_FOUND})
        except Employer_Profile.DoesNotExist:
            return Response({"error": "Employer profile not found", "status code":status.HTTP_404_NOT_FOUND})
        except Exception as e:
            return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return Response({'message': 'Please use POST method', "status_code":status.HTTP_400_BAD_REQUEST})



#Extracting the Last Five record from the Log Table
class LastFiveLogsView(APIView):
    def get(self, request, format=None):
        try:
           logs = LogEntry.objects.order_by('-timestamp')[:5]
           serializer = LogSerializer(logs, many=True)
           response_data = {
                       'success': True,
                       'message': 'Data Get successfully',
                       'status code': status.HTTP_200_OK,
                      'data' : serializer.data}
           return JsonResponse(response_data)
        except Exception as e:
            return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})


#Extracting the ALL Employer Detials  
class EmployerProfileList(generics.ListAPIView):
    def get(self, request, format=None):
        try:
            employees = Employer_Profile.objects.all()
            serializer = EmployerProfileSerializer(employees, many=True)
            response_data = {
                        'success': True,
                        'message': 'Data Get successfully',
                        'status code': status.HTTP_200_OK,
                        'data' : serializer.data}
            return JsonResponse(response_data)
        except Exception as e:
            return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})


#Extracting the ALL Employee Details 
class EmployeeDetailsList(generics.ListAPIView):
    def get(self, request, format=None):
        try:
            employees = Employee_Details.objects.all()
            serializer = EmployeeDetailsSerializer(employees, many=True)
            response_data = {
                        'success': True,
                        'message': 'Data Get successfully',
                        'status code': status.HTTP_200_OK,
                        'data' : serializer.data}
            return JsonResponse(response_data)
        except Exception as e:
            return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})

#Extracting the ALL Tax Details
class TaxDetailsList(generics.ListAPIView):
    def get(self, request, format=None):
        try:
            queryset = Tax_details.objects.all()
            serializer = TaxSerializer(queryset, many=True)
            response_data = {
                        'success': True,
                        'message': 'Data Get successfully',
                        'status code': status.HTTP_200_OK,
                        'data' : serializer.data}
            return JsonResponse(response_data)
        except Exception as e:
            return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
    

#Extracting the ALL Location Details
class LocationDetailsList(generics.ListAPIView):
    def get(self, request, format=None):
        try:
            queryset = Location.objects.all()
            serializer = LocationSerializer(queryset, many=True)
            response_data = {
                        'success': True,
                        'message': 'Data Get successfully',
                        'status code': status.HTTP_200_OK,
                        'data' : serializer.data}
            return JsonResponse(response_data)
        except Exception as e:
            return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})


#Extracting the ALL Department Details
class DepartmentDetailsList(generics.ListAPIView):
    def get(self, request, format=None):
        try:
            queryset = Department.objects.all()
            serializer = DepartmentSerializer(queryset, many=True)
            response_data = {
                        'success': True,
                        'message': 'Data Get successfully',
                        'status code': status.HTTP_200_OK,
                        'data' : serializer.data}
            return JsonResponse(response_data)
        except Exception as e:
            return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})

# Get the single employee details
@api_view(['GET'])
def get_single_calculation_details(request, employer_id, employee_id):
    employees = CalculationResult.objects.filter(employer_id=employer_id, employee_id=employee_id).order_by('-timestamp')[0:1]
    if employees.exists():
        try:
            employee = employees.order_by('-timestamp')[0]
            serializer = ResultSerializer(employee) 
            response_data = {
                'success': True,
                'message': 'Data fetched successfully',
                'status code': status.HTTP_200_OK,
                'data': serializer.data  
            }
            return JsonResponse(response_data)
        except CalculationResult.DoesNotExist:  # Adjust the exception as appropriate
            return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status code': status.HTTP_404_NOT_FOUND})


#Get the single employee details
@api_view(['GET'])
def get_single_employee_details(request, employer_id, employee_id):
    try:
        employee = Employee_Details.objects.get(employer_id=employer_id, employee_id=employee_id)
        serializer = EmployeeDetailsSerializer(employee)
        response_data = {
            'success': True,
            'message': 'Employee Data retrieved successfully',
            'status code': status.HTTP_200_OK,
            'data': serializer.data
        }
        return JsonResponse(response_data)
    except Employee_Details.DoesNotExist:
        return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})

    

#Get the singal Tax details  
@api_view(['GET'])
def get_single_tax_details(request, employer_id,tax_id):
    employees=Tax_details.objects.filter(employer_id=employer_id,tax_id=tax_id)
    if employees.exists():
        try:
            serializer = TaxSerializer(employees, many=True)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'status code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)
        except Employer_Profile.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status code':status.HTTP_404_NOT_FOUND})


#Get the singal Location details  
@api_view(['GET'])
def get_single_location_details(request, employer_id,location_id):
    employees=Location.objects.filter(employer_id=employer_id,location_id=location_id)
    if employees.exists():
        try:
            serializer = LocationSerializer(employees, many=True)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'status code': status.HTTP_200_OK,
                    'data' : serializer.data}
            return JsonResponse(response_data)
        except Employer_Profile.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status code':status.HTTP_404_NOT_FOUND})


 #Get the singal Department details  
@api_view(['GET'])
def get_single_department_details(request, employer_id,department_id):
    employees=Department.objects.filter(employer_id=employer_id,department_id=department_id)
    if employees.exists():
        try:
            serializer = DepartmentSerializer(employees, many=True)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'status code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)
        except Employer_Profile.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status code':status.HTTP_404_NOT_FOUND})   
    

@api_view(['GET'])
def get_single_result_details(request, employer_id):
    employees = CalculationResult.objects.filter(employer_id=employer_id).order_by('-timestamp')[0:1]
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
        except Employer_Profile.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status code': status.HTTP_404_NOT_FOUND})


@api_view(['GET'])
def get_SingleStudentLoanResult(request, employer_id):
    employees = single_student_loan_result.objects.filter(employer_id=employer_id).order_by('-timestamp')[0:1]
    if employees.exists():
        try:
            serializer = SingleStudentLoanSerializer(employees, many=True)
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


@api_view(['GET'])
def get_MultipleStudentLoanResult(request, employer_id):
    employees = multiple_student_loan_result.objects.filter(employer_id=employer_id).order_by('-timestamp')[0:1]
    if employees.exists():
        try:
            serializer = MultipleStudentLoanSerializer(employees, many=True)
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



@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = Employer_Profile.objects.get(email=email)
        except Employer_Profile.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

        token = RefreshToken.for_user(user).access_token
        # Change this URL to point to your frontend
        reset_url = f'https://garnishment-react-main.vercel.app/reset-password/{str(token)}'
        send_mail(
            'Password Reset Request',
            f'Click the link to reset your password: {reset_url}',
            'your-email@example.com',
            [email],
        )
        return Response({"message": "Password reset link sent.", "status code":status.HTTP_200_OK})



class PasswordResetConfirmView(APIView):
    def post(self, request, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data['password']

        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = Employer_Profile.objects.get(employer_id=user_id)
        except (Employer_Profile.DoesNotExist, TokenError) as e:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        employee = get_object_or_404(Employer_Profile, employer_name=user.employer_name, employer_id=user.employer_id)
        application_activity.objects.create(
            action='Forget Pasword',
            details=f'Employer {employee.employer_name} successfully forget password with ID {employee.employer_id}. '
        )
        return Response({"message": "Password reset successful.", "status code":status.HTTP_200_OK})



@csrf_exempt
@api_view(['POST'])
def federal_case(request):
    if request.method == 'POST':
        try:
            data = request.data
            required_fields = [ 'garnishment_fees','employee_name','no_of_exception','filing_status','pay_period', 'earnings']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return Response({'error': f'Required fields are missing: {", ".join(missing_fields)}'}, status=status.HTTP_400_BAD_REQUEST)           
            user = federal_loan_case_data.objects.create(**data)

            # Retrieve the employee, tax, and employer records
            employee = Employee_Details.objects.get(employee_id=data['employee_id'], employer_id=data['employer_id'])
            tax = Tax_details.objects.get(employer_id=data['employer_id'])
            employer = Employer_Profile.objects.get(employer_id=data['employer_id'])

            # Extracting earnings and garnishment fees from gdata
            earnings = data['earnings']
            garnishment_fees = data['garnishment_fees']
            
            # Calculate the various taxes
            federal_income_tax_rate = tax.fedral_income_tax
            social_tax_rate = tax.social_and_security
            medicare_tax_rate = tax.medicare_tax
            state_tax_rate = tax.state_tax
            mexico_tax=tax.mexico_tax
            workers_compensation=tax.workers_compensation
            medical_insurance=tax.medical_insurance
            contribution=tax.contribution
            united_way_contribution=tax.united_way_contribution
            filing_status=data['filing_status']
            no_of_exception=data['no_of_exception']
            pay_period=data['pay_period']
            total_tax = federal_income_tax_rate+social_tax_rate+mexico_tax+medicare_tax_rate+state_tax_rate+workers_compensation+medical_insurance+contribution+united_way_contribution
            # print("total_tax:",total_tax)

            disposable_earnings = round(earnings - total_tax, 2)
            # print("disposable_earnings:",disposable_earnings)
            # allowable_disposable_earning=disposable_earnings-garnishment_fees
            

            if filing_status.lower() == "single":
                queryset = single_filing_status.objects.filter(pay_period=pay_period)
                obj = queryset.first()
                if obj is None:
                    return JsonResponse({"error": "No matching records found for the given pay period"}, status=404)
                fields = single_filing_status._meta.get_fields()
                column_name = next((field.name for field in fields if field.name.endswith(str(no_of_exception))), None)
                if not column_name:
                    return JsonResponse({"error": "Column not found"}, status=404)
                column_value = getattr(obj, column_name)

            elif filing_status.lower() == "married filing sepearte return":
                queryset = married_filing_sepearte_return.objects.filter(pay_period=pay_period)
                obj = queryset.first()

                if obj is None:
                    return JsonResponse({"error": "No matching records found for the given pay period"}, status=404)
                fields = single_filing_status._meta.get_fields()
                column_name = next((field.name for field in fields if field.name.endswith(str(no_of_exception))), None)
                if not column_name:
                    return JsonResponse({"error": "Column not found"}, status=404)
                column_value = getattr(obj, column_name)

  
            elif filing_status.lower() == "married filing joint return":
                queryset = married_filing_joint_return.objects.filter(pay_period=pay_period)
                obj = queryset.first()
                if obj is None:
                    return JsonResponse({"error": "No matching records found for the given pay period"}, status=404)
                fields = single_filing_status._meta.get_fields()
                column_name = next((field.name for field in fields if field.name.endswith(str(no_of_exception))), None)
                if not column_name:
                    return JsonResponse({"error": "Column not found"}, status=404)
                column_value = getattr(obj, column_name)
            elif filing_status.lower() == "head of household":
                fields = head_of_household._meta.get_fields()

                queryset = head_of_household.objects.filter(pay_period=pay_period)
                obj = queryset.first()

                if obj is None:
                    return JsonResponse({"error": "No matching records found for the given pay period"}, status=404)
                fields = head_of_household._meta.get_fields()
                column_name = next((field.name for field in fields if field.name.endswith(str(no_of_exception))), None)
                if not column_name:
                    return JsonResponse({"error": "Column not found"}, status=404)
                column_value = getattr(obj, column_name)
                print(column_value)
            else:
                return JsonResponse({"error": "Invalid filing status"}, status=400)

            amount_deduct=round(disposable_earnings-column_value,2)

            net_pay=round(disposable_earnings-amount_deduct,2) 

            # Create CalculationResult object
            federal_case_result.objects.create(
                employee_id=data['employee_id'],
                employer_id=data['employer_id'],
                result=amount_deduct,
                net_pay=net_pay
            
            )
            LogEntry.objects.create(
                action='Federal Tax Calculation data Added',
                details=f'Federal Tax Calculation data Added successfully with employer ID {user.employer_id} and employee ID {user.employee_id}'
            )
            return Response({'message': 'Federal Tax Calculations Details Successfully Registered', "status code":status.HTTP_200_OK})

        except Employee_Details.DoesNotExist:
            return Response({"error": "Employee details not found"}, status=status.HTTP_404_NOT_FOUND)
        except Tax_details.DoesNotExist:
            return Response({"error": "Tax details not found", "status code":status.HTTP_404_NOT_FOUND})
        except Employer_Profile.DoesNotExist:
            return Response({"error": "Employer profile not found", "status code":status.HTTP_404_NOT_FOUND})
        except Exception as e:
            return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return Response({'message': 'Please use POST method', "status_code":status.HTTP_400_BAD_REQUEST}) 
    


class get_federal_case_result(APIView):
    def get(self, request, employee_id):
        employees = federal_case_result.objects.filter(employee_id=employee_id).order_by('-timestamp')[0:1]
        if employees.exists():
            try:
                serializer = federal_case_result_Serializer(employees)
                response_data = {
                    'success': True,
                    'message': 'Data retrieved successfully',
                    'status code': status.HTTP_200_OK,
                    'data': serializer.data
                }
                return JsonResponse(response_data)
            except federal_case_result.DoesNotExist:
                return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
        else:
            return JsonResponse({'message': 'Employee ID not found', 'status code': status.HTTP_404_NOT_FOUND})


@csrf_exempt
def Setting(request):
    try:  
        data = {
            'Setting1': False,
            'Setting2': False 
        }
    except Exception as e:
        return JsonResponse({'error': str(e), "status code":status.HTTP_500_INTERNAL_SERVER_ERROR}) 
    response_data = {
        'success': True,
        'message': 'Data Get successfully',
        'status code': status.HTTP_200_OK,
        'data' : data}
    return JsonResponse(response_data)

