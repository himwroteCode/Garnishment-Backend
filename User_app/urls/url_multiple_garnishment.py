from django.urls import path
from ..views.view_multiple_garnishment import *


urlpatterns = [
    path('state_tax_case/',multiple_case_calculation, name='state_tax_case'),
    path('multiple_garnishment_result/<str:employer_id>/<str:employee_id>/',get_multiple_garnishment_case_result.as_view(), name='state_tax_case'),

]