from django.db import models

# Create your models here.

class Cooperative(models.Model):
    cooperative_type = models.CharField(max_length=4)
    cooperative_name = models.CharField(max_length=255)
    cooperative_itn = models.CharField(max_length=12)
    cooperative_address = models.CharField(max_length=255)
    cooperative_email_address = models.EmailField()
    cooperative_telephone_number = models.CharField(max_length=16)
