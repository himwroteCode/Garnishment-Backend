# Generated by Django 4.2.1 on 2024-06-19 09:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('User_app', '0008_calculationresult'),
    ]

    operations = [
        migrations.RenameField(
            model_name='calculationresult',
            old_name='CalculationResult',
            new_name='result',
        ),
    ]
