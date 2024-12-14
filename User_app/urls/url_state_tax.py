from django.urls import path
from ..views.view_state_tax import *


urlpatterns = [
    path('state_tax_case/',state_tax, name='state_tax_case'),

]