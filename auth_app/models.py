from django.contrib.auth.models import AbstractUser
from django.db import models

class user_data(models.Model):
    username=models.CharField(max_length=50)
    password=models.CharField( max_length=50)

