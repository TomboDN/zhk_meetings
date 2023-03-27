from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField
from .models import Cooperative


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
    ZHK_CHOICES = [
        ('zhk', 'ЖК'),
        ('zhsk', 'ЖСК')
    ]
    cooperative_type = forms.CharField(label='Выберите тип объединения', widget=forms.RadioSelect(choices=ZHK_CHOICES))
    cooperative_name = forms.CharField(label='Наименование ЖК/ЖСК', help_text='Сведения содержатся в Уставе ЖК/ЖСК')
    cooperative_itn = forms.CharField(label='ИНН', help_text='Можно узнать на сайте ФНС (www.nalog.gov.ru)')
    cooperative_address = forms.CharField(label='Адрес ЖК/ЖСК', help_text='Сведения содержатся в Уставе ЖК/ЖСК')
    cooperative_email_address = forms.EmailField(label='Эл.почта ЖК/ЖСК', widget=forms.EmailInput)
    cooperative_telephone_number = PhoneNumberField(label='Номер телефона')

    class Meta:
        model = Cooperative
        fields = ['cooperative_type', 'cooperative_name', 'cooperative_itn', 'cooperative_address',
                  'cooperative_email_address', 'cooperative_telephone_number']
