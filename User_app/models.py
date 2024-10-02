# models.py
from django.contrib.auth.models import AbstractUser ,AbstractBaseUser ,BaseUserManager
from django.db import models



# Employer_Profile details
class Employer_Profile(AbstractBaseUser):
    employer_id = models.AutoField(primary_key=True)
    employer_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True)
    street_name = models.CharField(max_length=255, null=True, blank=True)
    federal_employer_identification_number = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    zipcode = models.CharField(max_length=10, null=True, blank=True)
    number_of_employees = models.IntegerField(null=True, blank=True)
    department = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'employer_name']

    def __str__(self):
        return self.username
    

class Calculation_data_results(models.Model):
    employee_id=models.IntegerField()
    employer_id=models.IntegerField()
    fedral_income_tax=models.FloatField()
    social_and_security=models.FloatField()
    medicare_tax=models.FloatField()
    state=models.CharField(max_length=255)
    state_taxes=models.FloatField()
    earnings= models.FloatField()
    support_second_family=models.BooleanField()
    garnishment_fees=models.FloatField()
    arrears_greater_than_12_weeks=models.BooleanField()
    amount_to_withhold_child1=models.FloatField(null=True, blank=True)
    amount_to_withhold_child2 =models.FloatField(null=True, blank=True)
    amount_to_withhold_child3=models.FloatField(null=True, blank=True)
    amount_to_withhold_child4=models.FloatField(null=True, blank=True)
    amount_to_withhold_child5=models.FloatField(null=True, blank=True)
    arrears_amt_Child1=models.FloatField(null=True, blank=True)
    arrears_amt_Child2 =models.FloatField(null=True, blank=True)
    arrears_amt_Child3 =models.FloatField(null=True, blank=True)
    arrears_amt_Child4 =models.FloatField(null=True, blank=True)
    arrears_amt_Child5 =models.FloatField(null=True, blank=True)
    number_of_arrear= models.IntegerField(null=True, blank=True)
    number_of_garnishment=models.IntegerField(null=True, blank=True)
    allowable_disposable_earnings=models.FloatField()
    withholding_available=models.FloatField()
    other_garnishment_amount=models.FloatField()
    amount_left_for_arrears=models.FloatField()
    allowed_amount_for_other_garnishment=models.FloatField()

class Employee_Details(models.Model):
    employee_id = models.AutoField(primary_key=True)
    employer_id = models.IntegerField()
    employee_name = models.CharField(max_length=255)
    department = models.CharField(max_length=255)
    pay_cycle = models.CharField(max_length=255)
    number_of_garnishment = models.IntegerField()
    location = models.CharField(max_length=255)
    def __str__(self):
        return self.employee_name
  
class Tax_details(models.Model):
    tax_id = models.AutoField(primary_key=True)
    employer_id=models.IntegerField(unique=True)
    fedral_income_tax =models.FloatField()
    social_and_security =models.FloatField()
    medicare_tax= models.FloatField()
    state_tax =models.FloatField()
    SDI_tax=models.FloatField()
    mexico_tax=models.FloatField()
    workers_compensation=models.FloatField()
    medical_insurance=models.FloatField()
    contribution=models.FloatField()
    united_way_contribution=models.FloatField()


class IWOPDFFile(models.Model):
    pdf_name = models.CharField(max_length=100)
    pdf = models.FileField(upload_to='pdfs/')
    employer_id=models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
 
 
class IWO_Details_PDF(models.Model):
    IWO_ID = models.AutoField(primary_key=True)
    employer_id=models.IntegerField(unique=True)
    employee_id=models.IntegerField()
    IWO_Status =models.CharField(max_length=250)


class Department(models.Model):
    department_id = models.AutoField(primary_key=True)
    department_name=models.CharField(max_length=250)
    employer_id=models.IntegerField(unique=True)

class Location(models.Model):
    location_id = models.AutoField(primary_key=True)
    employer_id=models.IntegerField(unique=True)
    state=models.CharField(max_length=250)
    city=models.CharField(max_length=250)
    # street=models.CharField(max_length=250)

class Garcalculation_data(models.Model):
    employee_id = models.IntegerField()
    employer_id = models.IntegerField()
    employee_name=models.CharField(max_length=255)
    garnishment_fees = models.FloatField()
    earnings = models.FloatField()
    support_second_family = models.BooleanField()
    arrears_greater_than_12_weeks = models.BooleanField(null=True, blank=True)
    amount_to_withhold_child1=models.FloatField(null=True, blank=True)
    amount_to_withhold_child2 =models.FloatField(null=True, blank=True)
    amount_to_withhold_child3=models.FloatField( null=True, blank=True)
    amount_to_withhold_child4=models.FloatField(null=True, blank=True )
    amount_to_withhold_child5=models.FloatField( null=True, blank=True)
    arrears_amt_Child1=models.FloatField(null=True, blank=True)
    arrears_amt_Child2 =models.FloatField(null=True, blank=True)
    arrears_amt_Child3 =models.FloatField(null=True, blank=True)
    arrears_amt_Child4 =models.FloatField(null=True, blank=True)
    arrears_amt_Child5 =models.FloatField(null=True, blank=True)
    number_of_garnishment= models.IntegerField()
    number_of_arrear= models.IntegerField()
    order_id=models.IntegerField()
    state=models.CharField(max_length=255)
    federal_income_tax =models.FloatField()
    social_tax =models.FloatField()
    medicare_tax= models.FloatField()
    state_tax =models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

class CalculationResult(models.Model):
    employee_id = models.IntegerField()
    employer_id = models.IntegerField()
    result = models.FloatField()  
    net_pay = models.FloatField()
    amount_to_withhold_child1=models.FloatField(null=True, blank=True)
    amount_to_withhold_child2 =models.FloatField(null=True, blank=True)
    amount_to_withhold_child3=models.FloatField( null=True, blank=True)
    amount_to_withhold_child4=models.FloatField(null=True, blank=True )
    amount_to_withhold_child5=models.FloatField( null=True, blank=True)
    arrears_amt_Child1=models.FloatField(null=True, blank=True)
    arrears_amt_Child2 =models.FloatField(null=True, blank=True)
    arrears_amt_Child3 =models.FloatField(null=True, blank=True)
    arrears_amt_Child4 =models.FloatField(null=True, blank=True)
    arrears_amt_Child5 =models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class LogEntry(models.Model):
    action = models.CharField(max_length=255)
    details = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    additional_info = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.timestamp} - {self.user} - {self.action}'
    
class application_activity(models.Model):
    action = models.CharField(max_length=255)
    details = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

class single_student_loan_result(models.Model):
    employee_id = models.IntegerField()
    employer_id = models.IntegerField()
    net_pay = models.FloatField()  
    garnishment_amount= models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

class multiple_student_loan_result(models.Model):
    employee_id = models.IntegerField()
    employer_id = models.IntegerField()
    net_pay = models.FloatField()  
    garnishment_amount= models.FloatField()
    StudentLoanAmount1= models.FloatField()
    StudentLoanAmount2= models.FloatField()
    StudentLoanAmount3= models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

class single_student_loan_data(models.Model):
    employee_id = models.IntegerField()
    employer_id = models.IntegerField()
    employee_name=models.CharField(max_length=255)
    earnings = models.FloatField()  
    garnishment_fees= models.IntegerField()
    order_id=models.IntegerField()
    federal_income_tax= models.FloatField()
    social_and_security_tax= models.FloatField()
    medicare_tax= models.FloatField()
    state_tax= models.FloatField()
    SDI_tax= models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

class multiple_student_loan_data(models.Model):
    employee_id = models.IntegerField()
    employer_id = models.IntegerField()
    employee_name=models.CharField(max_length=255)
    earnings = models.FloatField()  
    garnishment_fees= models.FloatField()
    order_id=models.IntegerField()
    federal_income_tax= models.FloatField()
    social_and_security_tax= models.FloatField()
    medicare_tax= models.FloatField()
    state_tax= models.FloatField()
    SDI_tax= models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

class multiple_student_loan_data_and_result(models.Model):
    employee_id = models.IntegerField()
    employer_id = models.IntegerField()
    employee_name=models.CharField(max_length=255)
    earnings = models.FloatField()  
    federal_income_tax= models.FloatField()
    social_and_security_tax= models.FloatField()
    medicare_tax= models.FloatField()
    state_tax= models.FloatField()
    SDI_tax= models.FloatField()
    total_tax=models.FloatField()
    garnishment_fees= models.FloatField()
    disposable_earnings= models.FloatField()
    allowable_disposable_earning= models.FloatField()
    twentyfive_percent_of_earning= models.FloatField()
    fmw= models.FloatField()
    garnishment_amount= models.FloatField()
    StudentLoanAmount1= models.FloatField()
    StudentLoanAmount2= models.FloatField()
    StudentLoanAmount3= models.FloatField()
    net_pay= models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

class single_student_loan_data_and_result(models.Model):
    employee_id = models.IntegerField()
    employer_id = models.IntegerField()
    employee_name=models.CharField(max_length=255)
    earnings = models.FloatField()  
    federal_income_tax= models.FloatField()
    social_and_security_tax= models.FloatField()
    medicare_tax= models.FloatField()
    state_tax= models.FloatField()
    SDI_tax= models.FloatField()
    total_tax=models.FloatField()
    garnishment_fees= models.FloatField()
    disposable_earnings= models.FloatField()
    allowable_disposable_earning= models.FloatField()
    fifteen_percent_of_eraning= models.FloatField()
    fmw= models.FloatField()
    difference=models.FloatField()
    garnishment_amount= models.FloatField()
    net_pay= models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

class federal_loan_case_data(models.Model):
    employee_id = models.IntegerField()
    employer_id = models.IntegerField()
    employee_name=models.CharField(max_length=255)
    earnings = models.FloatField()  
    garnishment_fees= models.FloatField()
    pay_period = models.CharField(max_length=255)
    filing_status = models.CharField(max_length=255)
    no_of_exception = models.IntegerField()
    federal_income_tax =models.FloatField()
    local_tax =models.FloatField()
    social_and_security =models.FloatField()
    medicare_tax= models.FloatField()
    state_tax =models.FloatField()
    workers_compensation=models.FloatField()
    medical_insurance=models.FloatField()
    contribution=models.FloatField()
    united_way_contribution=models.FloatField()
    order_id=models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

class federal_tax_data_and_result(models.Model):
    employee_id = models.IntegerField()
    employer_id = models.IntegerField()
    employee_name=models.CharField(max_length=255)
    earnings = models.FloatField()  
    garnishment_fees= models.IntegerField()
    pay_period = models.CharField(max_length=255)
    filing_status = models.CharField(max_length=255)
    no_of_exception = models.IntegerField()
    fedral_income_tax =models.FloatField()
    social_and_security =models.FloatField()
    medicare_tax= models.FloatField()
    state_tax =models.FloatField()
    local_tax =models.FloatField()
    workers_compensation=models.FloatField()
    medical_insurance=models.FloatField()
    contribution=models.FloatField()
    united_way_contribution=models.FloatField()
    total_tax=models.FloatField()
    disposable_earnings=models.FloatField()
    exempt_amount=models.FloatField()
    amount_deduct=models.FloatField()
    net_pay=models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

class federal_case_result(models.Model):
    employee_id = models.IntegerField()
    employer_id = models.IntegerField()
    net_pay = models.FloatField()  
    result= models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

class single_filing_status(models.Model):
    pay_period = models.CharField(max_length=255) 
    exemptions_1= models.FloatField() 
    exemptions_2= models.FloatField()  
    exemptions_3= models.FloatField()  
    exemptions_4= models.FloatField()  
    exemptions_5= models.FloatField()   
    exemptions_6= models.FloatField()   
    morethan7= models.CharField(max_length=255)

class head_of_household(models.Model):
    pay_period = models.CharField(max_length=255)
    exemptions_1= models.FloatField() 
    exemptions_2= models.FloatField()  
    exemptions_3= models.FloatField()  
    exemptions_4= models.FloatField()  
    exemptions_5= models.FloatField()   
    exemptions_6= models.FloatField()   
    morethan7= models.CharField(max_length=255)


class married_filing_joint_return(models.Model):
    pay_period = models.CharField(max_length=255) 
    exemptions_1= models.FloatField() 
    exemptions_2= models.FloatField()  
    exemptions_3= models.FloatField()  
    exemptions_4= models.FloatField()  
    exemptions_5= models.FloatField()  
    exemptions_6= models.FloatField()    
    morethan7= models.CharField(max_length=255)

class married_filing_sepearte_return(models.Model):
    pay_period = models.CharField(max_length=255)
    exemptions_1= models.FloatField() 
    exemptions_2= models.FloatField()  
    exemptions_3= models.FloatField()  
    exemptions_4= models.FloatField()  
    exemptions_5= models.FloatField() 
    exemptions_6= models.FloatField()     
    morethan7= models.CharField(max_length=255)

class setting(models.Model):
    employer_id=models.IntegerField()
    modes=models.BooleanField()
    visibilitys=models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)



class APICallLog(models.Model):
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f'{self.path} - {self.method} - {self.timestamp}'

# class APICallLog(models.Model):
#     endpoint = models.CharField(max_length=255)
#     date = models.DateField(auto_now_add=True)
#     count = models.PositiveIntegerField(default=1)

#     def __str__(self):
#         return f'{self.endpoint} - {self.date} - {self.count}'