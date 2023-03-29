from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User


MEETING_TYPES = [
    ('regular', 'Очередное'),
    ('irregular', 'Внеочередное')
]

MEETING_FORMATS = [
    ('intramural', 'Очное'),
    ('extramural', 'Заочное')
]

MEETING_STAGES = [
    ('type-format', 'Выбор типа и формата'),
    ('questions', 'Выбор вопросов'),
    ('preparation', 'Стадия подготовки'),
    ('conducting', 'Стадия проведения'),
    ('decision-making', 'Стадия принятия решения'),
]


class Cooperative(models.Model):
    cooperative_user = models.ForeignKey(User, on_delete=models.CASCADE)
    cooperative_name = models.CharField(max_length=255)
    cooperative_itn = models.CharField(max_length=12)
    cooperative_address = models.CharField(max_length=255)
    cooperative_email_address = models.EmailField()
    cooperative_telephone_number = PhoneNumberField(null=False, blank=False, unique=True)
    chairman_name = models.CharField(max_length=255)
    auditor_name = models.CharField(max_length=255)
    auditor_email_address = models.EmailField()


class CooperativeMember(models.Model):
    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE)
    fio = models.CharField(max_length=255)
    email_address = models.EmailField()


class CooperativeQuestion(models.Model):
    question = models.CharField(max_length=255)
    is_report_approval = models.BooleanField()
    is_available = models.BooleanField(default=False)
    meeting_type = models.CharField(max_length=9, choices=MEETING_TYPES)
    meeting_format = models.CharField(max_length=10, choices=MEETING_FORMATS)


class CooperativeMeeting(models.Model):
    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE)
    meeting_type = models.CharField(max_length=9, choices=MEETING_TYPES)
    meeting_format = models.CharField(max_length=10, choices=MEETING_FORMATS)
    questions = models.ManyToManyField(CooperativeQuestion)
    meeting_stage = models.CharField(max_length=15, choices=MEETING_STAGES)
    last = models.BooleanField()
