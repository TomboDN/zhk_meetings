from django.db import transaction, IntegrityError
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse
from .forms import UserRegisterForm, UserLoginForm, CooperativeDataForm, CooperativeMembersForm, MemberForm, \
    BaseMemberFormSet
from .models import Cooperative, CooperativeMember


def register_request(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Создан аккаунт {username}!')
            return redirect('/login')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def login_request(request):
    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Вы зашли как {username}.")
                return redirect('/')
            else:
                messages.error(request, "Неправильная почта или пароль.")
        else:
            messages.error(request, "Неправильная почта или пароль.")
    form = UserLoginForm()
    return render(request=request, template_name="registration/login.html", context={"form": form})


def logout_request(request):
    logout(request)
    messages.info(request, "Вы успешно вышли из аккаунта.")
    return redirect('/')


def home(request):
    return render(request=request, template_name="home.html")


def dashboard(request):
    return render(request=request, template_name="dashboard.html")


def cooperative_main_data(request):
    if request.method == "POST":
        form = CooperativeDataForm(request.POST)
        if form.is_valid():
            obj, created = Cooperative.objects.update_or_create(cooperative_user=request.user, defaults=dict(
                cooperative_type=form.cleaned_data.get('cooperative_type'),
                cooperative_name=form.cleaned_data.get('cooperative_name'),
                cooperative_itn=form.cleaned_data.get('cooperative_itn'),
                cooperative_address=form.cleaned_data.get('cooperative_address'),
                cooperative_email_address=form.cleaned_data.get('cooperative_email_address'),
                cooperative_telephone_number=form.cleaned_data.get('cooperative_telephone_number')))
            messages.info(request, f"Обновление {created}")
            return redirect('/')
        else:
            messages.error(request, "Ошибки в полях.")
    form = CooperativeDataForm()
    return render(request=request, template_name="cooperative_data/main_data.html", context={"form": form})


def cooperative_members_data(request):
    user = request.user
    cooperative = Cooperative.objects.filter(cooperative_user=user).first()

    members_form_set = formset_factory(MemberForm, formset=BaseMemberFormSet)

    cooperative_members = CooperativeMember.objects.filter(cooperative=cooperative).order_by('email_address')
    member_data = [{'fio': x.fio, 'email_address': x.email_address}
                   for x in cooperative_members]

    if request.method == 'POST':
        cooperative_members_form = CooperativeMembersForm(request.POST)
        member_formset = members_form_set(request.POST)

        if cooperative_members_form.is_valid() and member_formset.is_valid():
            cooperative.chairman_name = cooperative_members_form.cleaned_data.get('chairman_name')
            cooperative.auditor_name = cooperative_members_form.cleaned_data.get('auditor_name')
            cooperative.auditor_email_address = cooperative_members_form.cleaned_data.get('auditor_email_address')
            cooperative.save()

            new_members = []

            for member_form in member_formset:
                fio = member_form.cleaned_data.get('fio')
                email_address = member_form.cleaned_data.get('email_address')

                if fio and email_address:
                    new_members.append(CooperativeMember(cooperative=cooperative, fio=fio, email_address=email_address))

            # TODO Add request.FILES check
                # TODO File parser

            try:
                with transaction.atomic():
                    CooperativeMember.objects.filter(cooperative=cooperative).delete()
                    CooperativeMember.objects.bulk_create(new_members)

                    messages.success(request, 'Вы обновили данные о членах кооператива.')

            except IntegrityError:
                messages.error(request, 'Ошибка сохранения данных о членах кооператива.')
                return redirect(reverse('members_data'))

    else:
        cooperative_members_form = CooperativeMembersForm()
        member_formset = members_form_set(initial=member_data)

    context = {
        'cooperative_members_form': cooperative_members_form,
        'member_formset': member_formset,
    }

    return render(request, 'cooperative_data/members_data.html', context)
