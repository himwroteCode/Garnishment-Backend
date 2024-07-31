
def ccpa_limit(support_second_family,arrears_greater_than_12_weeks):
    if support_second_family and arrears_greater_than_12_weeks:
        ccpa_limit = 0.55
    elif not support_second_family and not arrears_greater_than_12_weeks:
        ccpa_limit = 0.60
    elif not support_second_family and arrears_greater_than_12_weeks:
        ccpa_limit = 0.65
    elif  support_second_family and not arrears_greater_than_12_weeks:
        ccpa_limit = 0.50
    return(ccpa_limit)

