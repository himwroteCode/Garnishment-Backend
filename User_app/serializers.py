from rest_framework import serializers
from .models import Employer_Profile,multiple_student_loan_data,multiple_garnishment_case_result,Calculation_data_results,single_student_loan_data,federal_loan_case_data,setting,Employee_Detail,multiple_student_loan_data_and_result,single_student_loan_data_and_result,IWO_Details_PDF,federal_tax_data_and_result,LogEntry


# class EmployerProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Employer_Profile
#         fields = ['profile_id','employer_name', 'street_name','federal_employer_identification_number', 'city', 'state', 'country', 'zipcode', 'email', 'number_of_employer', 'department','location']

class EmployerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer_Profile
        fields = '__all__'

class EmployeeDetailsSerializer(serializers.ModelSerializer):

    blind = serializers.BooleanField(required=False, allow_null=True)
    support_second_family = serializers.BooleanField(required=False, allow_null=True)
    spouse_age = serializers.IntegerField(required=False, allow_null=True)
    is_spouse_blind = serializers.BooleanField(required=False, allow_null=True)
    class Meta:
        model = Employee_Detail
        fields = '__all__'




class GetEmployerDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer_Profile
        fields = '__all__'


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = '__all__'

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    
# class MultipleStudentLoanSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = multiple_student_loan_result
#         fields = '__all__'

# class SingleStudentLoanSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = single_student_loan_result
#         fields = '__all__'


# class ResultSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CalculationResult
#         fields = '__all__'

class single_student_loan_data_and_result_Serializer(serializers.ModelSerializer):
    class Meta:
        model = single_student_loan_data_and_result
        fields = '__all__'
        
class multiple_student_loan_data_and_result_Serializer(serializers.ModelSerializer):
    class Meta:
        model = multiple_student_loan_data_and_result
        fields = '__all__'


class federal_case_result_and_data_Serializer(serializers.ModelSerializer):
    class Meta:
        model = federal_tax_data_and_result
        fields = '__all__'


class Calculation_data_results_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Calculation_data_results
        fields = '__all__'


class setting_Serializer(serializers.ModelSerializer):
    class Meta:
        model = setting
        fields = '__all__'


class federal_loan_data_Serializer(serializers.ModelSerializer):
    class Meta:
        model = federal_loan_case_data
        fields = '__all__'

class single_student_loan_data_Serializer(serializers.ModelSerializer):
    class Meta:
        model = single_student_loan_data
        fields = '__all__'

class multiple_student_loan_data_Serializer(serializers.ModelSerializer):
    class Meta:
        model = multiple_student_loan_data
        fields = '__all__'


class multiple_garnishment_data_Serializer(serializers.ModelSerializer):
    class Meta:
        model = multiple_garnishment_case_result
        fields = '__all__'

class APICallCountSerializer(serializers.Serializer):
    date = serializers.DateField()
    count = serializers.IntegerField()

        