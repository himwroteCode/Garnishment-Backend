from rest_framework import status
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CustomUser,Employer_Profile,Employee_Details,Tax_details,IWO_Details_PDF,Department,Location,PDFFile
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
from rest_framework import viewsets
from rest_framework.generics import RetrieveUpdateAPIView
from .serializers import UserUpdateSerializer,EmployerProfileSerializer ,GetEmployerDetailsSerializer,EmployeeDetailsSerializer,DepartmentSerializer, LocationSerializer,TaxSerializer
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



# @csrf_exempt
# def register(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             first_name = data.get('first_name')
#             last_name = data.get('last_name')
#             username = data.get('username')
#             email = data.get('email')
#             gender = data.get('gender')
#             contact_number = data.get('contact_number')
#             password1 = data.get('password1')
#             password2 = data.get('password2')
#             # first_name = request.POST.get('first_name')
#             # last_name = request.POST.get('last_name')
#             # username = request.POST.get('username')
#             # email = request.POST.get('email')
#             # gender = request.POST.get('gender')
#             # contact_number = request.POST.get('contact_number')
#             # password1 = request.POST.get('password1')
#             # password2 = request.POST.get('password2')
#             if password1 == password2:
#                 User = get_user_model()
#                 if User.objects.filter(username=username).exists():
#                     return JsonResponse({'error': 'Username Taken'}, status=status.HTTP_400_BAD_REQUEST)
#                 elif User.objects.filter(email=email).exists():
#                     return JsonResponse({'error': 'Email Taken'}, status=status.HTTP_400_BAD_REQUEST)
#                 else:
#                     user = CustomUser.objects.create_user(first_name=first_name, last_name=last_name, email=email, gender=gender, contact_number=contact_number, username=username, password=password1)
#                     user.save()
#                     return JsonResponse({'message': 'Successfully Registered'})
#             else:
#                 return JsonResponse({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     return render(request, 'register.html')


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
            return JsonResponse({'error': 'Username taken', 'status_code': status.HTTP_400_BAD_REQUEST})
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
            return JsonResponse({'message': 'Successfully registered', 'status_code': status.HTTP_201_CREATED})
        except Exception as e:
            return JsonResponse({'error': str(e), 'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return JsonResponse({'message': 'Please use POST method for registration', 'status_code': status.HTTP_400_BAD_REQUEST})

#new


def dashboard(request):
    return render( 'dashboard.html')

def logout(request):
    logout(request)
    return redirect('login')




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
            
            Employee_Details.objects.create(**data)
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
            
            Tax_details.objects.create(**data)
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

            return HttpResponse("File uploaded successfully.")
    else:
        form = PDFUploadForm()

    return render(request, 'upload_pdf.html', {'form': form})



#Get Employer Details on the bases of Employer_ID

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



@api_view(['GET'])
def get_Tax_details(request, employer_id):
    employees=Tax_details.objects.filter(employer_id=employer_id)
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
            required_fields = ['employee_id','fedral_income_tax','social_and_security','medicare_tax','state_taxes']
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
  

# @method_decorator(csrf_exempt, name='dispatch')
# class DepartmentViewSet(viewsets.ModelViewSet):
#     queryset = Department.objects.all()
#     serializer_class = DepartmentSerializer
#     csrf_exempt
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         response_data = {
#             'success': True,
#             'message': 'Detail successfully registered',
#             'Code': status.HTTP_201_CREATED
#         }
#         headers = self.get_success_headers(serializer.data)
#         return JsonResponse(response_data, status=status.HTTP_201_CREATED, headers=headers)

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
            required_fields = ['employer_id','state','city','street']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return JsonResponse({'error': f'Required fields are missing: {", ".join(missing_fields)}','status_code':status.HTTP_400_BAD_REQUEST})
            user = Location.objects.create(**data)
            return JsonResponse({'message': 'Location Details Successfully Registered'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
    else:
        return JsonResponse({'message': 'Please use POST method','status_code':status.HTTP_400_BAD_REQUEST})

# For Deleting the Employer Profile data
@method_decorator(csrf_exempt, name='dispatch')
class EmployeeDeleteAPIView(DestroyAPIView):
    queryset = Employee_Details.objects.all()
    lookup_field = 'employee_id' 
    @csrf_exempt
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        response_data = {
                'success': True,
                'message': 'Data Deleted successfully',
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
                employee.get('number_of_garnishment', ''),
                employee.get('location', '')
            ])

        return response
    except Exception as e:
        return JsonResponse({'detail': str(e), 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})

# class EmployeeImportView(APIView):
#     def post(self, request):
#         # Check if 'file' is in request.FILES
#         if 'file' not in request.FILES:
#             return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
#         file = request.FILES['file']
#         if not file.name.endswith(('.csv', '.xsl', '.xlsx')):
#             return Response({"error": "This is not a valid file type"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             file_data = file.read().decode('utf-8').splitlines()
#         except UnicodeDecodeError:
#             try:
#                 file_data = file.read().decode('latin-1').splitlines()
#             except UnicodeDecodeError:
#                 return Response({"error": "File encoding not supported"}, status=status.HTTP_400_BAD_REQUEST)
        
#         reader = csv.DictReader(file_data)
        
#         employees = []
#         for row in reader:
#             employee_data = {
#                 'employer_id': row['employer_id'],
#                 'employee_id': row['employee_id'],
#                 'employee_name': row['employee_name'],
#                 'department': row['department'],
#                 'net_pay': row['net_pay'],
#                 'minimum_wages': row['minimum_wages'],
#                 'pay_cycle': row['pay_cycle'],
#                 'number_of_garnishment': row['number_of_garnishment'],
#                 'location': row['location']
#             }
#             serializer = EmployeeDetailsSerializer(data=employee_data)
#             if serializer.is_valid():
#                 employees.append(serializer.save())
#             else:
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
#         return Response({"message": "CSV file processed successfully"}, status=status.HTTP_201_CREATED)


# class EmployeeImportView(APIView):
#     def post(self, request):
#         if 'file' not in request.FILES:
#             return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
#         file = request.FILES['file']
#         file_name = file.name

#         # Check the file extension
#         if file_name.endswith('.csv'):
#             df = pd.read_csv(file)
#         elif file_name.endswith(('.xlsx','.xls', '.xlsm', '.xlsb', '.odf', '.ods','.odt')):
#             df = pd.read_excel(file)
#         else:
#             return Response({"error": "Unsupported file format. Please upload a CSV or Excel file."}, status=status.HTTP_400_BAD_REQUEST)
        
#         employees = []
#         for _, row in df.iterrows():
#             employee_data={
#             # 'employer_id':row['employer_id'],
#             'employee_id':row['employee_id'],
#             'employee_name':row['employee_name'],
#             'department':row['department'],
#             'net_pay':row['net_pay'],
#             'minimun_wages':row['minimun_wages'],
#             'pay_cycle':row['pay_cycle'],
#             'number_of_garnishment':row['number_of_garnishment'],
#             'location':row['location']
#             }
#             serializer = EmployeeDetailsSerializer(data=employee_data)
#             if serializer.is_valid():
#                 employees.append(serializer.save())
#             else:
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
#         return JsonResponse({"message": "File processed successfully", status:status.HTTP_201_CREATED})


class EmployeeImportView(APIView):
    def post(self, request, employer_id):
        # Ensure the employer exists
        #employer = get_object_or_404(Employee_Details, id=employer_id)
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
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "File processed successfully"}, status=status.HTTP_201_CREATED)
