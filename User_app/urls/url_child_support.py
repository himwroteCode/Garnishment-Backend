from django.urls import path
from ..views.view_child_support import *
from ..views import *

urlpatterns = [
    path('GetResultDetails/<int:employer_id>/', AllGarnishmentResultDetailView.as_view(), name='GetResultDetails'),
    path('Gcalculations/<int:employer_id>/<int:employee_id>/', SingleCalculationDetailView.as_view(), name='SingleCalculationDetailView'),
    path('CalculationDataView', CalculationDataView.as_view(), name='Calculation Data'),
    path('ChildSupportBatchResult/<str:batch_id', ChildSupportGarnishmentBatchResult.as_view(), name='Calculation Data'),

    
]