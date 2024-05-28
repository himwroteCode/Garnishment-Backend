from rest_framework import serializers
from .models import CustomUser ,Employer_Profile,Employee_Details,IWO_Details_PDF



class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['name', 'email']


# class EmployerProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Employer_Profile
#         fields = ['profile_id','employer_name', 'street_name','federal_employer_identification_number', 'city', 'state', 'country', 'zipcode', 'email', 'number_of_employer', 'department','location']

class EmployerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer_Profile
        fields = '__all__'

class EmployeeDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee_Details
        fields = '__all__'


class GetEmployeeDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee_Details
        fields = '__all__'


class GetEmployerDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer_Profile
        fields = '__all__'

# class IWODetailsPDFSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = IWO_Details_PDF
#         fields = '__all__'