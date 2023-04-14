from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.forms import formset_factory, BaseFormSet
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse
from urllib.parse import quote

from doc import create_notification, create_requirement, create_decision, create_protocol, create_list, create_bulletin
from emails import *
from .forms import UserRegisterForm, UserLoginForm, CooperativeDataForm, CooperativeMembersForm, MemberForm, \
    BaseMemberFormSet, RegularQuestionsForm, ExtramuralQuestionsForm, \
    IntramuralQuestionsForm, IrregularIntramuralPreparationForm, CooperativeMeetingTypeForm, \
    CooperativeMeetingFormatForm, \
    IrregularExtramuralPreparationForm, MeetingRequirementInitiatorReasonFrom, MeetingApprovalForm, \
    MemberRepresentativeForm, MeetingCooperativeReorganizationForm, MemberTransferFioForm, ChairmanMemberFioForm, \
    MemberAcceptFioForm, ExecutionForm, IntramuralExecutionAttendantForm, \
    ExtramuralExecutionAttendantForm, MeetingChairmanAnotherMember, \
    ExecutionAskedQuestion, ExecutionQuestionInfoForm, ExecutionVoting, ExecutionFIOVoting, MemberVotes, \
    ExecutionCooperativeReorganizationForm, BoardMembersCandidate, BaseMemberVoteFormSet, BoardMembersForm, \
    ExecutionTerminationDateForm, RegularIntramuralPreparationForm, MeetingFinishNoQuorumForm, MeetingFinishQuorumForm
from .models import Cooperative, CooperativeMember, CooperativeMeeting, CooperativeMemberInitiator, \
    CooperativeReorganizationAcceptedMember, CooperativeMeetingReorganization, CooperativeTerminatedMember, \
    CooperativeAcceptedMember, CooperativeQuestion, CooperativeMeetingAskedQuestion, CooperativeMeetingSubQuestion, \
    CooperativeMeetingMemberCandidate, CooperativeMeetingTSZH, CooperativeMeetingAttendant


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
        return redirect('/meeting_execution_intramural/' + str(meeting_id))
    elif format == 'extramural':
        return redirect('/meeting_execution_extramural/' + str(meeting_id))


def sub_question_init(meeting_id):
    sub_questions_list = []
    meeting = CooperativeMeeting.objects.get(id=meeting_id)
    meeting_questions_object = meeting.questions.all()
    for question in meeting_questions_object:
        if question.id == 6:
            sub_question = f"1. Принятие решения о реорганизации кооператива “{meeting.cooperative.cooperative_name}” в форме преобразования в товарищество собственников жилья."
        elif question.id == 11:
            if CooperativeTerminatedMember.objects.filter(cooperative_meeting=meeting,
                                                          sequential_id=1).exists():
                member = CooperativeTerminatedMember.objects.get(cooperative_meeting=meeting,
                                                                 sequential_id=1)
                sub_question = f"1. Досрочное прекращение полномочий члена правления ЖК «{meeting.cooperative.cooperative_name}» {member.fio}"
            else:
                continue
        elif question.id == 20:
            if CooperativeAcceptedMember.objects.filter(cooperative_meeting=meeting,
                                                        sequential_id=1).exists():
                member = CooperativeAcceptedMember.objects.get(cooperative_meeting=meeting,
                                                               sequential_id=1)
                sub_question = f"1. Принятие в члены жилищного кооператива “{meeting.cooperative.cooperative_name}” {member.fio}"
            else:
                continue
        else:
            sub_question = ""
        sub_questions_list.append(
            CooperativeMeetingSubQuestion(cooperative_meeting=meeting, question_id=question.id, sub_question_id=1,
                                          title=question.question, sub_question=sub_question))
    try:
        with transaction.atomic():
            CooperativeMeetingSubQuestion.objects.bulk_create(sub_questions_list)
    except IntegrityError:
        return sub_question_init(meeting_id)
    first_sub_question = CooperativeMeetingSubQuestion.objects.filter(cooperative_meeting=meeting).first()
    if first_sub_question:
        return execution_sub_question_redirect(meeting_id, first_sub_question.question_id,
                                               first_sub_question.sub_question_id)
    else:
        return redirect('/meeting_finish/' + str(meeting_id))


def sub_question_create(meeting_id, question_id, sub_question_id):
    meeting = CooperativeMeeting.objects.get(id=meeting_id)
    sub_question_first = CooperativeMeetingSubQuestion.objects.get(cooperative_meeting=meeting,
                                                                   question_id=question_id,
                                                                   sub_question_id=1)
    if question_id == 6:
        tszh_data = CooperativeMeetingTSZH.objects.get(cooperative_meeting=meeting)
        if sub_question_id > 1 and sub_question_first.decision == False:
            if CooperativeMeetingSubQuestion.objects.filter(cooperative_meeting=meeting,
                                                            decision__isnull=True).exists():
                sub_question_object = CooperativeMeetingSubQuestion.objects.get(cooperative_meeting=meeting,
                                                                                decision__isnull=True)
                return execution_sub_question_redirect(meeting_id, sub_question_object.question_id,
                                                       sub_question_object.sub_question_id)
            else:
                return redirect('/meeting_finish/' + str(meeting_id))
        if sub_question_id == 2:
            sub_question = "2. Утверждения порядка реорганизации Кооператива в форме преобразования"
        elif sub_question_id == 3:
            sub_question = "3. Утверждение передаточного акта, актов инвентаризации и иных документов бухгалтерского учета"
        elif sub_question_id == 4:
            sub_question = f"4. Утверждение Устава товарищества собственников жилья “{tszh_data.name}”"
        elif sub_question_id == 5:
            sub_question = f"5. Избрание Правления товарищества собственников жилья “{tszh_data.name}”"
        elif sub_question_id == 6:
            sub_question = f"6. Избрание Председателя Правления товарищества собственников жилья “{tszh_data.name}” из числа членов Правления"
        elif sub_question_id == 7:
            reorganization_data = CooperativeMeetingReorganization.objects.get(cooperative_meeting=meeting)
            sub_question = f"7. Принятие решения о государственной регистрации преобразования жилищного кооператива “{meeting.cooperative.cooperative_name}” в товарищество собственников жилья “{tszh_data.name}” и назначении ответственным за подачу документов в регистрирующий орган “{reorganization_data.responsible_name}”"
        elif sub_question_id > 7:
            if CooperativeReorganizationAcceptedMember.objects.filter(cooperative_meeting=meeting,
                                                                      sequential_id=sub_question_id - 7).exists():
                member = CooperativeReorganizationAcceptedMember.objects.get(cooperative_meeting=meeting,
                                                                             sequential_id=sub_question_id - 7)
                sub_question = f"{sub_question_id}. Принятие “{member.fio}” в члены товарищества собственников жилья “{tszh_data.name}”."
            else:
                if CooperativeMeetingSubQuestion.objects.filter(cooperative_meeting=meeting,
                                                                decision__isnull=True).exists():
                    sub_question_object = CooperativeMeetingSubQuestion.objects.filter(cooperative_meeting=meeting,
                                                                                       decision__isnull=True).first()
                    return execution_sub_question_redirect(meeting_id, sub_question_object.question_id,
                                                           sub_question_object.sub_question_id)
                else:
                    return redirect('/meeting_finish/' + str(meeting_id))

    elif question_id == 11:
        if sub_question_id > 1:
            if CooperativeTerminatedMember.objects.filter(cooperative_meeting=meeting,
                                                          sequential_id=sub_question_id).exists():
                member = CooperativeTerminatedMember.objects.get(cooperative_meeting=meeting,
                                                                 sequential_id=sub_question_id)
                sub_question = f"{sub_question_id}. Досрочное прекращение полномочий члена правления ЖК «{meeting.cooperative.cooperative_name}» {member.fio}"
            else:
                if CooperativeMeetingSubQuestion.objects.filter(cooperative_meeting=meeting,
                                                                decision__isnull=True).exists():
                    sub_question_object = CooperativeMeetingSubQuestion.objects.filter(cooperative_meeting=meeting,
                                                                                       decision__isnull=True).first()
                    return execution_sub_question_redirect(meeting_id, sub_question_object.question_id,
                                                           sub_question_object.sub_question_id)
                else:
                    return redirect('/meeting_finish/' + str(meeting_id))
    elif question_id == 20:
        if sub_question_id > 1:
            if CooperativeAcceptedMember.objects.filter(cooperative_meeting=meeting,
                                                        sequential_id=sub_question_id).exists():
                member = CooperativeAcceptedMember.objects.get(cooperative_meeting=meeting,
                                                               sequential_id=sub_question_id)
                sub_question = f"{sub_question_id}. Принятие в члены жилищного кооператива “{meeting.cooperative.cooperative_name}” {member.fio}"
            else:
                if CooperativeMeetingSubQuestion.objects.filter(cooperative_meeting=meeting,
                                                                decision__isnull=True).exists():
                    sub_question_object = CooperativeMeetingSubQuestion.objects.filter(cooperative_meeting=meeting,
                                                                                       decision__isnull=True).first()
                    return execution_sub_question_redirect(meeting_id, sub_question_object.question_id,
                                                           sub_question_object.sub_question_id)
                else:
                    return redirect('/meeting_finish/' + str(meeting_id))
    try:
        with transaction.atomic():
            CooperativeMeetingSubQuestion.objects.create(cooperative_meeting=meeting,
                                                         question_id=question_id,
                                                         sub_question_id=sub_question_id,
                                                         title=sub_question_first.title,
                                                         sub_question=sub_question)
    except IntegrityError:
        return sub_question_create(meeting_id, question_id, sub_question_id)

    return execution_sub_question_redirect(meeting_id, question_id, sub_question_id)


def execution_sub_question_redirect(meeting_id, question_id, sub_question_id):
    meeting = CooperativeMeeting.objects.get(id=meeting_id)

    if question_id in [16] and sub_question_id > 1:
        if CooperativeMeetingSubQuestion.objects.filter(cooperative_meeting=meeting,
                                                        decision__isnull=True).exists():
            sub_question_object = CooperativeMeetingSubQuestion.objects.get(cooperative_meeting=meeting,
                                                                            decision__isnull=True)
            return execution_sub_question_redirect(meeting_id, sub_question_object.question_id,
                                                   sub_question_object.sub_question_id)
        else:
            return redirect('/meeting_finish/' + str(meeting_id))

    if CooperativeMeetingSubQuestion.objects.filter(cooperative_meeting=meeting,
                                                    question_id=question_id,
                                                    sub_question_id=sub_question_id,
                                                    decision__isnull=True).exists():
        if meeting.meeting_format == "extramural":
            return redirect(
                '/execution_voting/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))
        elif question_id == 6 and (sub_question_id == 1 or sub_question_id == 5):
            return redirect(
                '/execution_before_info/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))
        else:
            return redirect(
                '/execution_common_info/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))
    else:
        return sub_question_create(meeting_id, question_id, sub_question_id)


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

    members_form_set = formset_factory(MemberForm, formset=BaseMemberFormSet, min_num=5, extra=0)

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
        form = RegularQuestionsForm(initial={'questions': CooperativeQuestion.objects.filter(
            is_report_approval=True)})
    elif meeting.meeting_type == "irregular" and meeting.meeting_format == "intramural":
        form = IntramuralQuestionsForm()
    elif meeting.meeting_type == "irregular" and meeting.meeting_format == "extramural":
        form = ExtramuralQuestionsForm()

    if request.method == "POST":
        if meeting.meeting_type == 'regular':
            form = RegularQuestionsForm(request.POST,
                                        initial={'questions': CooperativeQuestion.objects.filter(
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

                if cooperative_member and is_initiator == True:
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
                print('err')
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
    initiators = []
    if CooperativeMemberInitiator.objects.filter(cooperative_meeting=cooperative_meeting).exists():
        for initiator in CooperativeMemberInitiator.objects.filter(cooperative_meeting=cooperative_meeting):
            initiators.append(initiator)
    if cooperative_meeting.meeting_type == 'regular':
        return redirect('/meeting_preparation/' + str(meeting_id))
    if request.method == "POST":
        if cooperative_meeting.initiator == 'members':
            members = []
            for member in initiators:
                members.append(member.cooperative_member.fio)
        else:
            members = []

        requirement = create_requirement(cooperative_meeting, members)
        if 'create_requirement' in request.POST:
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
                    send_requirement(meeting, requirement)
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

            decision_number = 1
            decision = create_decision(decision_number, meeting)

            if 'create_decision' in request.POST:
                filename = "Решение о проведении собрания.docx"
                response = HttpResponse(decision,
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
                    send_decision(meeting, decision)
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
            counter = 0

            for accepted_member_form in accepted_members_formset:
                counter += 1
                fio = accepted_member_form.cleaned_data.get('fio')
                accepted_members.append(CooperativeReorganizationAcceptedMember(cooperative_meeting=cooperative_meeting,
                                                                                sequential_id=counter,
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
            counter = 0

            for member_form in members_formset:
                counter += 1
                fio = member_form.cleaned_data.get('fio')
                terminated_members.append(
                    CooperativeTerminatedMember(cooperative_meeting=cooperative_meeting, sequential_id=counter,
                                                fio=fio))

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
            counter = 0

            for member_form in members_formset:
                counter += 1
                fio = member_form.cleaned_data.get('fio')
                accepted_members.append(
                    CooperativeAcceptedMember(cooperative_meeting=cooperative_meeting, sequential_id=counter, fio=fio))

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
    meeting_questions_object = meeting.questions.all()

    if CooperativeReorganizationAcceptedMember.objects.filter(cooperative_meeting=meeting).exists():
        reorganization_accepted_members = CooperativeReorganizationAcceptedMember.objects.filter(
            cooperative_meeting=meeting)
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

    tooltip_data = "Приложения:"
    for question in meeting_questions_object:
        if question.id == 6:
            tooltip_data += """
            
            Для принятия решения о реорганизации кооператива:
            1. Устав ТСЖ, в который преобразуется кооператив
            2. Порядок реорганизации ЖК в форме преобразования в ТСЖ
            3. Передаточный акт
            4. Акты инвентаризации
            5. При необходимости - другие документы в соответствии с ч. 3 ст. 11 Закона о бухгалтерском учете, п. п. 2.5, 4.1 и 5.6 Методических указаний по инвентаризации.
            6. Кандидатуры на должность Председателя и членов Правления ТСЖ.
            7. Список граждан, подавших заявления о приеме в члены ТСЖ.
            8. Заявления граждан о приеме в члены ТСЖ.
            """
        elif question.id == 11:
            tooltip_data += """
            Для прекращения полномочий отдельных членов правления:
            1. Заявление об увольнении по собственному желанию
            ИЛИ 2. Жалоба/претензия членов ЖК на действия членов правления.
            """
        elif question.id == 16:
            tooltip_data += """
            Для утверждения годового отчета кооператива и годовой бухгалтерской (финансовой) отчетности кооператива:
            1. Проект годового отчета
            2. Бухгалтерская отчетность за год
            3. Заключение ревизионной комиссии
            """
        elif question.id == 20:
            tooltip_data += """
            Для принятия решения о приеме граждан в члены кооператива:
            Заявление о вступлении в кооператив"""
    if meeting.meeting_type == "regular":
        title = "Стадия подготовки очередного собрания"
        form = RegularIntramuralPreparationForm()
        m_type = 1
    elif meeting.meeting_type == "irregular" and meeting.meeting_format == "intramural":
        title = "Стадия подготовки внеочередного очного собрания"
        form = IrregularIntramuralPreparationForm()
        m_type = 2
    elif meeting.meeting_type == "irregular" and meeting.meeting_format == "extramural":
        title = "Стадия подготовки внеочередного заочного собрания"
        form = IrregularExtramuralPreparationForm()
        m_type = 3

    if request.method == "POST":
        if meeting.meeting_type == "regular":
            form = RegularIntramuralPreparationForm(request.POST)
            m_type = 1
        elif meeting.meeting_type == "irregular" and meeting.meeting_format == "intramural":
            form = IrregularIntramuralPreparationForm(request.POST)
            m_type = 2
        elif meeting.meeting_type == "irregular" and meeting.meeting_format == "extramural":
            form = IrregularExtramuralPreparationForm(request.POST)
            m_type = 3

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
                notification_number = 1
                for member in cooperative_members:
                    notification = create_notification(notification_number, member.pk,
                                                       member.fio, meeting, responsible_name,
                                                       convert_name, reorganization_accepted_members,
                                                       terminated_members, accepted_members, files)
                    send_notification_email(cooperative_meeting=meeting, notification=notification,
                                            user_attachments=files,
                                            member_email=member.email_address)
                    if meeting.meeting_type == "irregular" and meeting.meeting_format == "extramural":
                        bulletin = create_bulletin(meeting, member, terminated_members, accepted_members, 
                                                   notification_number, member.pk)
                        send_bulletin(bulletin=bulletin, member_email=member.email_address)
                    notification_number += 1

                return redirect('/meeting_execution/' + str(meeting_id))

        else:
            return redirect('/intramural_preparation')

    return render(request=request, template_name="meeting_data/meeting_preparation.html",
                  context={"form": form, "title": title, 'm_id': meeting_id, 'm_type': m_type,
                           'tooltip_data': tooltip_data})


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

                return execution_redirect(meeting_id)

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

                return execution_redirect(meeting_id)

        else:
            return redirect('/meeting_execution/' + str(meeting_id))

    return render(request=request, template_name="meeting_data/meeting_execution.html",
                  context={'form': form})


@login_required
def meeting_execution_attendance_intramural(request, meeting_id):
    cooperative = Cooperative.objects.get(cooperative_user=request.user)
    cooperative_meeting = CooperativeMeeting.objects.get(id=meeting_id)
    attendant_form_set = formset_factory(IntramuralExecutionAttendantForm, formset=BaseFormSet, extra=0)
    cooperative_members = CooperativeMember.objects.filter(cooperative=cooperative)
    member_data = [{'cooperative_member_id': x.id, 'cooperative_member': x.fio}
                   for x in cooperative_members]
    if CooperativeMeetingAttendant.objects.filter(cooperative_meeting=cooperative_meeting).exists():
        attendants = CooperativeMeetingAttendant.objects.filter(cooperative_meeting=cooperative_meeting)
    else:
        attendants = []
    if request.method == "POST":
        attendant_formset = attendant_form_set(request.POST)

        if attendant_formset.is_valid():
            attendants = []

            for attendant_form in attendant_formset:
                cooperative_member = CooperativeMember.objects.get(
                    id=attendant_form.cleaned_data.get('cooperative_member_id'))
                meeting_attendant_type = attendant_form.cleaned_data.get('meeting_attendant_type')
                representative = attendant_form.cleaned_data.get('representative')

                if cooperative_member and representative and meeting_attendant_type == 'representative':
                    attendants.append(CooperativeMeetingAttendant(cooperative_meeting=cooperative_meeting,
                                                                  cooperative_member=cooperative_member,
                                                                  representative_attends=True,
                                                                  representative_name=representative))
                elif cooperative_member and meeting_attendant_type == "member":
                    attendants.append(CooperativeMeetingAttendant(cooperative_meeting=cooperative_meeting,
                                                                  cooperative_member=cooperative_member))

            quorum = True
            if len(attendants) <= 0.5 * CooperativeMember.objects.filter(cooperative=cooperative).count():
                quorum = False
            if 'turnout_list' in request.POST:

                listt = create_list(attendants, cooperative_meeting)

                filename = "Явочный лист.docx"
                response = HttpResponse(listt,
                                        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                disposition = 'attachment'
                try:
                    filename.encode('ascii')
                    file_expr = 'filename="{}"'.format(filename)
                except UnicodeEncodeError:
                    file_expr = "filename*=utf-8''{}".format(quote(filename))
                response.headers['Content-Disposition'] = '{}; {}'.format(disposition, file_expr)
                return response

            try:
                with transaction.atomic():
                    meeting = CooperativeMeeting.objects.get(id=meeting_id)
                    meeting.quorum = quorum
                    meeting.save()
                    CooperativeMeetingAttendant.objects.bulk_create(attendants)
                    if quorum is True:
                        return sub_question_init(meeting_id)
                    else:
                        return redirect('/meeting_finish/' + str(meeting_id))

            except IntegrityError:
                return redirect('/meeting_execution_intramural/' + str(meeting_id))

        else:
            return redirect('/meeting_execution_intramural/' + str(meeting_id))
    else:
        attendant_formset = attendant_form_set(initial=member_data)
    context = {
        'attendant_formset': attendant_formset,
    }

    return render(request=request, template_name="meeting_data/meeting_execution_intramural.html", context=context)


@login_required
def meeting_execution_attendance_extramural(request, meeting_id):
    cooperative = Cooperative.objects.get(cooperative_user=request.user)
    cooperative_meeting = CooperativeMeeting.objects.get(id=meeting_id)
    attendant_form_set = formset_factory(ExtramuralExecutionAttendantForm, formset=BaseFormSet, extra=0)
    cooperative_members = CooperativeMember.objects.filter(cooperative=cooperative)
    member_data = [{'cooperative_member_id': x.id, 'cooperative_member': x.fio}
                   for x in cooperative_members]
    if request.method == "POST":
        attendant_formset = attendant_form_set(request.POST)

        if attendant_formset.is_valid():
            attendants = []

            for attendant_form in attendant_formset:
                cooperative_member = CooperativeMember.objects.get(
                    id=attendant_form.cleaned_data.get('cooperative_member_id'))
                meeting_attendant_type = attendant_form.cleaned_data.get('meeting_attendant_type')
                representative = attendant_form.cleaned_data.get('representative')

                if cooperative_member and representative and meeting_attendant_type == 'representative':
                    attendants.append(CooperativeMeetingAttendant(cooperative_meeting=cooperative_meeting,
                                                                  cooperative_member=cooperative_member,
                                                                  representative_attends=True,
                                                                  representative_name=representative))
                elif cooperative_member and meeting_attendant_type == "member":
                    attendants.append(CooperativeMeetingAttendant(cooperative_meeting=cooperative_meeting,
                                                                  cooperative_member=cooperative_member))

            quorum = True
            if len(attendants) <= 0.5 * CooperativeMember.objects.filter(cooperative=cooperative).count():
                quorum = False

            try:
                with transaction.atomic():
                    meeting = CooperativeMeeting.objects.get(id=meeting_id)
                    meeting.quorum = quorum
                    meeting.save()
                    CooperativeMeetingAttendant.objects.bulk_create(attendants)
                    if quorum is True:
                        return sub_question_init(meeting_id)
                    else:
                        return redirect('/meeting_finish/' + str(meeting_id))

            except IntegrityError:
                return redirect('/meeting_execution_extramural/' + str(meeting_id))

        else:
            return redirect('/meeting_execution_extramural/' + str(meeting_id))
    else:
        attendant_formset = attendant_form_set(initial=member_data)
    context = {
        'attendant_formset': attendant_formset,
    }

    return render(request=request, template_name="meeting_data/meeting_execution_extramural.html", context=context)


@login_required
def execution_before_info(request, meeting_id, question_id, sub_question_id):
    cooperative_meeting = CooperativeMeeting.objects.get(id=meeting_id)

    sub_question_object = CooperativeMeetingSubQuestion.objects.get(cooperative_meeting=cooperative_meeting,
                                                                    question_id=question_id,
                                                                    sub_question_id=sub_question_id)
    members_form_set = formset_factory(BoardMembersCandidate, formset=BaseMemberVoteFormSet)

    if request.method == "POST" and question_id == 6 and sub_question_id == 1:
        form = ExecutionCooperativeReorganizationForm(request.POST)

        if form.is_valid():

            try:
                with transaction.atomic():
                    CooperativeMeetingTSZH.objects.create(cooperative_meeting=cooperative_meeting,
                                                          name=form.cleaned_data.get('tszh_name'),
                                                          place=form.cleaned_data.get('tszh_place'))
                    return redirect('/execution_common_info/' + str(meeting_id) + '/' + str(question_id) + '/' + str(
                        sub_question_id))

            except IntegrityError:
                return redirect(
                    '/execution_before_info/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))
        else:
            return redirect(
                '/execution_before_info/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))

    elif request.method == "POST" and question_id == 6 and sub_question_id == 5:
        form = BoardMembersForm(request.POST)
        member_formset = members_form_set(request.POST)

        if form.is_valid() and member_formset.is_valid():

            try:
                member_list = []
                for member_form in member_formset:
                    if member_form.cleaned_data.get('fio') is not None:
                        member_list.append(CooperativeMeetingMemberCandidate(sub_question=sub_question_object,
                                                                             fio=member_form.cleaned_data.get('fio')))
                with transaction.atomic():
                    CooperativeMeetingMemberCandidate.objects.bulk_create(member_list)
                    sub_question_object.member_limit = int(form.cleaned_data.get('chosen_candidates_limit') or 0)
                    sub_question_object.save()
                    return redirect('/execution_common_info/' + str(meeting_id) + '/' + str(question_id) + '/' + str(
                        sub_question_id))

            except IntegrityError:
                return redirect(
                    '/execution_before_info/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))
        else:
            return redirect(
                '/execution_before_info/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))

    if question_id == 6 and sub_question_id == 1:
        form = ExecutionCooperativeReorganizationForm()
        context = {
            'title': sub_question_object.title,
            'sub_question': sub_question_object.sub_question,
            'form': form,
        }
        return render(request=request, template_name="meeting_data/execution/reorganization_tszh.html",
                      context=context)

    elif question_id == 6 and sub_question_id == 5:
        form = BoardMembersForm()
        member_formset = members_form_set()
        context = {
            'title': sub_question_object.title,
            'sub_question': sub_question_object.sub_question,
            'form': form,
            'member_formset': member_formset,
        }
        return render(request=request,
                      template_name="meeting_data/execution/reorganization_chairman_candidates.html",
                      context=context)


@login_required
def execution_common_info(request, meeting_id, question_id, sub_question_id):
    cooperative_meeting = CooperativeMeeting.objects.get(id=meeting_id)
    questions_form_set = formset_factory(ExecutionAskedQuestion, formset=BaseFormSet)

    sub_question_object = CooperativeMeetingSubQuestion.objects.get(cooperative_meeting=cooperative_meeting,
                                                                    question_id=question_id,
                                                                    sub_question_id=sub_question_id)

    if request.method == "POST":
        form = ExecutionQuestionInfoForm(request.POST)
        questions_formset = questions_form_set(request.POST)

        if form.is_valid() and questions_formset.is_valid():
            questions_list = []

            for question_form in questions_formset:
                question = question_form.cleaned_data.get('question')
                if question is not None:
                    questions_list.append(
                        CooperativeMeetingAskedQuestion(sub_question=sub_question_object, question=question))

            try:
                with transaction.atomic():
                    if form.cleaned_data.get('speaker') is not None:
                        sub_question_object.speaker = form.cleaned_data.get('speaker')
                        changes = True
                    if form.cleaned_data.get('theses') is not None:
                        sub_question_object.theses = form.cleaned_data.get('theses')
                        changes = True
                    if len(questions_list) > 0:
                        CooperativeMeetingAskedQuestion.objects.bulk_create(questions_list)
                    if changes:
                        sub_question_object.save()
                    return redirect(
                        '/execution_voting/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))

            except IntegrityError:
                return redirect(
                    '/execution_common_info/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))
        else:
            return redirect(
                '/execution_common_info/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))
    else:
        questions_formset = questions_form_set()
        form = ExecutionQuestionInfoForm()
    context = {
        'title': sub_question_object.title,
        'sub_question': sub_question_object.sub_question,
        'form': form,
        'questions_formset': questions_formset,
    }
    return render(request=request, template_name="meeting_data/execution/common_info.html", context=context)


def custom_key(member):
    return member['votes_for']


@login_required
def execution_voting(request, meeting_id, question_id, sub_question_id):
    cooperative_meeting = CooperativeMeeting.objects.get(id=meeting_id)

    sub_question_object = CooperativeMeetingSubQuestion.objects.get(cooperative_meeting=cooperative_meeting,
                                                                    question_id=question_id,
                                                                    sub_question_id=sub_question_id)
    attendants_number = CooperativeMeetingAttendant.objects.filter(cooperative_meeting=cooperative_meeting,
                                                                   cooperative_member__isnull=False).count()

    members_form_set = formset_factory(MemberVotes, formset=BaseFormSet, extra=0)
    if question_id == 6 and sub_question_id == 6:
        prev_sub_question = CooperativeMeetingSubQuestion.objects.get(cooperative_meeting=cooperative_meeting,
                                                                      question_id=question_id,
                                                                      sub_question_id=sub_question_id - 1)
        is_member_vote = CooperativeMeetingMemberCandidate.objects.filter(sub_question=prev_sub_question).exists()
        is_second_stage_member_vote = CooperativeMeetingMemberCandidate.objects.filter(sub_question=prev_sub_question,
                                                                                       votes_for__isnull=False).exists()

    else:
        is_member_vote = CooperativeMeetingMemberCandidate.objects.filter(sub_question=sub_question_object).exists()
        is_second_stage_member_vote = CooperativeMeetingMemberCandidate.objects.filter(sub_question=sub_question_object,
                                                                                       votes_for__isnull=False).exists()
    if request.method == "POST" and not is_member_vote:
        form = ExecutionVoting(request.POST)

        if form.is_valid():

            try:
                with transaction.atomic():
                    sub_question_object.votes_for = int(form.cleaned_data.get('votes_for') or 0)
                    sub_question_object.votes_against = int(form.cleaned_data.get('votes_against') or 0)
                    sub_question_object.votes_abstained = int(form.cleaned_data.get('votes_abstained') or 0)
                    sub_question_object.decision = form.cleaned_data.get('decision')
                    sub_question_object.save()
                    if question_id == 11:
                        return redirect(
                            '/execution_after_info/' + str(meeting_id) + '/' + str(question_id) + '/' + str(
                                sub_question_id))
                    else:
                        return execution_sub_question_redirect(meeting_id, question_id, sub_question_id + 1)

            except IntegrityError:
                return redirect(
                    '/execution_voting/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))
        else:
            return redirect(
                '/execution_voting/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))
    elif request.method == "POST" and is_member_vote:
        form = ExecutionFIOVoting(request.POST)
        member_formset = members_form_set(request.POST)

        if form.is_valid() and member_formset.is_valid():
            member_list = []
            candidate_list = []
            member_limit = sub_question_object.member_limit
            decision = None
            for member_form in member_formset:
                member_votes = int(member_form.cleaned_data.get('votes_for') or 0)
                if member_votes == 0:
                    continue
                else:
                    member_list.append({'fio': member_form.cleaned_data.get('fio'),
                                        'votes_for': member_votes})
            if is_second_stage_member_vote:
                if len(member_list) > 1:
                    member_list.sort(key=custom_key, reverse=True)
                    if member_list[0]['votes_for'] == member_list[1]['votes_for']:
                        decision = False
                        for member in member_list:
                            candidate = CooperativeMeetingMemberCandidate.objects.get(sub_question=prev_sub_question,
                                                                                      fio=member['fio'])
                            candidate.votes_for_second_stage = member['votes_for']
                            candidate.accepted_second_stage = False
                            candidate_list.append(candidate)
                    else:
                        candidate = CooperativeMeetingMemberCandidate.objects.get(sub_question=prev_sub_question,
                                                                                  fio=member_list[0]['fio'])
                        candidate.votes_for_second_stage = member_list[0]['votes_for']
                        candidate.accepted_second_stage = True
                        candidate_list.append(candidate)
                elif len(member_list) == 1:
                    candidate = CooperativeMeetingMemberCandidate.objects.get(sub_question=prev_sub_question,
                                                                              fio=member_list[0]['fio'])
                    candidate.votes_for_second_stage = member_list[0]['votes_for']
                    candidate.accepted_second_stage = True
                    candidate_list.append(candidate)

                else:
                    decision = False

            else:
                if len(member_list) > member_limit:
                    member_list.sort(key=custom_key, reverse=True)
                    if member_list[member_limit - 1]['votes_for'] == member_list[member_limit]['votes_for']:
                        decision = False
                        for member in member_list:
                            candidate = CooperativeMeetingMemberCandidate.objects.get(sub_question=sub_question_object,
                                                                                      fio=member['fio'])
                            candidate.votes_for = member['votes_for']
                            candidate.accepted = False
                            candidate_list.append(candidate)

                    else:
                        for i in range(member_limit):
                            candidate = CooperativeMeetingMemberCandidate.objects.get(sub_question=sub_question_object,
                                                                                      fio=member_list[i]['fio'])
                            candidate.votes_for = member_list[i]['votes_for']
                            candidate.accepted = True
                            candidate_list.append(candidate)

                elif len(member_list) == member_limit:
                    candidate = CooperativeMeetingMemberCandidate.objects.get(sub_question=sub_question_object,
                                                                              fio=member_list[0]['fio'])
                    candidate.votes_for = member_list[0]['votes_for']
                    candidate.accepted = True
                    candidate_list.append(candidate)

                else:
                    decision = False

            try:
                with transaction.atomic():
                    for candidate in candidate_list:
                        candidate.save()
                    sub_question_object.votes_abstained = int(form.cleaned_data.get('votes_abstained') or 0)
                    if decision is not None:
                        sub_question_object.decision = decision
                    else:
                        sub_question_object.decision = form.cleaned_data.get('decision')
                    sub_question_object.save()
                    return execution_sub_question_redirect(meeting_id, question_id, sub_question_id + 1)

            except IntegrityError:
                return redirect(
                    '/execution_voting/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))
        else:
            return redirect(
                '/execution_voting/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))

    if is_member_vote:
        form = ExecutionFIOVoting()
        candidate_data = []
        if is_second_stage_member_vote:
            candidates = CooperativeMeetingMemberCandidate.objects.filter(sub_question=prev_sub_question,
                                                                          accepted=True)
            for candidate in candidates:
                candidate_data.append({'fio': candidate.fio})
            member_limit = 1
        else:
            candidates = CooperativeMeetingMemberCandidate.objects.filter(sub_question=sub_question_object)
            for candidate in candidates:
                candidate_data.append({'fio': candidate.fio})
            member_limit = sub_question_object.member_limit

        member_formset = members_form_set(initial=candidate_data)

        context = {
            'title': sub_question_object.title,
            'sub_question': sub_question_object.sub_question,
            'form': form,
            'member_formset': member_formset,
            'attendants_number': attendants_number,
            'member_limit': member_limit,
        }
        return render(request=request, template_name="meeting_data/execution/vote_people.html", context=context)

    else:
        form = ExecutionVoting()
        context = {
            'title': sub_question_object.title,
            'sub_question': sub_question_object.sub_question,
            'form': form,
            'attendants_number': attendants_number,
        }
        return render(request=request, template_name="meeting_data/execution/vote_subquestion.html", context=context)


@login_required
def execution_after_info(request, meeting_id, question_id, sub_question_id):
    cooperative_meeting = CooperativeMeeting.objects.get(id=meeting_id)

    sub_question_object = CooperativeMeetingSubQuestion.objects.get(cooperative_meeting=cooperative_meeting,
                                                                    question_id=question_id,
                                                                    sub_question_id=sub_question_id)

    if request.method == "POST" and question_id == 11:
        form = ExecutionTerminationDateForm(request.POST)

        if form.is_valid():

            try:
                with transaction.atomic():
                    terminated_member = CooperativeTerminatedMember.objects.get(cooperative_meeting=cooperative_meeting,
                                                                                sequential_id=sub_question_id)
                    terminated_member.date = form.cleaned_data.get('date')
                    terminated_member.save()
                    return execution_sub_question_redirect(meeting_id, question_id, sub_question_id + 1)

            except IntegrityError:
                return redirect(
                    '/execution_after_info/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))
        else:
            return redirect(
                '/execution_after_info/' + str(meeting_id) + '/' + str(question_id) + '/' + str(sub_question_id))

    if question_id == 11:
        form = ExecutionTerminationDateForm()
        context = {
            'title': sub_question_object.title,
            'sub_question': sub_question_object.sub_question,
            'form': form,
        }
        return render(request=request, template_name="meeting_data/execution/termination_date.html",
                      context=context)


@login_required
def meeting_finish(request, meeting_id):
    meeting = CooperativeMeeting.objects.get(id=meeting_id)
    cooperative_members = CooperativeMember.objects.filter(cooperative=meeting.cooperative)

    if CooperativeReorganizationAcceptedMember.objects.filter(cooperative_meeting=meeting).exists():
        reorganization_accepted_members = CooperativeReorganizationAcceptedMember.objects.filter(
            cooperative_meeting=meeting)
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
        convert_name = CooperativeMeetingReorganization.objects.get(cooperative_meeting=meeting).convert_name
    else:
        convert_name = ''

    if CooperativeMeetingAttendant.objects.filter(cooperative_meeting=meeting).exists():
        attendants = CooperativeMeetingAttendant.objects.filter(cooperative_meeting=meeting)
    else:
        attendants = []

    if CooperativeMeetingSubQuestion.objects.filter(cooperative_meeting=meeting).exists():
        sub_questions = CooperativeMeetingSubQuestion.objects.filter(cooperative_meeting=meeting)
    else:
        sub_questions = []
    asked_questions = []
    for sub_question in sub_questions:
        if CooperativeMeetingAskedQuestion.objects.filter(sub_question=sub_question).exists():
            for asked_question in CooperativeMeetingAskedQuestion.objects.filter(sub_question=sub_question):
                asked_questions.append(asked_question)
    if request.method == "POST":
        meeting = CooperativeMeeting.objects.get(id=meeting_id)
        if meeting.quorum is True:
            form = MeetingFinishQuorumForm(request.POST)
        else:
            form = MeetingFinishNoQuorumForm(request.POST)
        if form.is_valid():
            if meeting.quorum is False:
                new_meeting = form.cleaned_data.get('new_meeting')
            else:
                new_meeting = False
            if 'create_protocol' in request.POST:
                for member in cooperative_members:
                    protocol = create_protocol(member, meeting, convert_name, attendants, sub_questions, asked_questions,
                                               terminated_members, accepted_members, reorganization_accepted_members,
                                               new_meeting, datetime.now().strftime('%H:%M:%S'))
                filename = "Протокол.docx"
                response = HttpResponse(protocol,
                                        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                disposition = 'attachment'
                try:
                    filename.encode('ascii')
                    file_expr = 'filename="{}"'.format(filename)
                except UnicodeEncodeError:
                    file_expr = "filename*=utf-8''{}".format(quote(filename))
                response.headers['Content-Disposition'] = '{}; {}'.format(disposition, file_expr)
                return response
            elif 'send_protocol' in request.POST:
                for member in cooperative_members:
                    protocol = create_protocol(member, meeting, convert_name, attendants, sub_questions, asked_questions,
                                               terminated_members, accepted_members, reorganization_accepted_members,
                                               new_meeting, datetime.now().strftime('%H:%M:%S'))
                    send_protocol(meeting, protocol, member.email_address)
            else:
                try:
                    with transaction.atomic():
                        meeting = CooperativeMeeting.objects.get(id=meeting_id)
                        meeting.meeting_stage = 'finished'
                        meeting.new_meeting = new_meeting
                        meeting.save()

                except IntegrityError:
                    return redirect(
                        '/meeting_finish/' + str(meeting_id))
                return redirect('dashboard')
    if meeting.quorum is True:
        form = MeetingFinishQuorumForm()
    else:
        form = MeetingFinishNoQuorumForm()
    return render(request=request, template_name="meeting_data/meeting_finish.html", context={'form': form})
