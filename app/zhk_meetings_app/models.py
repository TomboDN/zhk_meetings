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
    ('preparation', 'Стадия подготовки'),
    ('conducting', 'Стадия проведения'),
    ('decision-making', 'Стадия принятия решения'),
]

INITIATORS = [
        ('chairman', 'Правление кооператива'),
        ('auditor', 'Ревизионная комиссия / ревизор'),
        ('members', 'Члены кооператива')
    ]

REGULAR_QUESTIONS = [
        ('statute-approval', 'Утверждение устава кооператива'),
        ('statute-changes', 'Внесение изменений в устав кооператива'),
        ('statute-changes-approval', 'Утверждение устава кооператива в новой редакции'),
        ('internal-docs', 'Утверждение внутренних документов кооператива, регулирующих деятельность органов управления '
                                    'кооператива и иных органов кооператива, предусмотренных настоящим уставом'),
        ('mutual-fund', 'Утверждение размера паевого фонда Кооператива и порядка его использования Кооперативом'),
        ('reorganization', 'Принятие решения о реорганизации кооператива'),
        ('liquidation', 'Принятие решения о ликвидации кооператива, а также назначение ликвидационной комиссии и '
                                    'утверждение промежуточного и окончательного ликвидационных балансов'),
        ('mandatory-contributions', 'Установление размера обязательных взносов членов кооператива, за исключением размера '
                                    'вступительных и паевых взносов, определяемых настоящим уставом'),
        ('governance', 'Избрание правления кооператива'),
        ('governance-termination', 'Прекращение полномочий правления кооператива'),
        ('governers-termination', 'Прекращение полномочий отдельных членов правления'),
        ('auditor', 'Избрание ревизионной комиссии (ревизора)'),
        ('auditor-termination', 'Прекращение, в том числе досрочное, полномочий ревизионной комиссии (ревизора) кооператива или ее отдельных членов'),
        ('governance-report', 'Утверждение отчетов о деятельности правления кооператива'),
        ('auditor-report', 'Утверждение отчета о деятельности ревизионной комиссии (ревизора) кооператива'),
        ('annual-report', 'Утверждение годового отчета кооператива и годовой бухгалтерской (финансовой) отчетности кооператива'),
        ('financial-approval', 'Утверждение аудиторского заключения о достоверности бухгалтерской (финансовой) отчетности '
                                    'кооператива по итогам финансового года'),
        ('financial-economic-approval', 'Утверждение заключений ревизионной комиссии (ревизора) кооператива по результатам проверки '
                                    'финансово-хозяйственной деятельности кооператива'),
        ('fund-report', 'Утверждение отчетов об использовании фондов кооператива'),
        ('member-inclusion', 'Принятие решения о приеме граждан в члены кооператива'),
        ('member-exclusion', 'Принятие решения об исключении граждан из кооператива'),
        ('fund-planning', 'Определение порядка формирования фондов кооператива, за исключением паевого фонда кооператива, и их использования'),
    ]

IRREGULAR_INTRAMURAL_QUESTIONS = [
        ('statute-approval', 'Утверждение устава кооператива'),
        ('statute-changes', 'Внесение изменений в устав кооператива'),
        ('statute-changes-approval', 'Утверждение устава кооператива в новой редакции'),
        ('internal-docs', 'Утверждение внутренних документов кооператива, регулирующих деятельность органов управления '
                                    'кооператива и иных органов кооператива, предусмотренных настоящим уставом'),
        ('mutual-fund', 'Утверждение размера паевого фонда Кооператива и порядка его использования Кооперативом'),
        ('reorganization', 'Принятие решения о реорганизации кооператива'),
        ('liquidation', 'Принятие решения о ликвидации кооператива, а также назначение ликвидационной комиссии и '
                                    'утверждение промежуточного и окончательного ликвидационных балансов'),
        ('mandatory-contributions', 'Установление размера обязательных взносов членов кооператива, за исключением размера '
                                    'вступительных и паевых взносов, определяемых настоящим уставом'),
        ('governance-termination', 'Прекращение полномочий правления кооператива'),
        ('governers-termination', 'Прекращение полномочий отдельных членов правления'),
        ('auditor', 'Избрание ревизионной комиссии (ревизора)'),
        ('auditor-termination', 'Прекращение, в том числе досрочное, полномочий ревизионной комиссии (ревизора) кооператива или ее отдельных членов'),
        ('financial-approval', 'Утверждение аудиторского заключения о достоверности бухгалтерской (финансовой) отчетности '
                                    'кооператива по итогам финансового года'),
        ('financial-economic-approval', 'Утверждение заключений ревизионной комиссии (ревизора) кооператива по результатам проверки '
                                    'финансово-хозяйственной деятельности кооператива'),
        ('fund-report', 'Утверждение отчетов об использовании фондов кооператива'),
        ('member-inclusion', 'Принятие решения о приеме граждан в члены кооператива'),
        ('member-exclusion', 'Принятие решения об исключении граждан из кооператива'),
        ('fund-planning', 'Определение порядка формирования фондов кооператива, за исключением паевого фонда кооператива, и их использования'),
]

IRREGULAR_EXTRAMURAL_QUESTIONS = [
        ('internal-docs', 'Утверждение внутренних документов кооператива, регулирующих деятельность органов управления '
                                    'кооператива и иных органов кооператива, предусмотренных настоящим уставом'),
        ('mutual-fund', 'Утверждение размера паевого фонда Кооператива и порядка его использования Кооперативом'),
        ('mandatory-contributions', 'Установление размера обязательных взносов членов кооператива, за исключением размера '
                                    'вступительных и паевых взносов, определяемых настоящим уставом'),
        ('governance-termination', 'Прекращение полномочий правления кооператива'),
        ('governers-termination', 'Прекращение полномочий отдельных членов правления'),
        ('auditor-termination', 'Прекращение, в том числе досрочное, полномочий ревизионной комиссии (ревизора) кооператива или ее отдельных членов'),
        ('financial-approval', 'Утверждение аудиторского заключения о достоверности бухгалтерской (финансовой) отчетности '
                                    'кооператива по итогам финансового года'),
        ('financial-economic-approval', 'Утверждение заключений ревизионной комиссии (ревизора) кооператива по результатам проверки '
                                    'финансово-хозяйственной деятельности кооператива'),
        ('fund-report', 'Утверждение отчетов об использовании фондов кооператива'),
        ('fund-planning', 'Определение порядка формирования фондов кооператива, за исключением паевого фонда кооператива, и их использования'),
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
    is_report_approval = models.BooleanField()
    is_available = models.BooleanField(default=False)
    meeting_type = models.CharField(max_length=9, choices=MEETING_TYPES)
    meeting_format = models.CharField(max_length=10, choices=MEETING_FORMATS)


class CooperativeMeeting(models.Model):
    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE)
    meeting_type = models.CharField(max_length=9, choices=MEETING_TYPES)
    meeting_format = models.CharField(max_length=10, choices=MEETING_FORMATS)
    questions = models.ManyToManyField(CooperativeQuestion)
    meeting_stage = models.CharField(max_length=15, choices=MEETING_STAGES, default='type')
    initiator = models.CharField(max_length=30, choices=INITIATORS)
    reason = models.TextField()
    conduct_decision = models.BooleanField(null=True)
    conduct_reason = models.CharField(max_length=255)
    date = models.DateField(null=True)
    time = models.TimeField(null=True)
    place = models.CharField(max_length=255)


class CooperativeMemberRepresentative(models.Model):
    cooperative_meeting = models.ForeignKey(CooperativeMeeting, on_delete=models.CASCADE)
    cooperative_member = models.ForeignKey(CooperativeMember, on_delete=models.CASCADE)
    representative = models.CharField(max_length=255)

