from rest_framework import status
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import *
import pandas 
from User_app.models import *
from django.contrib.auth import authenticate, login as auth_login ,get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Count
from django.shortcuts import get_object_or_404
import json
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from rest_framework.generics import DestroyAPIView ,RetrieveUpdateAPIView
from ..serializers import *
from django.http import HttpResponse
from ..forms import PDFUploadForm
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
                    'message': 'Login successfully',
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


class EmployeeDetailsAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            # Deserialize and validate data using the serializer
            serializer = EmployeeDetailsSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Validation error', 'details': serializer.errors,
                    "status":status.HTTP_400_BAD_REQUEST }
                )
            
            # Save validated data to the database
            employee = serializer.save()
            
            # Log the action
            LogEntry.objects.create(
                action='Employee details added',
                details=f'Employee details added successfully with employee ID {employee.employee_id}'
            )
            
            return Response(
                {'message': 'Employee Details Successfully Registered',
                "status":status.HTTP_201_CREATED}
            )
        
        except Exception as e:  # Handle general errors
            return Response(
                {'error': str(e),
                "status":status.HTTP_500_INTERNAL_SERVER_ERROR}
            )


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
            # required_fields = ['employer_name', 'street_name', 'federal_employer_identification_number', 'city', 'state', 'country', 'zipcode', 'email', 'number_of_employees', 'department', 'location']
            # missing_fields = [field for field in required_fields if field not in data or not data[field]]
            # if missing_fields:
            #     return JsonResponse({'error': f'Required fields are missing: {", ".join(missing_fields)}', 'status_code':status.HTTP_400_BAD_REQUEST})
    
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
    queryset = Employee_Detail.objects.all()
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
    employees=Employee_Detail.objects.filter(employer_id=employer_id)
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

        except Employee_Detail.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code':status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status code':status.HTTP_404_NOT_FOUND})



@api_view(['GET'])
def get_employee_by_employer_id(request, employer_id):
    employees=Employee_Detail.objects.filter(employer_id=employer_id)
    if employees.exists():
        try:
            serializer = EmployeeDetailsSerializer(employees, many=True)
            response_data = {
                    'success': True,
                    'message': 'Data Get successfully',
                    'status code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)
        except Employee_Detail.DoesNotExist:
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
    queryset = Employee_Detail.objects.all()
    lookup_field = 'employee_id'

    def get_object(self):
        employee_id = self.kwargs.get('employee_id')
        employer_id = self.kwargs.get('employer_id')
        return Employee_Detail.objects.get(employee_id=employee_id, employer_id=employer_id)
    
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
        employees = Employee_Detail.objects.filter(employer_id=employer_id)
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
                df = pandas.read_csv(file)
            elif file_name.endswith(('.xlsx','.xls', '.xlsm', '.xlsb', '.odf', '.ods','.odt')):
                df = pandas.read_excel(file)
            else:
                return Response({"error": "Unsupported file format. Please upload a CSV or Excel file."}, status=status.HTTP_400_BAD_REQUEST)
            df['employer_id'] = employer_id        
            employees = []
            for _, row in df.iterrows():
                employee_data={
                'employee_name':row['employee_name'],
                'department':row['department'],
                'pay_cycle':row['pay_cycle'],
                'number_of_child_support_order':row['number_of_child_support_order'],
                'location':row['location'],
                'employer_id': row['employer_id'] 
                }
                # employer = get_object_or_404(Employee_Detail, employer_id=employer_id)
    
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
class EmployerProfileList(APIView):
    def get(self, request, format=None):
        try:
            employees = Employer_Profile.objects.all()
            serializer = EmployerProfileSerializer(employees, many=True)
            response_data = {
                'success': True,
                'message': 'Data retrieved successfully',
                'status_code': status.HTTP_200_OK,
                'data': serializer.data
            }
            return JsonResponse(response_data)
        except Exception as e:
            return Response({"error": str(e), "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR})


#Extracting the ALL Employee Details 
class EmployeeDetailsList(APIView):
    def get(self, request, format=None):
        try:
            employees = Employee_Detail.objects.all()
            serializer = EmployeeDetailsSerializer(employees, many=True)
            response_data = {
                        'success': True,
                        'message': 'Data Get successfully',
                        'status code': status.HTTP_200_OK,
                        'data' : serializer.data}
            return JsonResponse(response_data)
        except Exception as e:
            return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})




#Get the single employee details
@api_view(['GET'])
def get_single_Employee_Detail(request, employer_id, employee_id):
    try:
        employee = Employee_Detail.objects.get(employer_id=employer_id, employee_id=employee_id)
        serializer = EmployeeDetailsSerializer(employee)
        response_data = {
            'success': True,
            'message': 'Employee Data retrieved successfully',
            'status code': status.HTTP_200_OK,
            'data': serializer.data
        }
        return JsonResponse(response_data)
    except Employee_Detail.DoesNotExist:
        return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})

    



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
            user.set_password(new_password)
            user.save()
            employee = get_object_or_404(Employer_Profile, employer_name=user.employer_name, employer_id=user.employer_id)
            application_activity.objects.create(
                action='Forget Pasword',
                details=f'Employer {employee.employer_name} successfully forget password with ID {employee.employer_id}. '
            )
        except (Employer_Profile.DoesNotExist, TokenError) as e:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})
        return Response({"message": "Password reset successful.", "status code":status.HTTP_200_OK})




@csrf_exempt
def SettingPostAPI(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            required_fields = ['modes','visibilitys','employer_id']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return JsonResponse({'error': f'Required fields are missing: {", ".join(missing_fields)}','status_code':status.HTTP_400_BAD_REQUEST})
            
            user = setting.objects.create(**data)
            LogEntry.objects.create(
            action='setting details added',
            details=f'setting details added successfully'
            ) 
            return JsonResponse({'message': 'Setting Details Successfully Registered', "status code" :status.HTTP_201_CREATED})
        except Exception as e:
            return JsonResponse({'error': str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR}) 
    else:
        return JsonResponse({'message': 'Please use POST method','status code':status.HTTP_400_BAD_REQUEST})

class GETSettingDetails(APIView):
    def get(self, request, employer_id):
        employees = setting.objects.filter(employer_id=employer_id)
        if employees.exists():
            try:
                employee = employees.first() 
                serializer = setting_Serializer(employee)
                response_data = {
                    'success': True,
                    'message': 'Data retrieved successfully',
                    'status code': status.HTTP_200_OK,
                    'data' : serializer.data
                    }
                return JsonResponse(response_data)
            except setting.DoesNotExist:
                return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
        else:
            return JsonResponse({'message': 'Employee ID not found', 'status code': status.HTTP_404_NOT_FOUND})
    

# class GETallcalculationresult(APIView):
#     def get(self, request, employer_id):
        
#         # Retrieve data for each model
#         calculation_data_result = CalculationResult.objects.filter(employer_id=employer_id)
#         single_student_loan_results = single_student_loan_result.objects.filter(employer_id=employer_id)
#         multiple_student_loan_results = multiple_student_loan_result.objects.filter(employer_id=employer_id)
#         federal_case_results = federal_case_result.objects.filter(employer_id=employer_id)

#         if calculation_data_result.exists() or single_student_loan_results.exists() or multiple_student_loan_results.exists() or federal_case_results.exists():
#             try:
#                 # Serialize the data using the correct serializer classes
#                 calculatoinserializer = ResultSerializer(calculation_data_result, many=True)
#                 singlestudentserializer = SingleStudentLoanSerializer(single_student_loan_results, many=True)
#                 multiplestudentserializer = MultipleStudentLoanSerializer(multiple_student_loan_results, many=True)
#                 federalcaseserializer = federal_case_result_Serializer(federal_case_results, many=True)

#                 # Adding the case field to each serialized data
#                 for item in calculatoinserializer.data:
#                     item['Garnishment case'] = 'Child Support Calculation Result'
#                 for item in singlestudentserializer.data:
#                     item['Garnishment case'] = 'Single Student Loan Result'
#                 for item in multiplestudentserializer.data:
#                     item['Garnishment case'] = 'Multiple Student Loan Result'
#                 for item in federalcaseserializer.data:
#                     item['Garnishment case'] = 'Federal Tax Case Result'

#                 # Combine all serialized data into one list
#                 final_result = (
#                     calculatoinserializer.data + 
#                     singlestudentserializer.data + 
#                     multiplestudentserializer.data + 
#                     federalcaseserializer.data
#                 )

#                 response_data = {
#                     'success': True,
#                     'message': 'Data retrieved successfully',
#                     'status code': status.HTTP_200_OK,
#                     'data': final_result
#                 }
#                 return JsonResponse(response_data, status=status.HTTP_200_OK)
#             except Exception as e:
#                 return JsonResponse({'message': f'Error occurred: {str(e)}', 'status code': status.HTTP_500_INTERNAL_SERVER_ERROR})
#         else:
#             return JsonResponse({'message': 'Employer ID not found', 'status code': status.HTTP_404_NOT_FOUND})


# from django.db.models import Count
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from ..models import APICallLog
# from ..serializers import APICallCountSerializer
# from django.utils.timezone import make_aware
# import datetime

class APICallCountView(APIView):
    def get(self, request):
        logs = APICallLog.objects.values('date', 'endpoint', 'count')
        return Response(logs)
