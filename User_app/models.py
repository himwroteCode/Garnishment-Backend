# models.py
from django.contrib.auth.models import AbstractUser ,AbstractBaseUser ,BaseUserManager
from django.db import models



class CustomUser(AbstractUser):
    name = models.CharField(max_length=100)

    # Remove the custom related_name and use the default ones
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='customuser_set',
        verbose_name='groups',
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='customuser_set',
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
    )

class Profile(models.Model):
    user = models.OneToOneField(CustomUser , on_delete=models.CASCADE)
    forget_password_token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)




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


class Employee_Details(models.Model):
    employee_id = models.AutoField(primary_key=True)
    employer_id = models.IntegerField()
    employee_name = models.CharField(max_length=255)
    department = models.CharField(max_length=255)
    net_pay = models.FloatField()
    minimun_wages = models.FloatField()  
    pay_cycle = models.CharField()
    number_of_garnishment = models.IntegerField()
    location = models.CharField(max_length=255)
    def __str__(self):
        return self.employee_name
  
class Tax_details(models.Model):
    tax_id = models.AutoField(primary_key=True)
    employer_id=models.IntegerField()
    fedral_income_tax =models.FloatField()
    social_and_security =models.FloatField()
    medicare_tax= models.FloatField()
    state_taxes =models.FloatField()


class PDFFile(models.Model):
    name = models.CharField(max_length=255)
    data = models.BinaryField()

    def __str__(self):
        return self.name

class IWO_Details_PDF(models.Model):
    IWO_ID = models.AutoField(primary_key=True)
    employer_id=models.IntegerField()
    employee_id=models.IntegerField()
    IWO_Status =models.CharField(max_length=250)

class Department(models.Model):
    department_id = models.AutoField(primary_key=True)
    department_name=models.CharField(max_length=250)
    employer_id=models.IntegerField()

class Location(models.Model):
    location_id = models.AutoField(primary_key=True)
    employer_id=models.IntegerField()
    state=models.CharField(max_length=250)
    city=models.CharField(max_length=250)
    # street=models.CharField(max_length=250)



class Garcalculation_data(models.Model):
    employee_id = models.IntegerField()
    employer_id = models.IntegerField()
    garnishment_fees = models.FloatField()
    arrears_greater_than_12_weeks = models.BooleanField()
    support_second_family = models.BooleanField()
    total_amount_to_withhold = models.FloatField()
    have_any_arrears = models.BooleanField()
    arrears_amt = models.FloatField()

class CalculationResult(models.Model):
    employee_id = models.IntegerField()
    employer_id = models.IntegerField()
    result = models.FloatField()   


class LogEntry(models.Model):
    action = models.CharField(max_length=255)
    details = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    additional_info = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.timestamp} - {self.user} - {self.action}'



