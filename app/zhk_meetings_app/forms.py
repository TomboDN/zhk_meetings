from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField
from django.forms.formsets import BaseFormSet
from phonenumber_field.widgets import RegionalPhoneNumberWidget

from .models import Cooperative, CooperativeMember, CooperativeMeeting, CooperativeQuestion, REGULAR_QUESTIONS, \
    IRREGULAR_INTRAMURAL_QUESTIONS, IRREGULAR_EXTRAMURAL_QUESTIONS


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
    cooperative_name = forms.CharField(label='Наименование ЖК/ЖСК', help_text='Сведения содержатся в Уставе ЖК/ЖСК')
    cooperative_itn = forms.CharField(label='ИНН', help_text='Можно узнать на сайте ФНС (www.nalog.gov.ru)')
    cooperative_address = forms.CharField(label='Адрес ЖК/ЖСК', help_text='Сведения содержатся в Уставе ЖК/ЖСК')
    cooperative_email_address = forms.EmailField(label='Эл.почта ЖК/ЖСК', widget=forms.EmailInput)
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

    chairman_name = forms.CharField(label='ФИО Председателя правления ЖК/ЖСК')
    auditor_name = forms.CharField(label='ФИО ревизора / председателя ревизионной комиссии ЖК/ЖСК')
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


class RegularQuestionsForm(forms.ModelForm):
    questions = forms.CharField(label='Вопросы, которые можно рассматривать на очередном собрании:',
                                widget=forms.CheckboxSelectMultiple(choices=REGULAR_QUESTIONS))
    additional_question = forms.CharField(label='Другой вопрос', help_text='Ввести вручную', required=False)
    additional_question.disabled = True

    class Meta:
        model = CooperativeMeeting
        fields = ['questions']


class IntramuralQuestionsForm(forms.ModelForm):
    questions = forms.CharField(label='Вопросы, которые можно рассматривать на внеочередном очном собрании:',
                                widget=forms.CheckboxSelectMultiple(choices=IRREGULAR_INTRAMURAL_QUESTIONS))
    additional_question = forms.CharField(label='Другой вопрос', help_text='Ввести вручную', required=False)
    additional_question.disabled = True

    class Meta:
        model = CooperativeMeeting
        fields = ['questions']


class ExtramuralQuestionsForm(forms.ModelForm):
    questions = forms.CharField(label='Вопросы, которые можно рассматривать на внеочередном заочном собрании:',
                                widget=forms.CheckboxSelectMultiple(choices=IRREGULAR_EXTRAMURAL_QUESTIONS))
    additional_question = forms.CharField(label='Другой вопрос', help_text='Ввести вручную', required=False)
    additional_question.disabled = True

    class Meta:
        model = CooperativeMeeting
        fields = ['questions']


class IntramuralPreparationForm(forms.ModelForm):
    date = forms.DateField(label='Дата', widget=forms.NumberInput(attrs={'type': 'date'}))
    time = forms.TimeField(label='Время', widget=forms.TimeInput(attrs={'type': 'time'}))
    place = forms.CharField(label='Место')
    appendix = forms.FileField(label='Приложения', widget=forms.ClearableFileInput(attrs={'multiple': True}),
                               help_text='Загрузите в поле необходимые приложения к Уведомлению в формате (?). '
                                         'Название файла должно соответствовать содержанию документа. Приложения '
                                         'будут направлены членам кооператива вместе с Уведомлением.')

    class Meta:
        model = CooperativeMeeting
        fields = ['date', 'time', 'place']


class ExtramuralPreparationForm(forms.ModelForm):
    date = forms.DateField(label='Дата окончания приема бюллетеней', widget=forms.NumberInput(attrs={'type': 'date'}))
    time = forms.TimeField(label='Время окончания приема бюллетеней', widget=forms.TimeInput(attrs={'type': 'time'}))
    appendix = forms.FileField(label='Приложения', widget=forms.ClearableFileInput(attrs={'multiple': True}),
                               help_text='Загрузите в поле необходимые приложения к Уведомлению в формате (?). '
                                         'Название файла должно соответствовать содержанию документа. Приложения '
                                         'будут направлены членам кооператива вместе с Уведомлением.')

    class Meta:
        model = CooperativeMeeting
        fields = ['date', 'time']
