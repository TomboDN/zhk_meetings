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
    ('type', 'Выбор типа'),
    ('format', 'Выбор формата'),
    ('questions', 'Выбор вопросов'),
    ('question-reorganization', 'Реорганизация кооператива'),
    ('question-termination', 'Прекращение полномочий'),
    ('question-reception', 'Прием граждан'),
    ('requirement-initiator', 'Требование о проведении собрания'),
    ('requirement-creation', 'Создание требования'),
    ('requirement-approval', 'Принятие решения о проведении собрания'),
    ('preparation', 'Стадия подготовки'),
    ('conducting', 'Стадия проведения'),
    ('decision-making', 'Стадия принятия решения'),
]

INITIATORS = [
        ('chairman', 'Правление кооператива'),
        ('auditor', 'Ревизионная комиссия / ревизор'),
        ('members', 'Члены кооператива')
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

    def __str__(self):
        return self.fio


class CooperativeQuestion(models.Model):
    question = models.CharField(max_length=255)
    is_report_approval = models.BooleanField(default=False)
    is_clickable = models.BooleanField(default=False)
    is_available_for_regular_meeting = models.BooleanField()
    is_available_for_intramural_meeting = models.BooleanField()
    is_available_for_extramural_meeting = models.BooleanField()

    def __str__(self):
        return self.question


class CooperativeMeeting(models.Model):
    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE)
    meeting_type = models.CharField(max_length=9, choices=MEETING_TYPES)
    meeting_format = models.CharField(max_length=10, choices=MEETING_FORMATS)
    questions = models.ManyToManyField(CooperativeQuestion)
    meeting_stage = models.CharField(max_length=50, choices=MEETING_STAGES, default='type')
    initiator = models.CharField(max_length=30, choices=INITIATORS)
    reason = models.TextField()
    conduct_decision = models.BooleanField(null=True)
    conduct_reason = models.IntegerField(null=True)
    date = models.DateField(null=True)
    time = models.TimeField(null=True)
    place = models.CharField(max_length=255)


class CooperativeMemberInitiator(models.Model):
    cooperative_meeting = models.ForeignKey(CooperativeMeeting, on_delete=models.CASCADE)
    cooperative_member = models.ForeignKey(CooperativeMember, on_delete=models.CASCADE)
    representative = models.CharField(max_length=255)


class CooperativeReorganizationAcceptedMember(models.Model):
    cooperative_meeting = models.ForeignKey(CooperativeMeeting, on_delete=models.CASCADE)
    fio = models.CharField(max_length=255)


class CooperativeMeetingReorganization(models.Model):
    cooperative_meeting = models.ForeignKey(CooperativeMeeting, on_delete=models.CASCADE)
    convert_name = models.CharField(max_length=255)
    responsible_name = models.CharField(max_length=255)


class CooperativeTerminatedMember(models.Model):
    cooperative_meeting = models.ForeignKey(CooperativeMeeting, on_delete=models.CASCADE)
    fio = models.CharField(max_length=255)


class CooperativeAcceptedMember(models.Model):
    cooperative_meeting = models.ForeignKey(CooperativeMeeting, on_delete=models.CASCADE)
    fio = models.CharField(max_length=255)
