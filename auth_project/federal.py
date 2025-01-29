import os
import json
import re


single_filing_status= [
        {
            "Pay Period": "Daily",
            "0": 57.69,
            "1": 77.31,
            "2": 96.93,
            "3": 116.55,
            "4": 136.17,
            "5": 155.79,
            "6": "57.69 plus 19.62 for each exemption"
        },
        {
            "Pay Period": "Weekly",
            "0": 288.46,
            "1": 386.54,
            "2": 484.62,
            "3": 582.7,
            "4": 680.78,
            "5": 778.86,
            "6": "288.46 plus 98.08 for each exemption"
        },
        {
            "Pay Period": "Biweekly",
            "0": 576.92,
            "1": 773.07,
            "2": 969.22,
            "3": 1165.37,
            "4": 1361.52,
            "5": 1557.67,
            "6": "576.92 plus 196.15 for each exemption"
        },
        {
            "Pay Period": "Semimonthly",
            "0": 625,
            "1": 837.5,
            "2": 1050,
            "3": 1262.5,
            "4": 1475,
            "5": 1687.5,
            "6": "625.00 plus 212.50 for each exemption"
        },
        {
            "Pay Period": "Monthly",
            "0": 1250,
            "1": 1675,
            "2": 2100,
            "3": 2525,
            "4": 2950,
            "5": 3375,
            "6": "1250.00 plus 425.00 for each exemption"
        }
    ]

additional_exempt_amt=[
        {
            "no_of_exemption": 1,
            "filing_status": ["single_filing_status", "head_of_household"],
            "daily": 7.69,
            "weekly": 38.46,
            "biweekly": 76.92,
            "semimonthly": 83.33,
            "monthly": 166.67
        },
        {
            "no_of_exemption": 2,
            "filing_status": ["single_filing_status", "head_of_household"],
            "daily": 15.38,
            "weekly": 76.92,
            "biweekly": 153.85,
            "semimonthly": 166.67,
            "monthly": 333.33
        },
        {
            "no_of_exemption": 1,
            "filing_status": ["Any Other Filing Status"],
            "daily": 6.15,
            "weekly": 30.77,
            "biweekly": 61.54,
            "semimonthly": 66.67,
            "monthly": 133.33
        },
        {
            "No_of_Exemption": 2,
            "filing_status": ["Any Other Filing Status"],
            "daily": 12.31,
            "weekly": 61.54,
            "biweekly": 123.08,
            "semimonthly": 133.33,
            "monthly": 266.67
        },
        {
            "No_of_Exemption": 3,
            "filing_status": ["Any Other Filing Status"],
            "daily": 18.46,
            "weekly": 92.31,
            "biweekly": 184.62,
            "semimonthly": 200,
            "monthly": 400
        },
        {
            "No_of_Exemption": 4,
            "filing_status": ["Any Other Filing Status"],
            "daily": 24.62,
            "weekly": 123.08,
            "biweekly": 246.15,
            "semimonthly": 266.67,
            "monthly": 533.33
        }
    ]
    

class federal_tax_calculation():
    """ Calculate Federal Tax based on the given filing status and number of exceptions """

    # def get_file_data(self, file_path):
    #     with open(file_path, 'r') as file:
    #         data = json.load(file)
    #     return data


    def get_total_exemption(self, request):
        age = request.get('age')
        dependent_age= request.get('dependent_age')
        disabiltiy = request.get('disability')
        dependent_disability = request.get('dependent_disability')
        if (age>=65 and disabiltiy==True) or (dependent_age>=65 and dependent_disability==True) :
            number_of_exemption=2
        elif (age<65 and disabiltiy==False) or (dependent_age>=65 and dependent_disability==False):
            number_of_exemption=1
        elif(age>=65 and disabiltiy==True) or (dependent_age>=65 and dependent_disability==False):
            number_of_exemption=1
        return number_of_exemption

    def get_additional_exempt(self, record):

        pay_period=record.get('pay_period').lower()
        filing_status=record.get('filing_status')

        file_path='/content/additional_exempt_amount.json'
        data = additional_exempt_amt

        
        get_total_exemption=self.get_total_exemption(record)
        # print("get_total_exemption11",get_total_exemption)
        additional_exempt  = next(
            (item[pay_period] for item in data if filing_status in item.get("filing_status")  and item.get("no_of_exemption") == get_total_exemption),None
        )
        # print("additional_exempt",additional_exempt)

        return additional_exempt

    def get_standard_exempt_amt(self, record):

        filing_status=record.get('filing_status')
        no_of_exception=record.get('no_of_exception')
        pay_period=record.get('pay_period')

        # Check if the number of exceptions is greater than 5
        exempt= 6 if no_of_exception >5 else no_of_exception

        # file_path='/content/single_filing_status.json'
        # data = self.get_file_data(file_path)
        status_data = single_filing_status

        # Accessing federal tax data
        if no_of_exception <=5:
            semimonthly_data = next((item for item in status_data if item["Pay Period"].lower() == pay_period.lower()), None)
            exempt_amount = semimonthly_data.get(str(exempt))
        elif no_of_exception >5:
            semimonthly_data = next((item for item in status_data if item["Pay Period"].lower() == pay_period.lower()), None)
            print("semimonthly_data",semimonthly_data)
            exemp_amt = semimonthly_data.get(str(exempt))
            print("exemp_amt",exemp_amt)
            exempt_amount  = re.findall(r'\d+\.?\d*',exemp_amt)
            exempt1=float(exempt_amount[0])
            exempt2=float(exempt_amount[1])
            exempt_amount=round((exempt1+(exempt2*no_of_exception)),2)
            # print("Single exempt_amount",exempt_amount)
        return exempt_amount


class federal_tax(federal_tax_calculation):

    def calculate(self, record):


        no_of_exception=record.get('no_of_exception')
        age=record.get('age')
        disability=record.get('disability')
        dependent_age=record.get('dependent_age')
        dependent_disability=record.get('dependent_disability')

        gross_pay = record.get('gross_pay')

        if (age>=65 and disability==True) or (age>=65 and disability==False) or (age<65 and disability==True):
            exempt_amount=self.get_additional_exempt(record)
            tax_payer_exempt_amt=exempt_amount*no_of_exception
            # print("tax_payer_exempt_amt",tax_payer_exempt_amt)
        else:
            tax_payer_exempt_amt=0
        if (dependent_age>=65 and dependent_disability==False) or (dependent_age>=65 and dependent_disability==True) or (dependent_age<65 and dependent_disability==True):
            exempt_amount=self.get_additional_exempt(record)
            # print("dependent exempt_amount",exempt_amount)

            dependent_exempt_amt=exempt_amount*no_of_exception
            # print("dependent_exempt_amt",dependent_exempt_amt)
        else:
            dependent_exempt_amt=0
        get_total_exemption=self.get_total_exemption(record)
        standard_exempt_amt=self.get_standard_exempt_amt(record)
        # Calculate the amount to deduct
        total_exempt_amt=standard_exempt_amt+tax_payer_exempt_amt+dependent_exempt_amt
        # print("total_exempt_amt",total_exempt_amt)
        amount_deduct = round((gross_pay-total_exempt_amt), 2)
        # print("amount_deduct",amount_deduct)
        amount_deduct = amount_deduct if amount_deduct > 0 else 0
        return ( {"result" : amount_deduct})

        # except Exception as e:
        #     return Response({"error": str(e), "status code" :status.HTTP_500_INTERNAL_SERVER_ERROR})



 

record = {
    "employee_id": "EE009",
    "employer_id": "EMP1009",
    "employee_name": "Nick Rode",
    "pay_period": "Semimonthly",
    "no_of_exception": 1,
    "filing_status": "single_filing_status",
    "gross_pay": 2086.06 ,
    "order_id": "B101",
    "age": 65,
    "disability": True,
    "dependent_age": 65,
    "dependent_disability": True
}


# print("get_file_data",federal_tax().get_file_data('/content/single_filing_status.json'))
# print("get_single_exempt_amt",federal_tax_calculation().get_standard_exempt_amt(record))
# print("get_total_exemption",federal_tax_calculation().get_total_exemption(record))
# print("get_additional_exempt",federal_tax().get_additional_exempt(record))

print("result:",federal_tax().calculate(record))
