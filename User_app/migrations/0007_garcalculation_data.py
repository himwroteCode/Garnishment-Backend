# Generated by Django 4.2.1 on 2024-06-18 03:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('User_app', '0006_remove_location_street'),
    ]

    operations = [
        migrations.CreateModel(
            name='Garcalculation_data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_id', models.IntegerField()),
                ('employer_id', models.IntegerField()),
                ('earning', models.FloatField()),
                ('garnishment_fees', models.FloatField()),
                ('arrears_greater_than_12_weeks', models.BooleanField()),
                ('total_amount_to_withhold', models.FloatField()),
                ('have_any_arrears', models.BooleanField()),
                ('arrears_amt', models.FloatField()),
            ],
        ),
    ]
