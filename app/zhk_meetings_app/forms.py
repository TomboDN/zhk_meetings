from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField
from django.forms.formsets import BaseFormSet
from phonenumber_field.widgets import RegionalPhoneNumberWidget
import datetime

from .models import Cooperative, CooperativeMember, CooperativeMeeting, CooperativeQuestion

DECISION_CHOICE = [
    ('True', 'Решение принято'),
    ('False', 'Решение не принято'),
]


def next_year(dt):
    try:
        return dt.replace(year=dt.year + 1)
    except ValueError:
        return dt + datetime.timedelta(days=365)


class UserRegisterForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Повторите пароль'
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
        labels = {
            'username': _('Электронная почта'),
        }
        help_texts = {
            'username': _(''),
        }


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин')
    password = forms.CharField(label='Пароль')


class CooperativeDataForm(forms.Form):
    cooperative_name = forms.CharField(label='Наименование ЖК', help_text='Сведения содержатся в Уставе ЖК')
    cooperative_itn = forms.RegexField(label='ИНН', regex=r'\d{10}|\d{12}',
                                       help_text='Можно узнать на сайте ФНС (www.nalog.gov.ru)')
    cooperative_address = forms.CharField(label='Адрес ЖК', help_text='Сведения содержатся в Уставе ЖК')
    cooperative_email_address = forms.EmailField(label='Эл.почта ЖК', widget=forms.EmailInput)
    cooperative_telephone_number = PhoneNumberField(label='Номер телефона', region="RU",
                                                    widget=RegionalPhoneNumberWidget(region="RU"),
                                                    help_text='В формате +7ХХХХХХХХХХ или 8 (ХХХ) ХХХ-ХХ-ХХ')

    class Meta:
        model = Cooperative
        fields = ['cooperative_name', 'cooperative_itn', 'cooperative_address',
                  'cooperative_email_address', 'cooperative_telephone_number']


class CooperativeMembersForm(forms.Form):
    members_file = forms.FileField(label='Загрузите файл со сведениями о членах кооператива',
                                   widget=forms.FileInput,
                                   help_text='Прикрепите файл .txt с данными в формате "ФИО:email;"',
                                   required=False)

    chairman_name = forms.CharField(label='ФИО Председателя правления ЖК')
    auditor_name = forms.CharField(label='ФИО ревизора / председателя ревизионной комиссии ЖК')
    auditor_email_address = forms.EmailField(label='Почта ревизионной комиссии / ревизора', widget=forms.EmailInput)


class MemberForm(forms.ModelForm):
    class Meta:
        model = CooperativeMember
        exclude = ('cooperative',)
        labels = {
            'fio': _('ФИО'),
            'email_address': _('Почта'),
        }


class BaseMemberFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return

        email_address_list = []
        duplicates = False

        for form in self.forms:
            if form.cleaned_data:
                fio = form.cleaned_data['fio']
                email_address = form.cleaned_data['email_address']

                if fio and email_address:
                    if email_address in email_address_list:
                        duplicates = True
                    email_address_list.append(email_address)

                if duplicates:
                    raise forms.ValidationError(
                        'Адреса электронной почты должны быть уникальными.',
                        code='duplicate_emails'
                    )

                if email_address and not fio:
                    raise forms.ValidationError(
                        'У всех членов кооператива должно быть ФИО.',
                        code='missing_fio'
                    )
                elif fio and not email_address:
                    raise forms.ValidationError(
                        'У всех членов кооператива должен быть адрес электронной почты.',
                        code='missing_email'
                    )


class CooperativeMeetingTypeForm(forms.ModelForm):
    MEETING_TYPES = [
        ('regular', 'Очередное'),
        ('irregular', 'Внеочередное')
    ]

    meeting_type = forms.CharField(label='Вид собрания', widget=forms.RadioSelect(choices=MEETING_TYPES))

    class Meta:
        model = CooperativeMeeting
        fields = ['meeting_type']


class CooperativeMeetingFormatForm(forms.ModelForm):
    MEETING_FORMATS = [
        ('intramural', 'Очное'),
        ('extramural', 'Заочное')
    ]

    meeting_format = forms.CharField(label='Формат собрания', widget=forms.RadioSelect(choices=MEETING_FORMATS))

    class Meta:
        model = CooperativeMeeting
        fields = ['meeting_format']


class SelectWithDisabledOptions(forms.CheckboxSelectMultiple):

    def __init__(self, disabled_choices, *args, **kwargs):
        self.disabled_choices = disabled_choices
        super(SelectWithDisabledOptions, self).__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option_dict = super(SelectWithDisabledOptions, self).create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if value in self.disabled_choices:
            option_dict['attrs']['disabled'] = 'disabled'
        return option_dict


class RegularQuestionsForm(forms.ModelForm):
    questions = forms.ModelMultipleChoiceField(label='Вопросы, которые можно рассматривать на очередном собрании',
                                               widget=SelectWithDisabledOptions(disabled_choices=None),
                                               queryset=CooperativeQuestion.objects.filter(
                                                   is_available_for_regular_meeting=True), required=False)
    additional_question = forms.CharField(label='Другой вопрос', help_text='Ввести вручную', required=False)
    additional_question.disabled = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        disabled_choices = list()
        for question in CooperativeQuestion.objects.all():
            if not question.is_clickable:
                disabled_choices.append(question.id)
        self.fields['questions'].widget.disabled_choices = disabled_choices

    class Meta:
        model = CooperativeMeeting
        fields = ['questions']


class IntramuralQuestionsForm(forms.ModelForm):
    questions = forms.ModelMultipleChoiceField(
        label='Вопросы, которые можно рассматривать на очном внеочередном собрании',
        widget=SelectWithDisabledOptions(disabled_choices=None),
        queryset=CooperativeQuestion.objects.filter(is_available_for_intramural_meeting=True))
    additional_question = forms.CharField(label='Другой вопрос', help_text='Ввести вручную', required=False)
    additional_question.disabled = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        disabled_choices = list()
        for question in CooperativeQuestion.objects.all():
            if not question.is_clickable:
                disabled_choices.append(question.id)
        self.fields['questions'].widget.disabled_choices = disabled_choices

    class Meta:
        model = CooperativeMeeting
        fields = ['questions']


class ExtramuralQuestionsForm(forms.ModelForm):
    questions = forms.ModelMultipleChoiceField(
        label='Вопросы, которые можно рассматривать на заочном внеочередном собрании',
        widget=SelectWithDisabledOptions(disabled_choices=None),
        queryset=CooperativeQuestion.objects.filter(is_available_for_extramural_meeting=True))
    additional_question = forms.CharField(label='Другой вопрос', help_text='Ввести вручную', required=False)
    additional_question.disabled = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        disabled_choices = list()
        for question in CooperativeQuestion.objects.all():
            if not question.is_clickable:
                disabled_choices.append(question.id)
        self.fields['questions'].widget.disabled_choices = disabled_choices

    class Meta:
        model = CooperativeMeeting
        fields = ['questions']


class MeetingRequirementInitiatorReasonFrom(forms.ModelForm):
    INITIATORS = [
        ('chairman', 'Правление кооператива'),
        ('auditor', 'Ревизионная комиссия / ревизор'),
        ('members', 'Члены кооператива')
    ]
    initiator = forms.ChoiceField(label='Выберите инициатора', choices=INITIATORS,
                                  widget=forms.Select(attrs={'onchange': 'check()'}))
    reason = forms.CharField(label='Общее собрание созывается в связи с:', widget=forms.Textarea,
                             help_text='Рекомендуется вводить сведения в творительном падеже')

    class Meta:
        model = CooperativeMeeting
        fields = ['initiator', 'reason']


class MemberRepresentativeForm(forms.Form):
    cooperative_member_id = forms.IntegerField()
    cooperative_member = forms.CharField(label='ФИО / наименование', widget=forms.TextInput(attrs={'readonly': 'True'}))

    is_initiator = forms.BooleanField(label='Член кооператива является инициатором', required=False,
                                      initial=False)


class MeetingApprovalForm(forms.Form):
    APPROVAL_CHOICE = [
        ('True', 'Принять требование'),
        ('False', 'Отклонить требование'),
    ]
    REASONS = [
        (0, 'Не соблюден предусмотренный Уставом порядок предъявления требований'),
        (1, 'Ни один вопрос не относится к компетенции общего собрания'),
        (2, 'Требование предъявлено органом, не имеющим полномочий по предъявлению требования'),
        (3, 'Требование подано меньшим количеством членов кооператива, чем предусмотрено Уставом'),
    ]

    conduct_decision = forms.CharField(label='Решение о проведении',
                                       widget=forms.RadioSelect(choices=APPROVAL_CHOICE, attrs={'onclick': 'check()'}))
    conduct_reason = forms.ChoiceField(label='Выберите основание', choices=REASONS)


class MeetingCooperativeReorganizationForm(forms.Form):
    convert_name = forms.CharField(label='Наименование ТСЖ, в который преобразуется Кооператив')
    responsible_name = forms.CharField(
        label='ФИО ответственного за подачу документов о реорганизации в регистрирующий орган')


class MemberTransferFioForm(forms.Form):
    fio = forms.CharField(label='ФИО граждан, принимаемых в создаваемое ТСЖ')


class ChairmanMemberFioForm(forms.Form):
    fio = forms.CharField(
        label='ФИО/наименование члена Правления ЖК, чьи полномочия прекращаются (в родительном падеже)')


class MemberAcceptFioForm(forms.Form):
    fio = forms.CharField(
        label='ФИО гражданина/граждан, подавшего заявление о вступлении в члены ЖК (в родительном падеже)')


class RegularIntramuralPreparationForm(forms.ModelForm):
    date = forms.DateField(label='Дата', widget=forms.NumberInput(
        attrs={'type': 'date', 'min': (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
               'max': (next_year(datetime.date.today())).strftime(
                   '%Y-%m-%d'), 'onchange': 'check()'}))
    time = forms.TimeField(label='Время', widget=forms.TimeInput(attrs={'type': 'time'}))
    place = forms.CharField(label='Место')
    appendix = forms.FileField(label=False, widget=forms.ClearableFileInput(attrs={'multiple': True,
                                                                                          'accept': 'application/msword, application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document'}),
                               help_text='Загрузите в поле необходимые приложения к Уведомлению в формате .doc, .docx, .pdf. '
                                         'Название файла должно соответствовать содержанию документа. Приложения '
                                         'будут направлены членам кооператива вместе с Уведомлением.', required=False)

    class Meta:
        model = CooperativeMeeting
        fields = ['date', 'time', 'place']


class IrregularIntramuralPreparationForm(forms.ModelForm):
    date = forms.DateField(label='Дата', widget=forms.NumberInput(
        attrs={'type': 'date', 'min': (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
               'max': (next_year(datetime.date.today())).strftime(
                   '%Y-%m-%d'), 'onchange': 'check()'}))
    time = forms.TimeField(label='Время', widget=forms.TimeInput(attrs={'type': 'time'}))
    place = forms.CharField(label='Место')
    appendix = forms.FileField(label=False, widget=forms.ClearableFileInput(attrs={'multiple': True,
                                                                                          'accept': 'application/msword, application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document'}),
                               help_text='Загрузите в поле необходимые приложения к Уведомлению в формате .doc, .docx, .pdf. '
                                         'Название файла должно соответствовать содержанию документа. Приложения '
                                         'будут направлены членам кооператива вместе с Уведомлением.', required=False)

    class Meta:
        model = CooperativeMeeting
        fields = ['date', 'time', 'place']


class IrregularExtramuralPreparationForm(forms.ModelForm):
    date = forms.DateField(label='Дата окончания приема бюллетеней', widget=forms.NumberInput(
        attrs={'type': 'date', 'min': (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
               'max': (next_year(datetime.date.today())).strftime(
                   '%Y-%m-%d'), 'onchange': 'check()'}))
    time = forms.TimeField(label='Время окончания приема бюллетеней', widget=forms.TimeInput(attrs={'type': 'time'}))
    appendix = forms.FileField(label=False, widget=forms.ClearableFileInput(attrs={'multiple': True,
                                                                                          'accept': 'application/msword, application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document'}),
                               help_text='Загрузите в поле необходимые приложения к Уведомлению в формате .doc, .docx, .pdf. '
                                         'Название файла должно соответствовать содержанию документа. Приложения '
                                         'будут направлены членам кооператива вместе с Уведомлением.', required=False)

    class Meta:
        model = CooperativeMeeting
        fields = ['date', 'time']


class ExecutionForm(forms.ModelForm):
    MEETING_CHAIRMANS = [
        ('chairman', 'Председатель правления'),
        ('member', 'Другое лицо')
    ]
    meeting_chairman_type = forms.ChoiceField(label='Укажите председательствующего на собрании',
                                              choices=MEETING_CHAIRMANS,
                                              widget=forms.Select(attrs={'onchange': 'check()'}))
    another_member = forms.CharField(label='Другое лицо', help_text='Введите ФИО', required=False)
    vote_counter = forms.CharField(label='Укажите ответственного за подсчёт голосов',
                                   help_text='Введите ФИО')
    secretary = forms.CharField(label='Укажите секретаря собрания', help_text='Введите ФИО')

    class Meta:
        model = CooperativeMeeting
        fields = ['vote_counter', 'secretary']


class IntramuralExecutionAttendantForm(forms.Form):
    ATTENDANCE = [
        ('absent', 'Отсутствовал'),
        ('member', 'Присутствовал член кооператива'),
        ('representative', 'Присутствовал представитель члена кооператива')
    ]
    cooperative_member_id = forms.IntegerField()
    cooperative_member = forms.CharField(label='ФИО / наименование', widget=forms.TextInput(attrs={'readonly': 'True'}))
    meeting_attendant_type = forms.ChoiceField(label='Присутствие на собрании',
                                               choices=ATTENDANCE, widget=forms.Select(attrs={'onchange': 'check()'}))
    representative = forms.CharField(label='Представитель члена кооператива', help_text='Введите ФИО', required=False)


class ExtramuralExecutionAttendantForm(forms.Form):
    SENDING = [
        ('absent', 'Не отправил бюллетень'),
        ('member', 'Член кооператива отправил бюллетень'),
        ('representative', 'Представитель члена кооператива отправил бюллетень')
    ]
    cooperative_member_id = forms.IntegerField()
    cooperative_member = forms.CharField(label='ФИО / наименование', widget=forms.TextInput(attrs={'readonly': 'True'}))
    meeting_attendant_type = forms.ChoiceField(label='Отправка бюллетеней',
                                               choices=SENDING, widget=forms.Select(attrs={'onchange': 'check()'}))
    representative = forms.CharField(label='Представитель члена кооператива', help_text='Введите ФИО', required=False)


class MeetingChairmanAnotherMember(forms.Form):
    another_member = forms.CharField(label='Другое лицо', help_text='Введите ФИО')


class ExecutionCooperativeReorganizationForm(forms.Form):
    tszh_name = forms.CharField(label='Укажите наименование создаваемого ТСЖ', help_text='Введите название')
    tszh_place = forms.CharField(label='Укажите место нахождения создаваемого ТСЖ', help_text='Введите адрес')


class ExecutionQuestionInfoForm(forms.Form):
    speaker = forms.CharField(label='По вопросу выступил', help_text='ФИО')
    theses = forms.CharField(label='Основные тезисы выступления', help_text='Основные тезисы', widget=forms.Textarea)


class ExecutionAskedQuestion(forms.Form):
    question = forms.CharField(label='Были заданы вопросы:')


class ExecutionVoting(forms.Form):
    votes_for = forms.IntegerField(required=True, min_value=0, label=False, initial=0,
                                   widget=forms.NumberInput(attrs={'onchange': 'check()'}))
    votes_against = forms.IntegerField(required=True, min_value=0, label=False, initial=0,
                                       widget=forms.NumberInput(attrs={'onchange': 'check()'}))
    votes_abstained = forms.IntegerField(required=True, min_value=0, label=False, initial=0,
                                         widget=forms.NumberInput(attrs={'onchange': 'check()'}))
    decision = forms.ChoiceField(choices=DECISION_CHOICE, widget=forms.Select, label='Решение')


class BoardMembersCandidate(forms.Form):
    fio = forms.CharField(label='Укажите кандидатов на должности членов правления')


class BoardMembersForm(forms.Form):
    chosen_candidates_limit = forms.IntegerField(label='Укажите количество кандидатов, которые должны быть выбраны',
                                                 min_value=0, initial=0)


class ExecutionFIOVoting(forms.Form):
    votes_abstained = forms.IntegerField(required=False, min_value=0, label=False, initial=0,
                                         widget=forms.NumberInput(attrs={'onchange': 'check()'}))
    decision = forms.ChoiceField(choices=DECISION_CHOICE, widget=forms.Select, label='Решение')


class MemberVotes(forms.Form):
    fio = forms.CharField(required=True)
    votes_for = forms.IntegerField(required=True, min_value=0, label=False, initial=0,
                                   widget=forms.NumberInput(attrs={'onchange': 'check()'}))


class BaseMemberVoteFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return

        fio_list = []
        duplicates = False

        for form in self.forms:
            if form.cleaned_data:
                fio = form.cleaned_data['fio']

                if fio:
                    if fio in fio_list:
                        duplicates = True
                    fio_list.append(fio)

                if duplicates:
                    raise forms.ValidationError(
                        'Фио участников повторяются',
                        code='duplicate_fio'
                    )


class ExecutionTerminationDateForm(forms.Form):
    date = forms.DateField(label='Дата прекращения полномочий члена Правления:',
                           widget=forms.NumberInput(
                               attrs={'type': 'date',
                                      'min': (datetime.date.today() + datetime.timedelta(days=1)).strftime(
                                          '%Y-%m-%d'),
                                      'max': (next_year(datetime.date.today())).strftime(
                                          '%Y-%m-%d')}))


class MeetingFinishDateForm(forms.Form):
    date = forms.DateField(label='Дата окончания собрания:',
                           widget=forms.NumberInput(attrs={'type': 'date'}))
