from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User


ZHK_CHOICES = [
        ('zhk', 'ЖК'),
        ('zhsk', 'ЖСК')
    ]


class Cooperative(models.Model):
    cooperative_user = models.ForeignKey(User, on_delete=models.CASCADE)
    cooperative_type = models.CharField(max_length=4, choices=ZHK_CHOICES)
    cooperative_name = models.CharField(max_length=255)
    cooperative_itn = models.CharField(max_length=12)
    cooperative_address = models.CharField(max_length=255)
    cooperative_email_address = models.EmailField()
    cooperative_telephone_number = PhoneNumberField(null=False, blank=False, unique=True)
