from rest_framework import status
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CustomUser,Employer_Profile,Employee_Details,Tax_details,IWO_Details_PDF,Department,Location,PDFFile,Garcalculation_data,CalculationResult,LogEntry
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from django.db.models import Count
from django.shortcuts import get_object_or_404
import json
from rest_framework.response import Response
import pandas as pd
from django.contrib.auth.hashers import make_password
from rest_framework.generics import DestroyAPIView
from rest_framework import viewsets ,generics
from rest_framework.generics import RetrieveUpdateAPIView
from .serializers import UserUpdateSerializer,EmployerProfileSerializer ,GetEmployerDetailsSerializer,EmployeeDetailsSerializer,DepartmentSerializer, LocationSerializer,TaxSerializer,LogSerializer
from django.http import HttpResponse
from .forms import PDFUploadForm
from django.db import transaction
from rest_framework.decorators import api_view
from django.utils.decorators import method_decorator
import csv
from rest_framework.views import APIView
from io import StringIO

@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON',
                'status_code': status.HTTP_400_BAD_REQUEST
            })

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return JsonResponse({
                'success': False,
                'message': 'Email and password are required',
                'status_code': status.HTTP_400_BAD_REQUEST
            })

        try:
            user = Employer_Profile.objects.get(email=email)
        except Employer_Profile.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials',
                'status_code': status.HTTP_400_BAD_REQUEST
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

                employee = get_object_or_404(Employer_Profile, employer_id=user.employer_id)
                LogEntry.objects.create(
                action='Employer Login',
                details=f'Employer Login Successfully with ID {employee.employer_id}'
            )
                response_data = {
                    'success': True,
                    'message': 'Login successful',
                    'user_data': user_data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'status_code': status.HTTP_200_OK,
                }
                return JsonResponse(response_data)
            except AttributeError as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error generating tokens: {str(e)}',
                    'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials',
                'status_code': status.HTTP_400_BAD_REQUEST
            })
    else:
        return JsonResponse({
            'message': 'Please use POST method for login',
            'status_code': status.HTTP_400_BAD_REQUEST
        })


@csrf_exempt
def register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON', 'status_code': status.HTTP_400_BAD_REQUEST})

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
            return JsonResponse({'error': 'Password must meet complexity requirements', 'status_code': status.HTTP_400_BAD_REQUEST})

        User = get_user_model()
        if Employer_Profile.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already used', 'status_code': status.HTTP_400_BAD_REQUEST})
        if Employer_Profile.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email taken', 'status_code': status.HTTP_400_BAD_REQUEST})

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

            # Assuming your primary key is employer_id
            employee = get_object_or_404(Employer_Profile, employer_id=user.employer_id)
            LogEntry.objects.create(
                action='Employer Register',
                details=f'Employer Register Succesfully with ID {employee.employer_id}'
            )
            return JsonResponse({'message': 'Successfully registered', 'status_code': status.HTTP_201_CREATED})
        except Exception as e:
            return JsonResponse({'error': str(e), 'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return JsonResponse({'message': 'Please use POST method for registration', 'status_code': status.HTTP_400_BAD_REQUEST})
    

@csrf_exempt
def EmployerProfile(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            #required_fields = ['employer_name', 'street_name', 'federal_employer_identification_number', 'city', 'state', 'country', 'zipcode', 'email', 'number_of_employees', 'department', 'location']
            #missing_fields = [field for field in required_fields if field not in data or not data[field]]
            # if missing_fields:
            #     return JsonResponse({'error': f'Required fields are missing: {", ".join(missing_fields)}','status_code':status.HTTP_400_BAD_REQUEST})
            
            # Validate length of federal_employer_identification_number
            if len(str(data['federal_employer_identification_number'])) != 9:
                return JsonResponse({'error': 'Federal Employer Identification Number must be exactly 9 characters long', 'status_code':status.HTTP_400_BAD_REQUEST})
            
            if Employer_Profile.objects.filter(email=data['email']).exists():
                return JsonResponse({'error': 'Email already registered', 'status_code':status.HTTP_400_BAD_REQUEST})
            
            user = Employer_Profile.objects.create(**data)
            # Assuming your primary key is employer_id
            employee = get_object_or_404(Employer_Profile, employer_id=user.employer_id)
            LogEntry.objects.create(
                action='Employer details added',
                details=f'Employer details with ID {employee.employer_id}'
            )
            return JsonResponse({'message': 'Employer Detail Successfully Registered'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
    else:
        return JsonResponse({'message': 'Please use POST method','status_code':status.HTTP_400_BAD_REQUEST})


@csrf_exempt
def EmployeeDetails(request):
    if request.method == 'POST' :
        try:
            data = json.loads(request.body)
            required_fields = ['employee_name','department', 'net_pay', 'minimun_wages', 'pay_cycle', 'number_of_garnishment', 'location']
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
                details=f'Employee details added with ID {employee.employee_id}'
            )
            return JsonResponse({'message': 'Employee Details Successfully Registered', 'status_code':status.HTTP_201_CREATED})
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format','status_code':status.HTTP_400_BAD_REQUEST})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return JsonResponse({'message': 'Please use POST method ', 'status_code':status.HTTP_400_BAD_REQUEST})



@csrf_exempt
def TaxDetails(request):
    if request.method == 'POST' :
        try:
            data = json.loads(request.body)
            required_fields = ['employee_id','fedral_income_tax','social_and_security','medicare_tax','state_taxes']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            
            if missing_fields:
                return JsonResponse({'error': f'Required fields are missing: {", ".join(missing_fields)}', 'status_code':status.HTTP_400_BAD_REQUEST})
            
            user=Tax_details.objects.create(**data)
            user.save()

            employee = get_object_or_404(Tax_details, tax_id=user.tax_id)
            LogEntry.objects.create(
                action='Tax details added',
                details=f'Tax details have been successfully added for tax ID {employee.tax_id}'
            )
            return JsonResponse({'message': 'Tax Details Successfully Registered', 'status_code':status.HTTP_201_CREATED})
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format','status_code':status.HTTP_400_BAD_REQUEST})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return JsonResponse({'message': 'Please use POST method ', 'status_code':status.HTTP_400_BAD_REQUEST})


@api_view(['GET'])
def get_Location_Deatils(request, employer_id):
    employees=LocationSerializer.objects.filter(employer_id=employer_id)
    if employees.exists():
        try:
            serializer = LocationSerializer(employees, many=True)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'Code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)


        except Tax_details.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status_code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status':status.HTTP_404_NOT_FOUND})



#for Updating the Employer Profile data
class EmployerProfileEditView(RetrieveUpdateAPIView):
    queryset = Employer_Profile.objects.all()
    serializer_class = EmployerProfileSerializer
    lookup_field = 'employer_id'
    @csrf_exempt
    def put(self, request, *args, **kwargs):
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
                action='Tax details added',
                details=f'Tax details Successfully added with ID {instance.employer_id}'
            )

        response_data = {
            'success': True,
            'message': 'Data Updated successfully',
            'Code': status.HTTP_200_OK
        }
        return JsonResponse(response_data)




#For updating the Registor details

class UserUpdateAPIView(RetrieveUpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserUpdateSerializer
    lookup_field = 'username'  
    @csrf_exempt
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_data = {
                'success': True,
                'message': 'Data Updated successfully',
                'Code': status.HTTP_200_OK}
        return JsonResponse(response_data)
    

#Delete User Deatils
class UserDeleteAPIView(DestroyAPIView):
    queryset = CustomUser.objects.all()
    lookup_field = 'username' 
    @csrf_exempt
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        response_data = {
                'success': True,
                'message': 'Data Deleted successfully',
                'Code': status.HTTP_204_NO_CONTENT}
        return JsonResponse(response_data)
    
#update employee Details
@method_decorator(csrf_exempt, name='dispatch')
class EmployeeDetailsUpdateAPIView(RetrieveUpdateAPIView):
    queryset = Employee_Details.objects.all()
    serializer_class = EmployeeDetailsSerializer
    lookup_field = 'employee_id'  
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        LogEntry.objects.create(
        action='Employee details Updated',
        details=f'Employee details have been successfully Updated for Employee ID {instance.employee_id}'
            )
        response_data = {
                'success': True,
                'message': 'Data Updated successfully',
                'Code': status.HTTP_200_OK}
        return JsonResponse(response_data)


#update Tax Details
@method_decorator(csrf_exempt, name='dispatch')
class TaxDetailsUpdateAPIView(RetrieveUpdateAPIView):
    queryset = Tax_details.objects.all()
    serializer_class = TaxSerializer
    lookup_field = 'tax_id'  
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_data = {
                'success': True,
                'message': 'Data Updated successfully',
                'Code': status.HTTP_200_OK}
        LogEntry.objects.create(
        action='Tax details Updated',
        details=f'Tax details have been Updated successfully added for tax ID {instance.tax_id}'
            )
        return JsonResponse(response_data)


#update Location Details
@method_decorator(csrf_exempt, name='dispatch')
class LocatiionDetailsUpdateAPIView(RetrieveUpdateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    lookup_field = 'location_id'  
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        LogEntry.objects.create(
        action='Location details Updated',
        details=f'LOcation details have been Updated successfully added for Location ID{instance.location_id}'
            )
        response_data = {
                'success': True,
                'message': 'Data Updated successfully',
                'Code': status.HTTP_200_OK}
        return JsonResponse(response_data)
    

#update Department Details
@method_decorator(csrf_exempt, name='dispatch')
class DepartmentDetailsUpdateAPIView(RetrieveUpdateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    lookup_field = 'department_id'  
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        LogEntry.objects.create(
        action='Department details Updated',
        details=f'Department details have been successfully added for Loaction ID{instance.department_id}'
            )
        response_data = {
                'success': True,
                'message': 'Data Updated successfully',
                'Code': status.HTTP_200_OK}
        return JsonResponse(response_data)



# For Deleting the Employer Profile data
@method_decorator(csrf_exempt, name='dispatch')
class UserDeleteAPIView(DestroyAPIView):
    queryset = CustomUser.objects.all()
    lookup_field = 'username' 
    @csrf_exempt
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        LogEntry.objects.create(
        action='Department details Updated',
        details=f'Department details Updated successfully with ID {instance.department_id}'
            )
        response_data = {
                'success': True,
                'message': 'Data Deleted successfully',
                'Code': status.HTTP_200_OK}
        return JsonResponse(response_data)
    

#PDF upload view
@transaction.atomic
def upload_pdf(request):
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = form.cleaned_data['pdf_file']
            pdf_name = pdf_file.name
            pdf_data = pdf_file.read()
            
            # Store PDF file data in the database
            pdf_record = PDFFile(name=pdf_name, data=pdf_data)
            pdf_record.save()
            employee = get_object_or_404(PDFFile, id=pdf_record.id)
            LogEntry.objects.create(
            action='PDF Uploaded',
            details=f'PDF successfully Uploaded with ID {employee.id}')
        
            return HttpResponse("File uploaded successfully.")
    else:
        form = PDFUploadForm()

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
                    'Code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)


        except Employee_Details.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status_code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status':status.HTTP_404_NOT_FOUND})



@api_view(['GET'])
def get_Tax_details(request, employer_id,self):
    employees=Tax_details.objects.filter(employer_id=employer_id)
    instance = self.get_object()
    if employees.exists():
        try:
            serializer = TaxSerializer(employees, many=True)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'Code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)

        except Tax_details.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status_code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status':status.HTTP_404_NOT_FOUND})


@api_view(['GET'])
def get_Location_details(request, employer_id):
    employees=Location.objects.filter(employer_id=employer_id)
    if employees.exists():
        try:
            serializer = LocationSerializer(employees, many=True)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'Code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)

        except Tax_details.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status_code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status':status.HTTP_404_NOT_FOUND})


@api_view(['GET'])
def get_Department_details(request, employer_id):
    employees=Department.objects.filter(employer_id=employer_id)
    if employees.exists():
        try:
            serializer = DepartmentSerializer(employees, many=True)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'Code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)


        except Tax_details.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status_code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status':status.HTTP_404_NOT_FOUND})



@api_view(['GET'])
def get_employee_by_employer_id(request, employer_id):
    employees=Employee_Details.objects.filter(employer_id=employer_id)
    if employees.exists():
        try:
            serializer = EmployeeDetailsSerializer(employees, many=True)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'Code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)


        except Employee_Details.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status_code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status':status.HTTP_404_NOT_FOUND})


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
                    'Code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)
        except Employer_Profile.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status_code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status_code':status.HTTP_404_NOT_FOUND})
    


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
            # LogEntry.objects.create(
            # action='Location details Updated',
            # details=f'LOcation details have been Updated successfully added for Location ID{instance.location_id}'
            # )

            return JsonResponse({'message': 'IWO detail inserted successfully', 'code' :status.HTTP_201_CREATED})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON', 'status_code':status.HTTP_400_BAD_REQUEST})
        except Exception as e:
            return JsonResponse({'error': str(e),'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR})

    return JsonResponse({'error': 'Invalid request method', 'status_code': status.HTTP_405_METHOD_NOT_ALLOWED})



@csrf_exempt
def get_dashboard_data(request):
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

    return JsonResponse({'data':data,'status_code':status.HTTP_200_OK})


@csrf_exempt
def TaxDetails(request):
    if request.method == 'POST' :
        try:
            data = json.loads(request.body)
            required_fields = ['employer_id','fedral_income_tax','social_and_security','medicare_tax','state_taxes']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            
            if missing_fields:
                return JsonResponse({'error': f'Required fields are missing: {", ".join(missing_fields)}', 'status_code':status.HTTP_400_BAD_REQUEST})
            
            Tax_details.objects.create(**data)
            return JsonResponse({'message': 'Tax Details Successfully Registered', 'status_code':status.HTTP_201_CREATED})
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format','status_code':status.HTTP_400_BAD_REQUEST})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return JsonResponse({'message': 'Please use POST method ', 'status_code':status.HTTP_400_BAD_REQUEST})
  


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
            return JsonResponse({'message': 'Department Details Successfully Registered'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
    else:
        return JsonResponse({'message': 'Please use POST method','status_code':status.HTTP_400_BAD_REQUEST})

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
            return JsonResponse({'message': 'Location Details Successfully Registered'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
    else:
        return JsonResponse({'message': 'Please use POST method','status_code':status.HTTP_400_BAD_REQUEST})



# For Deleting the Employee Details
@method_decorator(csrf_exempt, name='dispatch')
class EmployeeDeleteAPIView(DestroyAPIView):
    queryset = Employee_Details.objects.all()
    lookup_field = 'employee_id' 
    @csrf_exempt
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        LogEntry.objects.create(
        action='Employee details Deleted',
        details=f'Employee details Deleted successfully with ID {instance.employee_id}'
            ) 
        response_data = {
                'success': True,
                'message': 'Data Deleted successfully',
                'Code': status.HTTP_200_OK}
        return JsonResponse(response_data)
    
# For Deleting the Tax Details
@method_decorator(csrf_exempt, name='dispatch')
class TaxDeleteAPIView(DestroyAPIView):
    queryset = Tax_details.objects.all()
    lookup_field = 'tax_id' 
    @csrf_exempt
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        LogEntry.objects.create(
        action='Tax details Deleted',
        details=f'Tax details Deleted successfully with ID {instance.tax_id}'
            ) 
        response_data = {
                'success': True,
                'message': 'Tax Data Deleted successfully',
                'Code': status.HTTP_200_OK}
        return JsonResponse(response_data)
    

# For Deleting the Location Details
@method_decorator(csrf_exempt, name='dispatch')
class LocationDeleteAPIView(DestroyAPIView):
    queryset = Location.objects.all()
    lookup_field = 'location_id' 
    @csrf_exempt
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        LogEntry.objects.create(
        action='Location details Deleted',
        details=f'Location details Deleted successfully with ID {instance.location_id}'
            ) 
        response_data = {
                'success': True,
                'message': 'Location Data Deleted successfully',
                'Code': status.HTTP_200_OK}
        return JsonResponse(response_data)



# For Deleting the Department Details
@method_decorator(csrf_exempt, name='dispatch')
class DepartmentDeleteAPIView(DestroyAPIView):
    queryset = Department.objects.all()
    lookup_field = 'department_id' 
    @csrf_exempt
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        LogEntry.objects.create(
        action='Department details Deleted',
        details=f'Department details Deleted successfully with ID {instance.department_id}'
            ) 
        response_data = {
                'success': True,
                'message': 'Department Data Deleted successfully',
                'Code': status.HTTP_200_OK}
        return JsonResponse(response_data)
    
    


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
                employee.get('minimun_wages', ''),
                employee.get('pay_cycle', ''),
                employee.get('number_of_garnishment ', ''),
                employee.get('location', '')
            ])

        return response
    except Exception as e:
        return JsonResponse({'detail': str(e), 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})



#Import employee details using the Excel file
class EmployeeImportView(APIView):
    def post(self, request, employer_id):
        employer = get_object_or_404(Employee_Details, id=employer_id)
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
            'net_pay':row['net_pay'],
            'minimun_wages':row['minimun_wages'],
            'pay_cycle':row['pay_cycle'],
            'number_of_garnishment':row['number_of_garnishment'],
            'location':row['location'],
            'employer_id': row['employer_id'] 
            }
            serializer = EmployeeDetailsSerializer(data=employee_data)
            if serializer.is_valid():
                employees.append(serializer.save())
                LogEntry.objects.create(
                action='Employee details Imported',
                details=f'Employee details Imported successfully using excel file with ID {employer.employee_id}'
            )   
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        
        return Response({"message": "File processed successfully"}, status=status.HTTP_201_CREATED)


#Post API Taking the Calculation data
@csrf_exempt
def CalculationDataView(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            required_fields = ['earning', 'have_any_arrears' ,'garnishment_fees', 'arrears_greater_than_12_weeks', 'arrears_amt' , 'total_amount_to_withhold']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return JsonResponse({'error': f'Required fields are missing: {", ".join(missing_fields)}'}, status=status.HTTP_400_BAD_REQUEST)         
            user = Garcalculation_data.objects.create(**data)
            table = get_object_or_404(Garcalculation_data, id=user.id)
            LogEntry.objects.create(
            action='Employee details Deleted',
            details=f'Employee details Deleted successfully with ID {table.id}'
            )  
            return JsonResponse({'message': 'Calculations Details Successfully Registered'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return JsonResponse({'error': str(e), status:status.HTTP_500_INTERNAL_SERVER_ERROR}) 
    else:
        return JsonResponse({'message': 'Please use POST method', status:status.HTTP_400_BAD_REQUEST})




#class Gcalculations(APIView):
def Gcalculations(request, employee_id, employer_id):
    try:
        # Retrieve the employee, tax, and employer records
        employee = Employee_Details.objects.get(employee_id=employee_id, employer_id=employer_id)
        tax = Tax_details.objects.get(employer_id=employer_id)
        employer = Employer_Profile.objects.get(employer_id=employer_id)
        gdata=Garcalculation_data.objects.get(employee_id=employee_id, employer_id=employer_id)
        
        # Calculate the various taxes
        federal_income_tax = employee.net_pay * tax.fedral_income_tax / 100
        social_tax = employee.net_pay * tax.social_and_security / 100
        medicare_tax = employee.net_pay * tax.medicare_tax / 100
        state_tax = employee.net_pay * tax.state_taxes / 100
        total_tax = federal_income_tax + social_tax + medicare_tax + state_tax
        disposable_earnings = employee.net_pay - total_tax
        
        # Calculate allowable disposable earnings
        fmw = 30 * 7.5  # Federal Minimum Wage
        ccpa_limit = 0.65  # Maximum CCPA limit (65%)
        allowable_disposable_earnings = disposable_earnings * (1 - ccpa_limit)
        withholding_available = allowable_disposable_earnings - gdata.garnishment_fees
        # Determine the allowable garnishment amount
        if (allowable_disposable_earnings - fmw) < 0:
            allowable_garnishment_amount = 0
        else:
            allowable_garnishment_amount = allowable_disposable_earnings - fmw
        if allowable_garnishment_amount < withholding_available:
            allowed_amount_for_garnishment = allowable_garnishment_amount
        else:
            allowed_amount_for_garnishment = withholding_available
        
        # Determine allocation method for garnishment
        if employer.state in ["Texas", "Washington"]:
            allocation_method_for_garnishment = "Divide Equally"
        else:
            allocation_method_for_garnishment = "Prorate"
        # Calculate the amount left for arrears
        allowed_child_support_arrear = gdata.arrears_amt
        amount_left_for_arrears = allowed_amount_for_garnishment - gdata.arrears_amt
        
        if gdata.have_any_arrears:
            allowed_amount_for_other_garnishment = allowed_amount_for_garnishment - allowed_child_support_arrear
        else:
            allowed_amount_for_other_garnishment = allowed_amount_for_garnishment - allowed_child_support_arrear
        
        # Save the calculation result to the database
        CalculationResult.objects.create(
        employee_id=employee_id,
        employer_id=employer_id,
        result=allowed_amount_for_other_garnishment)     
        return JsonResponse({'Garnishment Amount': allowed_amount_for_other_garnishment}, status=status.HTTP_200_OK)
    
    except Employee_Details.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)
    except Tax_details.DoesNotExist:
        return JsonResponse({'error': 'Tax details not found'}, status=status.HTTP_404_NOT_FOUND)
    except Employer_Profile.DoesNotExist:
        return JsonResponse({'error': 'Employer not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#Extracting the Last Five record from the Log Table
class LastFiveLogsView(APIView):
    def get(self, request, format=None):
        logs = LogEntry.objects.order_by('-timestamp')[:5]
        serializer = LogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class EmployerProfileList(generics.ListAPIView):
    queryset = Employer_Profile.objects.all()
    serializer_class = EmployerProfileSerializer

class EmployeeDetailsList(generics.ListAPIView):
    queryset = Employee_Details.objects.all()
    serializer_class = EmployeeDetailsSerializer

