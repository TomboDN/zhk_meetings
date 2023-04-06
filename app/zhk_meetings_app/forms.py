from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField
from django.forms.formsets import BaseFormSet
from phonenumber_field.widgets import RegionalPhoneNumberWidget

from .models import Cooperative, CooperativeMember, CooperativeMeeting, CooperativeQuestion, \
    CooperativeMemberInitiator


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
    cooperative_itn = forms.RegexField(label='ИНН', regex=r'\d{10}|\d{12}', help_text='Можно узнать на сайте ФНС (www.nalog.gov.ru)')
    cooperative_address = forms.CharField(label='Адрес ЖК', help_text='Сведения содержатся в Уставе ЖК')
    cooperative_email_address = forms.EmailField(label='Эл.почта ЖК', widget=forms.EmailInput)
    cooperative_telephone_number = PhoneNumberField(label='Номер телефона', region="RU",
                                                    widget=RegionalPhoneNumberWidget(region="RU"))

    class Meta:
        model = Cooperative
        fields = ['cooperative_name', 'cooperative_itn', 'cooperative_address',
                  'cooperative_email_address', 'cooperative_telephone_number']


class CooperativeMembersForm(forms.Form):
    members_file = forms.FileField(label='Поле для загрузки документа с данными членов кооператива',
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
                        'Links must have unique anchors and URLs.',
                        code='duplicate_links'
                    )

                if email_address and not fio:
                    raise forms.ValidationError(
                        'All links must have an fio.',
                        code='missing_fio'
                    )
                elif fio and not email_address:
                    raise forms.ValidationError(
                        'All links must have an email_address.',
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
                                    is_available_for_regular_meeting=True))
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
    representatives_request = forms.BooleanField(label='Требование выдвигает представитель', required=False,
                                                 initial=False)
    representative = forms.CharField(label='ФИО представителя', required=False)


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


class IntramuralPreparationForm(forms.ModelForm):
    date = forms.DateField(label='Дата', widget=forms.NumberInput(attrs={'type': 'date'}))
    time = forms.TimeField(label='Время', widget=forms.TimeInput(attrs={'type': 'time'}))
    place = forms.CharField(label='Место')
    appendix = forms.FileField(label='Приложения', widget=forms.ClearableFileInput(attrs={'multiple': True}),
                               help_text='Загрузите в поле необходимые приложения к Уведомлению в формате (?). '
                                         'Название файла должно соответствовать содержанию документа. Приложения '
                                         'будут направлены членам кооператива вместе с Уведомлением.', required=False)

    class Meta:
        model = CooperativeMeeting
        fields = ['date', 'time', 'place']


class ExtramuralPreparationForm(forms.ModelForm):
    date = forms.DateField(label='Дата окончания приема бюллетеней', widget=forms.NumberInput(attrs={'type': 'date'}))
    time = forms.TimeField(label='Время окончания приема бюллетеней', widget=forms.TimeInput(attrs={'type': 'time'}))
    appendix = forms.FileField(label='Приложения', widget=forms.ClearableFileInput(attrs={'multiple': True}),
                               help_text='Загрузите в поле необходимые приложения к Уведомлению в формате (?). '
                                         'Название файла должно соответствовать содержанию документа. Приложения '
                                         'будут направлены членам кооператива вместе с Уведомлением.', required=False)

    class Meta:
        model = CooperativeMeeting
        fields = ['date', 'time']
