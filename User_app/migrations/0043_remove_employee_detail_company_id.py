# Generated by Django 5.1.5 on 2025-01-23 07:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('User_app', '0042_company_details_registered_address'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employee_detail',
            name='company_id',
        ),
    ]
