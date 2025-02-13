# Generated by Django 5.0.9 on 2025-01-27 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('User_app', '0052_garnishment_order'),
    ]

    operations = [
        migrations.RenameField(
            model_name='payroll',
            old_name='deductions',
            new_name='deduction_401k',
        ),
        migrations.RenameField(
            model_name='payroll',
            old_name='taxes_federal_income_tax',
            new_name='deduction_medical_insurance',
        ),
        migrations.RenameField(
            model_name='payroll',
            old_name='taxes_local_tax',
            new_name='deduction_sdi',
        ),
        migrations.RenameField(
            model_name='payroll',
            old_name='taxes_medicare_tax',
            new_name='deduction_union_dues',
        ),
        migrations.RenameField(
            model_name='payroll',
            old_name='taxes_sdi',
            new_name='deduction_voluntary',
        ),
        migrations.RenameField(
            model_name='payroll',
            old_name='taxes_state_tax',
            new_name='tax_federal_income_tax',
        ),
        migrations.RemoveField(
            model_name='garnishment_order',
            name='cid',
        ),
        migrations.AddField(
            model_name='payroll',
            name='tax_local_tax',
            field=models.DecimalField(decimal_places=2, default=10, max_digits=250),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='payroll',
            name='tax_medicare_tax',
            field=models.DecimalField(decimal_places=2, default=10, max_digits=250),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='payroll',
            name='tax_social_security',
            field=models.CharField(default=10, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='payroll',
            name='tax_state_tax',
            field=models.DecimalField(decimal_places=2, default=10, max_digits=250),
            preserve_default=False,
        ),
    ]
