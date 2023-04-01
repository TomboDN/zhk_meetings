from django.db import transaction, IntegrityError
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse
from .forms import UserRegisterForm, UserLoginForm, CooperativeDataForm, CooperativeMembersForm, MemberForm, \
    BaseMemberFormSet, RegularQuestionsForm, IrregularExtramuralQuestionsForm, \
    IrregularIntramuralQuestionsForm, IntramuralPreparationForm, CooperativeMeetingTypeForm, \
    CooperativeMeetingFormatForm, ExtramuralPreparationForm
from .models import Cooperative, CooperativeMember, CooperativeMeeting


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
    cooperative = Cooperative.objects.filter(cooperative_user=request.user).first()
    if request.method == "POST":
        form = CooperativeDataForm(request.POST)
        if form.is_valid():
            obj, created = Cooperative.objects.update_or_create(cooperative_user=request.user, defaults=dict(
                cooperative_name=form.cleaned_data.get('cooperative_name'),
                cooperative_itn=form.cleaned_data.get('cooperative_itn'),
                cooperative_address=form.cleaned_data.get('cooperative_address'),
                cooperative_email_address=form.cleaned_data.get('cooperative_email_address'),
                cooperative_telephone_number=form.cleaned_data.get('cooperative_telephone_number')))
            messages.info(request, f"Обновление {created}")
            return redirect('/')
        else:
            messages.error(request, "Ошибки в полях.")

    if cooperative:
        form = CooperativeDataForm(
            initial={
                'cooperative_name': cooperative.cooperative_name,
                'cooperative_itn': cooperative.cooperative_itn,
                'cooperative_address': cooperative.cooperative_address,
                'cooperative_email_address': cooperative.cooperative_email_address,
                'cooperative_telephone_number': cooperative.cooperative_telephone_number
            })
    else:
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
            cooperative, created = Cooperative.objects.update_or_create(cooperative_user=request.user, defaults=dict(
                chairman_name=cooperative_members_form.cleaned_data.get('chairman_name'),
                auditor_name=cooperative_members_form.cleaned_data.get('auditor_name'),
                auditor_email_address=cooperative_members_form.cleaned_data.get('auditor_email_address'),
            ))

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
                    return redirect('/dashboard')

            except IntegrityError:
                messages.error(request, 'Ошибка сохранения данных о членах кооператива.')
                return redirect(reverse('members_data'))

    else:
        if cooperative:
            cooperative_members_form = CooperativeMembersForm(initial={
                'chairman_name': cooperative.chairman_name,
                'auditor_name': cooperative.auditor_name,
                'auditor_email_address': cooperative.auditor_email_address
            })
        else:
            cooperative_members_form = CooperativeMembersForm()
        member_formset = members_form_set(initial=member_data)

    context = {
        'cooperative_members_form': cooperative_members_form,
        'member_formset': member_formset,
    }

    return render(request, 'cooperative_data/members_data.html', context)


def cooperative_meeting_new(request):
    if request.method == "POST":
        form = CooperativeMeetingTypeForm(request.POST)
        if form.is_valid():
            meeting_type = form.cleaned_data.get('meeting_type')
            cooperative = Cooperative.objects.get(cooperative_user=request.user)
            if meeting_type == 'regular':
                obj = CooperativeMeeting.objects.create(cooperative=cooperative,
                                                        meeting_type=meeting_type,
                                                        meeting_stage='questions',
                                                        last=True
                                                        )
                return redirect('/meeting_questions/' + str(obj.id))
            elif meeting_type == 'irregular':
                obj = CooperativeMeeting.objects.create(cooperative=cooperative,
                                                        meeting_type=meeting_type,
                                                        meeting_stage='format',
                                                        last=True
                                                        )
                return redirect('/meeting_format/' + str(obj.id))
        else:
            return redirect('/meeting_new')
    form = CooperativeMeetingTypeForm()
    return render(request=request, template_name="meeting_data/meeting_type.html", context={"form": form})


def meeting_format_request(request, meeting_id):
    if request.method == "POST":
        form = CooperativeMeetingFormatForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    meeting = CooperativeMeeting.objects.get(id=meeting_id)
                    meeting.meeting_format = form.cleaned_data.get('meeting_format')
                    meeting.meeting_stage = 'questions'
                    meeting.save()
                    return redirect('/dashboard')

            except IntegrityError:
                return redirect('/meeting_format/' + str(meeting_id))
        else:
            return redirect('/meeting_format/' + str(meeting_id))
    form = CooperativeMeetingFormatForm()
    return render(request=request, template_name="meeting_data/meeting_format.html", context={"form": form})


def regular_questions(request):
    if request.method == "POST":
        form = RegularQuestionsForm(request.POST)
        if form.is_valid():
            cooperative = Cooperative.objects.filter(cooperative_user=request.user).first()
            obj, created = CooperativeMeeting.objects.update_or_create(cooperative=cooperative, defaults=dict(
                meeting_type='meeting_type',
                meeting_format='meeting_format',
                questions=form.cleaned_data.get('questions'),
                last=True
            ))
            messages.info(request, f"Обновление {created}")
            return redirect('/dashboard')
        else:
            messages.error(request, "Ошибки в полях.")
            return redirect('/regular_questions')
    form = RegularQuestionsForm()
    return render(request=request, template_name="meeting_data/questions.html", context={"form": form})


def irregular_intramural_questions(request):
    if request.method == "POST":
        form = IrregularIntramuralQuestionsForm(request.POST)
        if form.is_valid():
            cooperative = Cooperative.objects.filter(cooperative_user=request.user).first()
            obj, created = CooperativeMeeting.objects.update_or_create(cooperative=cooperative, defaults=dict(
                meeting_type='meeting_type',
                meeting_format='meeting_format',
                questions=form.cleaned_data.get('questions'),
                last=True
            ))
            messages.info(request, f"Обновление {created}")
            return redirect('/dashboard')
        else:
            messages.error(request, "Ошибки в полях.")
            return redirect('/irregular_intramural_questions')
    form = IrregularIntramuralQuestionsForm()
    return render(request=request, template_name="meeting_data/questions.html", context={"form": form})


def irregular_extramural_questions(request):
    if request.method == "POST":
        form = IrregularExtramuralQuestionsForm(request.POST)
        if form.is_valid():
            cooperative = Cooperative.objects.filter(cooperative_user=request.user).first()
            obj, created = CooperativeMeeting.objects.update_or_create(cooperative=cooperative, defaults=dict(
                meeting_type='meeting_type',
                meeting_format='meeting_format',
                questions=form.cleaned_data.get('questions'),
                last=True
            ))
            messages.info(request, f"Обновление {created}")
            return redirect('/dashboard')
        else:
            messages.error(request, "Ошибки в полях.")
            return redirect('/irregular_extramural_questions')
    form = IrregularExtramuralQuestionsForm()
    return render(request=request, template_name="meeting_data/questions.html", context={"form": form})


def meeting_preparation(request, meeting_id):
    meeting = CooperativeMeeting.objects.get(id=meeting_id)
    if meeting.meeting_type == "regular":
        title = "Стадия подготовки очередного собрания"
        form = IntramuralPreparationForm()
    elif meeting.meeting_type == "irregular" and meeting.meeting_format == "intramural":
        title = "Стадия подготовки внеочередного очного собрания"
        form = IntramuralPreparationForm()
    else:
        title = "Стадия подготовки внеочередного заочного собрания"
        form = ExtramuralPreparationForm()

    if request.method == "POST":
        if meeting.meeting_type == "regular":
            form = IntramuralPreparationForm(request.POST)
        elif meeting.meeting_type == "irregular" and meeting.meeting_format == "intramural":
            form = IntramuralPreparationForm(request.POST)
        else:
            form = ExtramuralPreparationForm(request.POST)
        if form.is_valid():
            meeting = CooperativeMeeting.objects.get(id=meeting_id)
            if meeting.meeting_type == "regular":
                try:
                    with transaction.atomic():
                        meeting = CooperativeMeeting.objects.get(id=meeting_id)
                        meeting.date = form.cleaned_data.get('date')
                        meeting.time = form.cleaned_data.get('time')
                        meeting.place = form.cleaned_data.get('place')
                        meeting.save()

                except IntegrityError:
                    return redirect('/meeting_preparation/' + str(meeting_id))

            elif meeting.meeting_type == "irregular" and meeting.meeting_format == "intramural":
                try:
                    with transaction.atomic():
                        meeting = CooperativeMeeting.objects.get(id=meeting_id)
                        meeting.date = form.cleaned_data.get('date')
                        meeting.time = form.cleaned_data.get('time')
                        meeting.place = form.cleaned_data.get('place')
                        meeting.save()

                except IntegrityError:
                    return redirect('/meeting_preparation/' + str(meeting_id))
            else:
                try:
                    with transaction.atomic():
                        meeting = CooperativeMeeting.objects.get(id=meeting_id)
                        meeting.date = form.cleaned_data.get('date')
                        meeting.time = form.cleaned_data.get('time')
                        meeting.save()

                except IntegrityError:
                    return redirect('/meeting_preparation/' + str(meeting_id))

            if 'create_notification' in request.POST:
                ...  # TODO create_notification(meeting)

            elif 'save_and_continue' in request.POST:
                files = request.FILES.getlist('appendix')
                for f in files:
                    ...  # TODO

                return redirect('/dashboard')

        else:
            messages.error(request, "Ошибки в полях.")
            return redirect('/intramural_preparation')

    return render(request=request, template_name="meeting_data/meeting_preparation.html",
                  context={"form": form, "title": title})
