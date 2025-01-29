import csv
import pandas as pd
import math
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from User_app.models import Employee_Detail, garnishment_order, company_details

@csrf_exempt
def upsert_employees_data(request):
    if request.method == 'POST' and request.FILES.get('file'):
        print("called")
        file = request.FILES['file']
        updated_employees = []
        added_employees = []

        try:
            if file.name.endswith('.csv'):
                data = list(csv.DictReader(file.read().decode('utf-8').splitlines()))
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
                data = df.to_dict(orient='records')
            else:
                return JsonResponse({'error': 'Unsupported file format. Please upload a CSV or Excel file.'}, status=400)

            for row in data:
                row = {k: v for k, v in row.items() if k and not k.startswith('Unnamed:')}
                updated_row = {}

                for k, v in row.items():
                    if k == "social_security_number" and isinstance(v, float) and math.isnan(v):
                        updated_row[k] = ""
                    else:
                        updated_row[k] = v

                try:
                    # Check if the employee already exists
                    employee_detail = Employee_Detail.objects.get(ee_id=updated_row['ee_id'], cid=updated_row['cid'])

                    has_changes = False
                    for field_name in [
                        'age', 'social_security_number', 'is_blind', 'home_state', 'work_state', 'gender', 'pay_period',
                        'number_of_exemptions', 'filing_status', 'marital_status', 'number_of_student_default_loan',
                        'support_second_family', 'spouse_age', 'is_spouse_blind'
                    ]:
                        incoming_value = updated_row.get(field_name)
                        if isinstance(getattr(employee_detail, field_name), bool) and isinstance(incoming_value, str):
                            incoming_value = incoming_value.lower() in ['true', '1', 'yes']
                        elif isinstance(getattr(employee_detail, field_name), bool):
                            incoming_value = bool(incoming_value)
                        if getattr(employee_detail, field_name) != incoming_value:
                            has_changes = True
                            break

                    if has_changes:
                        for field_name in [
                            'age', 'social_security_number', 'is_blind', 'home_state', 'work_state', 'gender', 'pay_period',
                            'number_of_exemptions', 'filing_status', 'marital_status', 'number_of_student_default_loan',
                            'support_second_family', 'spouse_age', 'is_spouse_blind'
                        ]:
                            incoming_value = updated_row.get(field_name)
                            if isinstance(getattr(employee_detail, field_name), bool) and isinstance(incoming_value, str):
                                incoming_value = incoming_value.lower() in ['true', '1', 'yes']
                            elif isinstance(getattr(employee_detail, field_name), bool):
                                incoming_value = bool(incoming_value)
                            setattr(employee_detail, field_name, incoming_value)

                        # Update timestamp when an existing record is modified
                        employee_detail.record_updated = datetime.now()
                        employee_detail.save()
                        updated_employees.append(employee_detail.ee_id)

                except Employee_Detail.DoesNotExist:
                    # Insert new employee record with the current timestamp
                    Employee_Detail.objects.create(
                        ee_id=updated_row['ee_id'],
                        cid=updated_row['cid'],
                        age=updated_row.get('age'),
                        social_security_number=updated_row.get('social_security_number'),
                        is_blind=updated_row.get('is_blind').lower() in ['true', '1', 'yes'] if isinstance(updated_row.get('is_blind'), str) else updated_row.get('is_blind'),
                        home_state=updated_row.get('home_state'),
                        work_state=updated_row.get('work_state'),
                        gender=updated_row.get('gender'),
                        pay_period=updated_row.get('pay_period'),
                        number_of_exemptions=updated_row.get('number_of_exemptions'),
                        filing_status=updated_row.get('filing_status'),
                        marital_status=updated_row.get('marital_status'),
                        number_of_student_default_loan=updated_row.get('number_of_student_default_loan'),
                        support_second_family=updated_row.get('support_second_family').lower() in ['true', '1', 'yes'] if isinstance(updated_row.get('support_second_family'), str) else updated_row.get('support_second_family'),
                        spouse_age=updated_row.get('spouse_age'),
                        is_spouse_blind=updated_row.get('is_spouse_blind').lower() in ['true', '1', 'yes'] if isinstance(updated_row.get('is_spouse_blind'), str) else updated_row.get('is_spouse_blind'),
                        record_import=datetime.now()  # Set timestamp for new records
                    )
                    added_employees.append(updated_row['ee_id'])

            if not updated_employees and not added_employees:
                return JsonResponse({'message': 'No data was updated or inserted.'}, status=200)

            response_data = []

            if added_employees:
                response_data.append({
                    'message': 'Employee(s) imported successfully',
                    'added_employees': added_employees
                })

            if updated_employees:
                response_data.append({
                    'message': 'Employee details updated successfully',
                    'updated_employees': updated_employees
                })

            return JsonResponse({'responses': response_data}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)

#upsert garnishment
@csrf_exempt
def upsert_garnishment_order(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        file_name = file.name
        updated_orders = []
        added_orders = []
        no_change = []

        try:
            # Load file into a DataFrame
            if file_name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file_name.endswith(('.xlsx', '.xls', '.xlsm', '.xlsb', '.odf', '.ods', '.odt')):
                df = pd.read_excel(file)
            else:
                return JsonResponse({"error": "Unsupported file format. Please upload a CSV or Excel file."}, status=400)

            # Format date columns
            date_columns = ['start_date', 'end_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    df[col] = df[col].apply(lambda x: x.date() if not pd.isna(x) else None)

            # Process each row
            for _, row in df.iterrows():
                try:
                    # Skip rows with missing 'cid' or 'eeid'
                    if pd.isna(row['cid']) or pd.isna(row['eeid']):
                        continue

                    # Retrieve existing order
                    order = garnishment_order.objects.filter(cid=row['cid'], eeid=row['eeid']).first()

                    if order:
                        # Check for changes
                        has_changes = (
                            order.case_id != row.get('case_id', None) or
                            order.state != row['state'] or
                            order.type != row['type'] or
                            order.sdu != row.get('sdu', None) or
                            order.start_date != row.get('start_date', None) or
                            order.end_date != row.get('end_date', None) or
                            float(order.amount) != float(row['amount']) or
                            order.arrear_greater_than_12_weeks != row['arrear_greater_than_12_weeks'] or
                            float(order.arrear_amount) != float(row['arrear_amount'])
                        )

                        if has_changes:
                            # Update order
                            order.case_id = row.get('case_id', None)
                            order.state = row['state']
                            order.type = row['type']
                            order.sdu = row.get('sdu', None)
                            order.start_date = row.get('start_date', None)
                            order.end_date = row.get('end_date', None)
                            order.amount = row['amount']
                            order.arrear_greater_than_12_weeks = row['arrear_greater_than_12_weeks']
                            order.arrear_amount = row['arrear_amount']
                            order.record_updated = datetime.now()
                            order.save()
                            updated_orders.append({'cid': order.cid, 'eeid': order.eeid})
                        else:
                            no_change.append({'cid': order.cid, 'eeid': order.eeid})
                    else:
                        # Create new order
                        garnishment_order.objects.create(
                            cid=row['cid'],
                            eeid=row['eeid'],
                            case_id=row.get('case_id', None),
                            state=row['state'],
                            type=row['type'],
                            sdu=row.get('sdu', None),
                            start_date=row.get('start_date', None),
                            end_date=row.get('end_date', None),
                            amount=row['amount'],
                            arrear_greater_than_12_weeks=row['arrear_greater_than_12_weeks'],
                            arrear_amount=row['arrear_amount'],
                            record_import=datetime.now()
                        )
                        added_orders.append({'cid': row['cid'], 'eeid': row['eeid']})
                except Exception as row_error:
                    # Error is no longer printed in terminal, only logged in exception handling
                    continue

            # Prepare response data
            if added_orders or updated_orders:
                response_data = []
                if added_orders:
                    response_data.append({
                        'message': 'Garnishment orders imported successfully',
                        'added_orders': added_orders
                    })
                if updated_orders:
                    response_data.append({
                        'message': 'Garnishment orders updated successfully',
                        'updated_orders': updated_orders
                    })
                if no_change:
                    response_data.append({
                        'message': 'No change for certain orders',
                        'no_change_orders': no_change
                    })
            else:
                response_data = {'message': 'No changes in data'}

            return JsonResponse({'responses': response_data}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)

#upsert company details
@csrf_exempt
def upsert_company_details(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']  
        file_name = file.name  
        updated_companies = []
        added_companies = []
        unchanged_companies = []  
        new_data_found = False 

        try:
            if file_name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file_name.endswith(('.xlsx', '.xls', '.xlsm', '.xlsb', '.odf', '.ods', '.odt')):
                df = pd.read_excel(file)
            else:
                return JsonResponse({"error": "Unsupported file format. Please upload a CSV or Excel file."}, status=400)

            for _, row in df.iterrows():
                company = company_details.objects.filter(cid=row['cid']).first()

                if company:
                    existing_data = {
                        'ein': str(company.ein).strip() if company.ein else '',
                        'company_name': str(company.company_name).strip() if company.company_name else '',
                        'zipcode': str(company.zipcode).strip() if company.zipcode else '',
                        'state': str(company.state).strip() if company.state else '',
                        'dba_name': str(company.dba_name).strip() if company.dba_name else '',
                        'bank_name': str(company.bank_name).strip() if company.bank_name else '',
                        'bank_account_number': str(company.bank_account_number).strip() if company.bank_account_number else '',
                        'location': str(company.location).strip() if company.location else '',
                        'registered_address': str(company.registered_address).strip() if company.registered_address else ''
                    }

                    file_data = {
                        'ein': str(row['ein']).strip() if row['ein'] else '',
                        'company_name': str(row['company_name']).strip() if row['company_name'] else '',
                        'zipcode': str(row['zipcode']).strip() if row['zipcode'] else '',
                        'state': str(row['state']).strip() if row['state'] else '',
                        'dba_name': str(row['dba_name']).strip() if row['dba_name'] else '',
                        'bank_name': str(row.get('bank_name', '')).strip() if row.get('bank_name') else '',
                        'bank_account_number': str(row.get('bank_account_number', '')).strip() if row.get('bank_account_number') else '',
                        'location': str(row.get('location', '')).strip() if row.get('location') else '',
                        'registered_address': str(row.get('registered_address', '')).strip() if row.get('registered_address') else ''
                    }

                    has_changes = any(existing_data[key] != file_data[key] for key in existing_data)

                    if has_changes:
                        company.ein = row['ein']
                        company.company_name = row['company_name']
                        company.zipcode = row['zipcode']
                        company.state = row['state']
                        company.dba_name = row['dba_name']
                        company.bank_name = row.get('bank_name', None)
                        company.bank_account_number = row.get('bank_account_number', None)
                        company.location = row.get('location', None)
                        company.registered_address = row.get('registered_address', None)
                        company.record_updated = datetime.now()  # Update timestamp
                        company.save()
                        updated_companies.append(company.cid)
                    else:
                        unchanged_companies.append(company.cid)
                else:
                    company_details.objects.create(
                        cid=row['cid'],
                        ein=row['ein'],
                        company_name=row['company_name'],
                        zipcode=row['zipcode'],
                        state=row['state'],
                        dba_name=row['dba_name'],
                        bank_name=row.get('bank_name', None),
                        bank_account_number=row.get('bank_account_number', None),
                        location=row.get('location', None),
                        registered_address=row.get('registered_address', None),
                        record_import=datetime.now()  # Set timestamp on insert
                    )
                    added_companies.append(row['cid'])
                    new_data_found = True  

            response_data = []
            if added_companies:
                response_data.append({
                    'message': 'Company details imported successfully',
                    'added_companies': added_companies
                })
            if updated_companies:
                response_data.append({
                    'message': 'Company details updated successfully',
                    'updated_companies': updated_companies
                })
            if not added_companies and not updated_companies:
                response_data.append({'message': 'No changes found'})

            return JsonResponse({'responses': response_data}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)
