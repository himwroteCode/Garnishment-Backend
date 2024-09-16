"""
URL configuration for auth_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('User/',include('User_app.urls.urls')),
    # path('User/',include('User_app.urls.url_federaltax')),
        path('garnishment', get_schema_view(
        title="Garnishment APIs",
        description="The Garnishment Project API is designed to manage and process employee garnishments efficiently. This API provides secure and streamlined methods for handling garnishment calculations, employee details, and employer data, ensuring compliance with legal requirements.",
        version="1.0.0"
    ), name='garnishment-schema'),

    path('APIWebDoc', TemplateView.as_view(
        template_name='doc.html',
        extra_context={'schema_url':'garnishment-schema'}
    ), name='api_doc'),
]
