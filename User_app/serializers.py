from rest_framework import serializers
from .models import Employer_Profile,Employee_Details,IWO_Details_PDF,federal_case_result,married_filing_sepearte_return,married_filing_joint_return,head_of_household,Department,CalculationResult, Location,Tax_details,LogEntry,IWOPDFFile,single_student_loan_result,multiple_student_loan_result,single_filing_status


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


class GetEmployerDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer_Profile
        fields = '__all__'


class PDFFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = IWOPDFFile
        fields = '__all__'

# class IWODetailsPDFSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = IWO_Details_PDF
#         fields = '__all__'

# serializers.py



class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class TaxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tax_details
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
    
class MultipleStudentLoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = multiple_student_loan_result
        fields = '__all__'

class SingleStudentLoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = single_student_loan_result
        fields = '__all__'

class TaxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tax_details
        fields = '__all__'

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalculationResult
        fields = '__all__'

class single_filing_status_Serializer(serializers.ModelSerializer):
    class Meta:
        model = single_filing_status
        fields = '__all__'

class head_of_household_Serializer(serializers.ModelSerializer):
    class Meta:
        model = head_of_household
        fields = '__all__'

class married_filing_joint_return_Serializer(serializers.ModelSerializer):
    class Meta:
        model = married_filing_joint_return
        fields = '__all__'
   

class married_filing_sepearte_return_Serializer(serializers.ModelSerializer):
    class Meta:
        model = married_filing_sepearte_return
        fields = '__all__'

class federal_case_result_Serializer(serializers.ModelSerializer):
    class Meta:
        model = federal_case_result
        fields = '__all__'