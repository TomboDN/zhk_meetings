from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.forms import formset_factory, BaseFormSet
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse
from urllib.parse import quote

from doc import create_notification, create_requirement, create_decision
from emails import send_notification
from .forms import UserRegisterForm, UserLoginForm, CooperativeDataForm, CooperativeMembersForm, MemberForm, \
    BaseMemberFormSet, RegularQuestionsForm, ExtramuralQuestionsForm, \
    IntramuralQuestionsForm, IntramuralPreparationForm, CooperativeMeetingTypeForm, CooperativeMeetingFormatForm, \
    ExtramuralPreparationForm, MeetingRequirementInitiatorReasonFrom, MeetingApprovalForm, \
    MemberRepresentativeForm, MeetingCooperativeReorganizationForm, MemberTransferFioForm, ChairmanMemberFioForm, \
    MemberAcceptFioForm, ExecutionForm
from .models import Cooperative, CooperativeMember, CooperativeMeeting, CooperativeMemberInitiator, \
    CooperativeReorganizationAcceptedMember, CooperativeMeetingReorganization, CooperativeTerminatedMember, \
    CooperativeAcceptedMember, CooperativeQuestion


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


@login_required
def dashboard(request):
    return render(request=request, template_name="dashboard.html")


def question_redirect(meeting_id):
    meeting = CooperativeMeeting.objects.get(id=meeting_id)
    stage = meeting.meeting_stage
    if stage == 'requirement-initiator':
        return redirect('/meeting_requirement_initiator_reason/' + str(meeting_id))
    elif stage == 'question-reorganization':
        return redirect('/meeting_cooperative_reorganization/' + str(meeting_id))
    elif stage == 'question-termination':
        return redirect('/meeting_power_termination/' + str(meeting_id))
    elif stage == 'question-reception':
        return redirect('/meeting_members_reception/' + str(meeting_id))
    elif stage == 'preparation':
        return redirect('/meeting_preparation/' + str(meeting_id))
    
def execution_redirect(meeting_id):
    meeting = CooperativeMeeting.objects.get(id=meeting_id)
    type = meeting.meeting_type
    format = meeting.meeting_format
    if type == 'regular' or (type == 'irregular' and format == 'intramural'):
        return redirect('/meeting_intramural_execution/' + str(meeting_id))
    elif format == 'extramural':
        return redirect('/meeting_extramural_execution/' + str(meeting_id))


@login_required
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
            return redirect('/dashboard')
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


@login_required
def cooperative_members_data(request):
    user = request.user
    cooperative = Cooperative.objects.filter(cooperative_user=user).first()

    members_form_set = formset_factory(MemberForm, formset=BaseMemberFormSet, min_num=4)

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

            # Request.FILES check
            # File parser
            if request.FILES:
                fio_email_list = str(request.FILES['members_file'].read(), 'UTF-8').split(';')

                for member in fio_email_list:
                    fio_email = member.split(':')
                    fio = fio_email[0]
                    email_address = fio_email[1]

                    if fio and email_address:
                        new_members.append(
                            CooperativeMember(cooperative=cooperative, fio=fio, email_address=email_address))

            try:
                with transaction.atomic():
                    CooperativeMember.objects.filter(cooperative=cooperative).delete()
                    CooperativeMember.objects.bulk_create(new_members)

                    return redirect('/dashboard')

            except IntegrityError:
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


@login_required
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
                                                        )
                return redirect('/meeting_questions/' + str(obj.id))
            elif meeting_type == 'irregular':
                obj = CooperativeMeeting.objects.create(cooperative=cooperative,
                                                        meeting_type=meeting_type,
                                                        meeting_stage='format',
                                                        )
                return redirect('/meeting_format/' + str(obj.id))
        else:
            return redirect('/meeting_new')
    form = CooperativeMeetingTypeForm()
    return render(request=request, template_name="meeting_data/meeting_type.html", context={"form": form})


@login_required
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
                    return redirect('/meeting_questions/' + str(meeting_id))

            except IntegrityError:
                return redirect('/meeting_format/' + str(meeting_id))
        else:
            return redirect('/meeting_format/' + str(meeting_id))
    form = CooperativeMeetingFormatForm()
    return render(request=request, template_name="meeting_data/meeting_format.html", context={"form": form})


@login_required
def meeting_questions(request, meeting_id):
    meeting = CooperativeMeeting.objects.get(id=meeting_id)
    if meeting.meeting_type == "regular":
        form = RegularQuestionsForm(initial={'questions' : CooperativeQuestion.objects.filter(
                                                                        is_report_approval=True)})
    elif meeting.meeting_type == "irregular" and meeting.meeting_format == "intramural":
        form = IntramuralQuestionsForm()
    elif meeting.meeting_type == "irregular" and meeting.meeting_format == "extramural":
        form = ExtramuralQuestionsForm()

    if request.method == "POST":
        if meeting.meeting_type == 'regular':
            form = RegularQuestionsForm(request.POST, 
                            initial={'questions' : CooperativeQuestion.objects.filter(
                                                                is_report_approval=True)})
        elif meeting.meeting_type == "irregular" and meeting.meeting_format == 'extramural':
            form = ExtramuralQuestionsForm(request.POST)
        elif meeting.meeting_type == "irregular" and meeting.meeting_format == 'intramural':
            form = IntramuralQuestionsForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    meeting = CooperativeMeeting.objects.get(id=meeting_id)
                    for question in form.cleaned_data.get('questions'):
                        meeting.questions.add(question)
                    meeting.save()
                    if meeting.meeting_type == 'regular':
                        meeting.questions.add(CooperativeQuestion.objects.get(
                                                    is_report_approval=True).id)
                        meeting.save()                        
                    if meeting.meeting_type == 'irregular':
                        meeting.meeting_stage = 'requirement-initiator'
                    elif meeting.questions.filter(question='Принятие решения о реорганизации кооператива').exists():
                        meeting.meeting_stage = 'question-reorganization'
                    elif meeting.questions.filter(question='Прекращение полномочий отдельных членов правления').exists():
                        meeting.meeting_stage = 'question-termination'
                    elif meeting.questions.filter(
                            question='Принятие решения о приеме граждан в члены кооператива').exists():
                        meeting.meeting_stage = 'question-reception'
                    else:
                        meeting.meeting_stage = 'preparation'

                    meeting.save()
                    return question_redirect(meeting_id)

            except IntegrityError:
                return redirect('/meeting_questions/' + str(meeting_id))
        else:
            print(form.errors.as_data())
            return redirect('/meeting_questions/' + str(meeting_id))

    return render(request=request, template_name="meeting_data/meeting_questions.html", context={"form": form})


@login_required
def meeting_requirement_initiator_reason(request, meeting_id):
    cooperative = Cooperative.objects.get(cooperative_user=request.user)
    cooperative_meeting = CooperativeMeeting.objects.get(id=meeting_id)
    if cooperative_meeting.meeting_type == 'regular':
        return redirect('/meeting_preparation/' + str(meeting_id))
    members_representatives_form_set = formset_factory(MemberRepresentativeForm, formset=BaseFormSet, extra=0)

    cooperative_members = CooperativeMember.objects.filter(cooperative=cooperative)
    member_data = [{'cooperative_member_id': x.id, 'cooperative_member': x.fio}
                   for x in cooperative_members]
    if request.method == "POST":
        form = MeetingRequirementInitiatorReasonFrom(request.POST)
        member_representative_formset = members_representatives_form_set(request.POST)

        if form.is_valid() and form.cleaned_data.get('initiator') != 'members':
            try:
                with transaction.atomic():
                    meeting = CooperativeMeeting.objects.get(id=meeting_id)
                    meeting.initiator = form.cleaned_data.get('initiator')
                    meeting.reason = form.cleaned_data.get('reason')
                    if form.cleaned_data.get('initiator') == 'chairman':
                        if meeting.questions.filter(question='Принятие решения о реорганизации кооператива').exists():
                            meeting.meeting_stage = 'question-reorganization'
                        elif meeting.questions.filter(
                                question='Прекращение полномочий отдельных членов правления').exists():
                            meeting.meeting_stage = 'question-termination'
                        elif meeting.questions.filter(
                                question='Принятие решения о приеме граждан в члены кооператива').exists():
                            meeting.meeting_stage = 'question-reception'
                        else:
                            meeting.meeting_stage = 'preparation'
                        meeting.save()
                        return question_redirect(meeting_id)

                    else:
                        meeting.meeting_stage = 'requirement-creation'
                        meeting.save()
                        return redirect('/meeting_requirement_creation/' + str(meeting_id))
            except IntegrityError:
                return redirect('/meeting_requirement_initiator_reason/' + str(meeting_id))

        if form.is_valid() and member_representative_formset.is_valid():
            initiator_members = []

            for member_representative_form in member_representative_formset:
                cooperative_member = CooperativeMember.objects.get(
                    id=member_representative_form.cleaned_data.get('cooperative_member_id'))
                is_initiator = member_representative_form.cleaned_data.get('is_initiator')
                representatives_request = member_representative_form.cleaned_data.get('representatives_request')
                representative = member_representative_form.cleaned_data.get('representative')

                if cooperative_member and representative and representatives_request == True:
                    initiator_members.append(CooperativeMemberInitiator(cooperative_meeting=cooperative_meeting,
                                                                        cooperative_member=cooperative_member,
                                                                        representative=representative))
                elif cooperative_member and is_initiator == True:
                    initiator_members.append(CooperativeMemberInitiator(cooperative_meeting=cooperative_meeting,
                                                                        cooperative_member=cooperative_member))

            try:
                with transaction.atomic():
                    meeting = CooperativeMeeting.objects.get(id=meeting_id)
                    meeting.initiator = form.cleaned_data.get('initiator')
                    meeting.reason = form.cleaned_data.get('reason')
                    meeting.meeting_stage = 'requirement-creation'
                    meeting.save()
                    CooperativeMemberInitiator.objects.bulk_create(initiator_members)
                    return redirect('/meeting_requirement_creation/' + str(meeting_id))

            except IntegrityError:
                return redirect('/meeting_requirement_initiator_reason/' + str(meeting_id))
        else:
            return redirect('/meeting_requirement_initiator_reason/' + str(meeting_id))
    else:
        member_representative_formset = members_representatives_form_set(initial=member_data)
    form = MeetingRequirementInitiatorReasonFrom()
    context = {
        'form': form,
        'member_representative_formset': member_representative_formset,
    }

    return render(request=request, template_name="meeting_data/meeting_initiator_reason.html", context=context)


@login_required
def meeting_requirement_creation(request, meeting_id):
    cooperative_meeting = CooperativeMeeting.objects.get(id=meeting_id)
    cooperative_members = CooperativeMember.objects.filter(
        cooperative=cooperative_meeting.cooperative).order_by('email_address')
    if cooperative_meeting.meeting_type == 'regular':
        return redirect('/meeting_preparation/' + str(meeting_id))
    if request.method == "POST":
        if 'create_requirement' in request.POST:
            requirement = None
            # TODO requirement = create_requirement(meeting)
           
            if cooperative_meeting.initiator == 'members':
                members = []
                representatives = []
                for member in cooperative_members:
                    representative = CooperativeMemberInitiator.objects.get(cooperative_member=member, 
                                                                        cooperative_meeting=cooperative_meeting).representative
                    if representative != '':
                        representatives.append(representative)
                    else:
                        members.append(member.fio)
            else:
                members = []
                representatives = []
                
            requirement = create_requirement(cooperative_meeting, members, representatives)

            filename = "Требование.docx"
            response = HttpResponse(requirement,
                                    content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            disposition = 'attachment'
            try:
                filename.encode('ascii')
                file_expr = 'filename="{}"'.format(filename)
            except UnicodeEncodeError:
                file_expr = "filename*=utf-8''{}".format(quote(filename))
            response.headers['Content-Disposition'] = '{}; {}'.format(disposition, file_expr)
            return response

        elif 'continue' in request.POST:
            try:
                with transaction.atomic():
                    meeting = CooperativeMeeting.objects.get(id=meeting_id)
                    meeting.meeting_stage = 'requirement-approval'
                    meeting.save()
                    return redirect('/meeting_requirement_approval/' + str(meeting_id))

            except IntegrityError:
                return redirect('/meeting_requirement_creation/' + str(meeting_id))
    return render(request=request, template_name="meeting_data/meeting_requirement_creation.html", context={})


@login_required
def meeting_requirement_approval(request, meeting_id):
    cooperative_meeting = CooperativeMeeting.objects.get(id=meeting_id)
    members = CooperativeMember.objects.filter(cooperative=cooperative_meeting.cooperative)
    if cooperative_meeting.meeting_type == 'regular':
        return redirect('/meeting_preparation/' + str(meeting_id))
    if request.method == "POST":
        form = MeetingApprovalForm(request.POST)
        if form.is_valid():
            conduct_decision = form.cleaned_data.get('conduct_decision')
            conduct_reason = form.cleaned_data.get('conduct_reason')
            try:
                with transaction.atomic():
                    meeting = CooperativeMeeting.objects.get(id=meeting_id)
                    meeting.conduct_decision = conduct_decision == "True"
                    meeting.conduct_reason = int(conduct_reason)

                    if meeting.questions.filter(question='Принятие решения о реорганизации кооператива').exists():
                        meeting.meeting_stage = 'question-reorganization'
                    elif meeting.questions.filter(
                            question='Прекращение полномочий отдельных членов правления').exists():
                        meeting.meeting_stage = 'question-termination'
                    elif meeting.questions.filter(
                            question='Принятие решения о приеме граждан в члены кооператива').exists():
                        meeting.meeting_stage = 'question-reception'
                    else:
                        meeting.meeting_stage = 'preparation'

                    meeting.save()

            except IntegrityError:
                return redirect('/meeting_requirement_approval/' + str(meeting_id))

            if 'create_decision' in request.POST:
                decision_number = 1
                requirement = create_decision(decision_number, meeting)
                filename = "Решение о проведении собрания.docx"
                response = HttpResponse(requirement,
                                        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                disposition = 'attachment'
                try:
                    filename.encode('ascii')
                    file_expr = 'filename="{}"'.format(filename)
                except UnicodeEncodeError:
                    file_expr = "filename*=utf-8''{}".format(quote(filename))
                response.headers['Content-Disposition'] = '{}; {}'.format(disposition, file_expr)
                return response

            elif 'continue' in request.POST:
                if conduct_decision == "True":
                    # TODO SEND decision
                    return question_redirect(meeting_id)
                else:
                    return redirect('/dashboard/')
        else:
            return redirect('/meeting_requirement_approval/' + str(meeting_id))
    form = MeetingApprovalForm()
    return render(request=request, template_name="meeting_data/meeting_requirement_approval.html",
                  context={"form": form})


@login_required
def meeting_cooperative_reorganization(request, meeting_id):
    cooperative_meeting = CooperativeMeeting.objects.get(id=meeting_id)
    accepted_members_form_set = formset_factory(MemberTransferFioForm, formset=BaseFormSet)

    if request.method == "POST":
        form = MeetingCooperativeReorganizationForm(request.POST)
        accepted_members_formset = accepted_members_form_set(request.POST)

        if form.is_valid() and accepted_members_formset.is_valid():
            accepted_members = []

            for accepted_member_form in accepted_members_formset:
                fio = accepted_member_form.cleaned_data.get('fio')
                accepted_members.append(CooperativeReorganizationAcceptedMember(cooperative_meeting=cooperative_meeting,
                                                                                fio=fio))

            try:
                with transaction.atomic():
                    meeting = CooperativeMeeting.objects.get(id=meeting_id)
                    reorganization_data = CooperativeMeetingReorganization.objects.create(
                        cooperative_meeting=cooperative_meeting, convert_name=form.cleaned_data.get('convert_name'),
                        responsible_name=form.cleaned_data.get('responsible_name'))
                    reorganization_data.save()
                    CooperativeReorganizationAcceptedMember.objects.bulk_create(accepted_members)
                    if meeting.questions.filter(question='Прекращение полномочий отдельных членов правления').exists():
                        meeting.meeting_stage = 'question-termination'
                    elif meeting.questions.filter(
                            question='Принятие решения о приеме граждан в члены кооператива').exists():
                        meeting.meeting_stage = 'question-reception'
                    else:
                        meeting.meeting_stage = 'preparation'
                    meeting.save()
                    return question_redirect(meeting_id)

            except IntegrityError:
                return redirect('/meeting_cooperative_reorganization/' + str(meeting_id))
        else:
            return redirect('/meeting_cooperative_reorganization/' + str(meeting_id))
    else:
        accepted_members_formset = accepted_members_form_set()
    form = MeetingCooperativeReorganizationForm()
    context = {
        'form': form,
        'accepted_members_formset': accepted_members_formset,
    }

    return render(request=request, template_name="meeting_data/meeting_cooperative_reorganization.html",
                  context=context)


@login_required
def meeting_power_termination(request, meeting_id):
    cooperative_meeting = CooperativeMeeting.objects.get(id=meeting_id)
    members_form_set = formset_factory(ChairmanMemberFioForm, formset=BaseFormSet)

    if request.method == "POST":
        members_formset = members_form_set(request.POST)

        if members_formset.is_valid():
            terminated_members = []

            for member_form in members_formset:
                fio = member_form.cleaned_data.get('fio')
                terminated_members.append(
                    CooperativeTerminatedMember(cooperative_meeting=cooperative_meeting, fio=fio))

            try:
                with transaction.atomic():
                    meeting = CooperativeMeeting.objects.get(id=meeting_id)
                    CooperativeTerminatedMember.objects.bulk_create(terminated_members)
                    if meeting.questions.filter(
                            question='Принятие решения о приеме граждан в члены кооператива').exists():
                        meeting.meeting_stage = 'question-reception'
                    else:
                        meeting.meeting_stage = 'preparation'
                    meeting.save()
                    return question_redirect(meeting_id)

            except IntegrityError:
                return redirect('/meeting_power_termination/' + str(meeting_id))
        else:
            return redirect('/meeting_power_termination/' + str(meeting_id))
    else:
        members_formset = members_form_set()
    context = {
        'members_formset': members_formset,
    }
    return render(request=request, template_name="meeting_data/meeting_power_termination.html",
                  context=context)


@login_required
def meeting_members_reception(request, meeting_id):
    cooperative_meeting = CooperativeMeeting.objects.get(id=meeting_id)
    members_form_set = formset_factory(MemberAcceptFioForm, formset=BaseFormSet)

    if request.method == "POST":
        members_formset = members_form_set(request.POST)

        if members_formset.is_valid():
            accepted_members = []

            for member_form in members_formset:
                fio = member_form.cleaned_data.get('fio')
                accepted_members.append(
                    CooperativeAcceptedMember(cooperative_meeting=cooperative_meeting, fio=fio))

            try:
                with transaction.atomic():
                    meeting = CooperativeMeeting.objects.get(id=meeting_id)
                    CooperativeAcceptedMember.objects.bulk_create(accepted_members)
                    meeting.meeting_stage = 'preparation'
                    meeting.save()
                    return redirect('/meeting_preparation/' + str(meeting_id))

            except IntegrityError:
                return redirect('/meeting_members_reception/' + str(meeting_id))
        else:
            return redirect('/meeting_members_reception/' + str(meeting_id))
    else:
        members_formset = members_form_set()
    context = {
        'members_formset': members_formset,
    }
    return render(request=request, template_name="meeting_data/meeting_members_reception.html",
                  context=context)


@login_required
def meeting_preparation(request, meeting_id):
    meeting = CooperativeMeeting.objects.get(id=meeting_id)
    cooperative_members = CooperativeMember.objects.filter(cooperative=meeting.cooperative)
   
    if CooperativeReorganizationAcceptedMember.objects.filter(cooperative_meeting=meeting).exists():
        reorganization_accepted_members = CooperativeReorganizationAcceptedMember.objects.filter(cooperative_meeting=meeting)
    else:
        reorganization_accepted_members = []
    
    if CooperativeTerminatedMember.objects.filter(cooperative_meeting=meeting).exists():
        terminated_members = CooperativeTerminatedMember.objects.filter(cooperative_meeting=meeting)
    else:
        terminated_members = []
        
    if CooperativeAcceptedMember.objects.filter(cooperative_meeting=meeting).exists():
        accepted_members = CooperativeAcceptedMember.objects.filter(cooperative_meeting=meeting)
    else:
        accepted_members = []

    if CooperativeMeetingReorganization.objects.filter(cooperative_meeting=meeting).exists():
        responsible_name = CooperativeMeetingReorganization.objects.get(cooperative_meeting=meeting).responsible_name
        convert_name = CooperativeMeetingReorganization.objects.get(cooperative_meeting=meeting).convert_name
    else:
        responsible_name = ''
        convert_name = ''

    if meeting.meeting_type == "regular":
        title = "Стадия подготовки очередного собрания"
        form = IntramuralPreparationForm()
    elif meeting.meeting_type == "irregular" and meeting.meeting_format == "intramural":
        title = "Стадия подготовки внеочередного очного собрания"
        form = IntramuralPreparationForm()
    elif meeting.meeting_type == "irregular" and meeting.meeting_format == "extramural":
        title = "Стадия подготовки внеочередного заочного собрания"
        form = ExtramuralPreparationForm()

    if request.method == "POST":
        if meeting.meeting_type == "regular":
            form = IntramuralPreparationForm(request.POST)
        elif meeting.meeting_type == "irregular" and meeting.meeting_format == "intramural":
            form = IntramuralPreparationForm(request.POST)
        elif meeting.meeting_type == "irregular" and meeting.meeting_format == "extramural":
            form = ExtramuralPreparationForm(request.POST)

        if form.is_valid():
            meeting = CooperativeMeeting.objects.get(id=meeting_id)
            if meeting.meeting_type == "regular" or (
                    meeting.meeting_type == "irregular" and meeting.meeting_format == "intramural"):
                try:
                    with transaction.atomic():
                        meeting = CooperativeMeeting.objects.get(id=meeting_id)
                        meeting.date = form.cleaned_data.get('date')
                        meeting.time = form.cleaned_data.get('time')
                        meeting.place = form.cleaned_data.get('place')
                        meeting.save()

                except IntegrityError:
                    return redirect('/meeting_preparation/' + str(meeting_id))

            elif meeting.meeting_type == "irregular" and meeting.meeting_format == "extramural":
                try:
                    with transaction.atomic():
                        meeting = CooperativeMeeting.objects.get(id=meeting_id)
                        meeting.date = form.cleaned_data.get('date')
                        meeting.time = form.cleaned_data.get('time')
                        meeting.save()

                except IntegrityError:
                    return redirect('/meeting_preparation/' + str(meeting_id))

            files = request.FILES.getlist('appendix')

            if 'create_notification' in request.POST:
                # TODO notification = create_notification(meeting)
                notification_number = 1
                for member in cooperative_members:
                    notification = create_notification(notification_number, member.pk, 
                                                member.fio, meeting, responsible_name,
                                                convert_name, reorganization_accepted_members, 
                                                terminated_members, accepted_members, files)
                    notification_number += 1
                filename = "Уведомление.docx"
                response = HttpResponse(notification,
                                        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                disposition = 'attachment'
                try:
                    filename.encode('ascii')
                    file_expr = 'filename="{}"'.format(filename)
                except UnicodeEncodeError:
                    file_expr = "filename*=utf-8''{}".format(quote(filename))
                response.headers['Content-Disposition'] = '{}; {}'.format(disposition, file_expr)
                return response

            elif 'save_and_continue' in request.POST:
                # files = request.FILES.getlist('appendix')
                send_notification(meeting, files)

                return redirect('/meeting_execution')

        else:
            return redirect('/intramural_preparation')

    return render(request=request, template_name="meeting_data/meeting_preparation.html",
                  context={"form": form, "title": title})

@login_required
def meeting_execution(request, meeting_id):
    form = ExecutionForm()
    if request.method == "POST":
        form = ExecutionForm(request.POST)

        if form.is_valid():
            meeting_chairman_type = form.cleaned_data.get('meeting_chairman_type')
            if meeting_chairman_type == 'chairman':
                try:
                    with transaction.atomic():
                        cooperative = Cooperative.objects.get(cooperative_user=request.user)
                        meeting = CooperativeMeeting.objects.get(id=meeting_id)
                        meeting.meeting_chairman = cooperative.chairman_name
                        meeting.vote_counter = form.cleaned_data.get('vote_counter')
                        meeting.secretary = form.cleaned_data.get('secretary')
                        meeting.save()

                except IntegrityError:
                    return redirect('/meeting_execution/' + str(meeting_id))
            
                #return execution_redirect(meeting_id)
                return redirect('/meeting_execution/' + str(meeting_id))
        
            elif meeting_chairman_type == 'member':
                try:
                    with transaction.atomic():
                        meeting = CooperativeMeeting.objects.get(id=meeting_id)
                        meeting.meeting_chairman = form.cleaned_data.get('another_member')
                        meeting.vote_counter = form.cleaned_data.get('vote_counter')
                        meeting.secretary = form.cleaned_data.get('secretary')
                        meeting.save()

                except IntegrityError:
                    return redirect('/meeting_execution/' + str(meeting_id))
            
                #return execution_redirect(meeting_id)
                return redirect('/meeting_execution/' + str(meeting_id))

        else:
            return redirect('/meeting_execution/' + str(meeting_id))
    
    return render(request=request, template_name="meeting_data/meeting_execution.html",
                  context={'form' : form})

