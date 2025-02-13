# Generated by Django 5.0.9 on 2025-01-20 12:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('User_app', '0032_delete_employee_details_delete_federal_case_result_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='employer_profile',
            old_name='bank_account_number',
            new_name='city',
        ),
        migrations.RenameField(
            model_name='employer_profile',
            old_name='bank_name',
            new_name='country',
        ),
        migrations.RenameField(
            model_name='employer_profile',
            old_name='cid',
            new_name='employer_id',
        ),
        migrations.RemoveField(
            model_name='employer_profile',
            name='company_name',
        ),
        migrations.RemoveField(
            model_name='employer_profile',
            name='ein',
        ),
        migrations.RemoveField(
            model_name='employer_profile',
            name='registered_address',
        ),
        migrations.AddField(
            model_name='employee_detail',
            name='employer_id',
            field=models.CharField(default=101, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='employer_profile',
            name='department',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='employer_profile',
            name='employer_name',
            field=models.CharField(default='ABS', max_length=100),
        ),
        migrations.AddField(
            model_name='employer_profile',
            name='federal_employer_identification_number',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='employer_profile',
            name='number_of_employees',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='employer_profile',
            name='state',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='employer_profile',
            name='street_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='employer_profile',
            name='username',
            field=models.CharField(default='USN', max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='employer_profile',
            name='email',
            field=models.EmailField(default='rtt@gmail.com', max_length=254, unique=True),
        ),
    ]
