import datetime
import io
import jinja2

from docxtpl import DocxTemplate


def strings_creating(shift, elements):
    elements_string = '\t'
    for index, element in enumerate(elements):
        elements_string = elements_string + str(index + shift + 1) + '. ' + element + '\n\t'
    return elements_string


def create_list(attendants, meeting):
    tpl = DocxTemplate("/usr/src/app/doc/List.docx")

    n = len(attendants)

    hours = str(meeting.time).split(':')[0]
    minutes = str(meeting.time).split(':')[1]

    context = {'cooperative_name': meeting.cooperative.cooperative_name,
               'cooperative_address': meeting.cooperative.cooperative_address,
               'cooperative_itn': meeting.cooperative.cooperative_itn,
               'cooperative_telephone_number': meeting.cooperative.cooperative_telephone_number,
               'cooperative_email_address': meeting.cooperative.cooperative_email_address,
               'date': meeting.date,
               'hours': hours,
               'minutes': minutes,
               'chairman_name': meeting.cooperative.chairman_name,
               'list': []}

    i = 1
    for member in attendants:
        if member.representative_attends:
            fio = member.representative_name + '\n'
        else:
            fio = member.cooperative_member.fio + '\n'

        d = {
            'n': str(i) + '.',
            'fio': fio,
        }
        context['list'].append(d)
        i += 1

    jinja_env = jinja2.Environment(autoescape=True)
    tpl.render(context, jinja_env)
    tpl.save('/usr/src/app/List.docx')
    file_stream = io.BytesIO()
    tpl.save(file_stream)
    file_stream.seek(0)
    return file_stream


# def create_bulletin():


def create_protocol(cooperative_member, meeting, convert_name, attendants, speakers, asked_questions,
                    terminated_members, accepted_members, reorganization_accepted_members):
    members = '\t'
    number = 1
    for member in attendants:
        if member.representative_attends:
            members += str(
                number) + '. ' + member.representative_name + ', Представитель члена ЖК ' + member.cooperative_member.fio + '\n\t'
        else:
            members += str(number) + '. ' + member.cooperative_member.fio + '\n\t'
        number += 1

    questions_list = meeting.questions
    chosen_questions = []
    for question in questions_list.all():
        chosen_questions.append(question)

    questions = []
    full_speech = ''
    number = 1
    for question in chosen_questions:

        speech = ''
        if question.question == 'Принятие решения о реорганизации кооператива':
            for member in reorganization_accepted_members:
                questions.append('Принятие ' + member.fio +
                                 ' в члены товарищества собственников жилья «' + convert_name + '»')

        elif question.question == 'Прекращение полномочий отдельных членов правления':
            for member in terminated_members:
                questions.append('Досрочное прекращение полномочий члена Правления жилищного кооператива '
                                 + member.fio + '.')

        elif question.question == 'Принятие решения о приеме граждан в члены кооператива':
            for member in accepted_members:
                questions.append('Принятие решения о приеме '
                                 + member.fio + ' в члены Жилищного кооператива')

        elif question.question == 'Утверждение годового отчета кооператива и годовой бухгалтерской (финансовой) отчетности кооператива':
            questions.append(
                'Утверждение годового отчета кооператива и годовой бухгалтерской (финансовой) отчетности кооператива')

        else:
            continue

        for speaker in speakers:
            if speaker.question_id == question.pk:
                speech += str(number) + '.  По вопросу повестки дня выступил: ' + speaker.speaker
                speech += '\n\tОсновные тезисы выступления: ' + speaker.theses
                speech += '\n\tБыли заданы вопросы:'
                number_2 = 1
                for asked_question in asked_questions:
                    if asked_question.sub_question.id == speaker.pk:
                        speech += '\n\t\t' + str(number_2) + ') ' + asked_question.question
                        number_2 += 1

                speech += '\n\n\tПо вопросу повестки дня голосовали:\n\t'
                speech += 'За - ' + str(speaker.votes_for) + ', '
                speech += 'Против - ' + str(speaker.votes_against) + ', '
                speech += 'Воздержался - ' + str(speaker.votes_abstained)
                speech += '\n\n\tПо вопросу повестки дня постановили:'
                if speaker.decision:
                    speech += '\n\tРешение принято\n'
                else:
                    speech += '\n\tРешение не принято\n'

        number += 1
        full_speech += speech
        speech = ''

    questions_string = strings_creating(0, questions)

    context = {'cooperative_name': meeting.cooperative.cooperative_name,
               'cooperative_address': meeting.cooperative.cooperative_address,
               'cooperative_itn': meeting.cooperative.cooperative_itn,
               'cooperative_email_address': meeting.cooperative.cooperative_email_address,
               'date': meeting.date,
               'end_date': meeting.end_date,
               'end_time': meeting.time,
               'meeting_chairman': meeting.cooperative.chairman_name,
               'secretary': meeting.secretary,
               'email_address': cooperative_member.email_address,
               'members': members,
               'questions': questions_string,
               'vote_counter': meeting.vote_counter}

    if (meeting.meeting_type == 'regular' and meeting.quorum) or (
            meeting.meeting_format == 'intramural' and meeting.quorum):
        doc = DocxTemplate("/usr/src/app/doc/Protocol_regular.docx")
        context['speech'] = full_speech

    elif meeting.meeting_format == 'extramural' and meeting.quorum:
        doc = DocxTemplate("/usr/src/app/doc/Protocol_extramural.docx")
        context['speech'] = full_speech

    elif meeting.meeting_format == 'extramural' and not meeting.quorum:
        doc = DocxTemplate("/usr/src/app/doc/Protocol_extramural_no_quorum.docx")

    else:
        doc = DocxTemplate("/usr/src/app/doc/Protocol_intramural_no_quorum.docx")

    doc.render(context)
    doc.save('/usr/src/app/notification.docx')
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream


def create_decision(decision_number, meeting):
    initiators = {
        'chairman': 'правления кооператива',
        'auditor': 'ревизионной комиссии / ревизора',
        'members': 'членов кооператива'
    }

    meeting_formats = {
        'intramural': 'очной',
        'extramural': 'заочной'
    }

    today_date = datetime.date.today().strftime("%d.%m.%Y")

    number = str(decision_number) + '/' + today_date.split('.')[2][2:]

    questions_list = meeting.questions
    questions = []
    for question in questions_list.all():
        questions.append(question.question)

    questions_string = '\n\t\t'
    for index, question in enumerate(questions):
        questions_string = questions_string + str(index + 1) + '. ' + question + '\n\t\t'

    context = {'number': number,
               'cooperative_name': meeting.cooperative.cooperative_name,
               'cooperative_address': meeting.cooperative.cooperative_address,
               'cooperative_itn': meeting.cooperative.cooperative_itn,
               'cooperative_telephone_number': meeting.cooperative.cooperative_telephone_number,
               'cooperative_email_address': meeting.cooperative.cooperative_email_address,
               'initiator': initiators[meeting.initiator],
               'date': today_date,
               'today_date': today_date,
               'chairman_name': meeting.cooperative.chairman_name}

    if meeting.conduct_decision:
        doc = DocxTemplate("/usr/src/app/doc/Decision_1.docx")
        context['meeting_format'] = meeting_formats[meeting.meeting_format]
        context['questions'] = questions_string

    else:
        doc = DocxTemplate("/usr/src/app/doc/Decision_2.docx")

        if meeting.conduct_reason == 0:
            conduct_reason = 'не соблюден предусмотренный Уставом порядок предъявления требований.'
        elif meeting.conduct_reason == 1:
            conduct_reason = 'ни один вопрос не относится к компетенции общего собрания.'
        elif meeting.conduct_reason == 2:
            conduct_reason = 'требование предъявлено органом, не имеющим полномочий по предъявлению требования.'
        else:
            conduct_reason = 'требование подано меньшим количеством членов кооператива, чем предусмотрено Уставом.'

        context['conduct_reason'] = conduct_reason

    doc.render(context)
    doc.save('/usr/src/app/decision.docx')
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream


def create_requirement(meeting, members):
    if meeting.initiator == 'chairman':
        name = meeting.cooperative.chairman_name
        name_type = 'Председатель кооператива:'
        sign_name = '________________________ ' + name
    elif meeting.initiator == 'auditor':
        name = meeting.cooperative.auditor_name
        name_type = 'Ревизор / председатель ревизионной комиссии:'
        sign_name = '________________________ ' + name
    else:
        name = ''
        name_type = ''
        sign_name = ''
        for member in members:
            name += member + '\n'
            name_type += 'Член Кооператива:\n\n\n'
            sign_name += '________________________ ' + member + '\n\n\n'

    today_date = datetime.date.today().strftime("%d.%m.%Y")

    questions_list = meeting.questions
    questions = []
    for question in questions_list.all():
        questions.append(question.question)

    questions_string = strings_creating(0, questions)

    context = {'name': name,
               'cooperative_name': meeting.cooperative.cooperative_name,
               'reason': meeting.reason,
               'questions': questions_string,
               'today_date': today_date,
               'name_type': name_type,
               'sign_name': sign_name}

    if meeting.meeting_format == 'intramural':
        doc = DocxTemplate("/usr/src/app/doc/Requirement_intramural.docx")

    else:
        doc = DocxTemplate("/usr/src/app/doc/Requirement_extramural.docx")

    doc.render(context)
    doc.save('/usr/src/app/requirement.docx')
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream


def create_notification(notification_number, pk, fio, meeting, responsible_name, convert_name,
                        reorganization_accepted_members, terminated_members, accepted_members, files):
    hours = str(meeting.time).split(':')[0]
    minutes = str(meeting.time).split(':')[1]

    if files:
        filenames = []
        for file in files:
            filenames.append(file.name.rsplit('.', 1)[0])

        filenames_string = 'Приложения:\n' + strings_creating(0, filenames)
    else:
        filenames_string = ''

    today_date = datetime.date.today().strftime("%d.%m.%Y")

    number = 'У' + str(notification_number) + '-' + str(pk) + '/' + today_date.split('.')[2][2:]

    questions_list = meeting.questions
    chosen_questions = []
    for question in questions_list.all():
        chosen_questions.append(question.question)

    questions = []
    questions_shift = 0

    if 'Принятие решения о реорганизации кооператива' in chosen_questions:
        questions_shift = 7
        for member in reorganization_accepted_members:
            questions.append('Принятие ' + member.fio +
                             ' в члены товарищества собственников жилья «' + convert_name + '»')

    for question in chosen_questions:
        if question == 'Прекращение полномочий отдельных членов правления':
            for member in terminated_members:
                questions.append('Досрочное прекращение полномочий члена Правления жилищного кооператива '
                                 + member.fio + '.')

        elif question == 'Принятие решения о приеме граждан в члены кооператива':
            for member in accepted_members:
                questions.append('Принятие решения о приеме '
                                 + member.fio + ' в члены Жилищного кооператива')

        elif question == 'Утверждение годового отчета кооператива и годовой бухгалтерской (финансовой) отчетности кооператива':
            questions.append(
                'Утверждение годового отчета кооператива и годовой бухгалтерской (финансовой) отчетности кооператива')

        else:
            continue

    questions_string = strings_creating(questions_shift, questions)

    context = {'member_name': fio,
               'cooperative_name': meeting.cooperative.cooperative_name,
               'cooperative_address': meeting.cooperative.cooperative_address,
               'cooperative_telephone_number': meeting.cooperative.cooperative_telephone_number,
               'cooperative_email_address': meeting.cooperative.cooperative_email_address,
               'notification_number': number,
               'date': meeting.date,
               'hours': hours,
               'minutes': minutes,
               'questions': questions_string,
               'filenames': filenames_string,
               'chairman_name': meeting.cooperative.chairman_name,
               'today_date': today_date}

    if meeting.meeting_type == 'regular':
        if 'Принятие решения о реорганизации кооператива' in chosen_questions:
            doc = DocxTemplate("/usr/src/app/doc/Notification_regular_reorganization.docx")
            context['responsible_name'] = responsible_name
            context['convert_name'] = convert_name
        else:
            doc = DocxTemplate("/usr/src/app/doc/Notification_regular.docx")
        context['meeting_address'] = meeting.place

    elif meeting.meeting_type == 'irregular' and meeting.meeting_format == 'intramural':
        if 'Принятие решения о реорганизации кооператива' in chosen_questions:
            doc = DocxTemplate("/usr/src/app/doc/Notification_regular_reorganization.docx")
            context['responsible_name'] = responsible_name
            context['convert_name'] = convert_name
        else:
            doc = DocxTemplate("/usr/src/app/doc/Notification_regular.docx")
        context['meeting_address'] = meeting.place

    else:
        if 'Принятие решения о реорганизации кооператива' in chosen_questions:
            doc = DocxTemplate("/usr/src/app/doc/Notification_regular_reorganization.docx")
            context['responsible_name'] = responsible_name
            context['convert_name'] = convert_name
        else:
            doc = DocxTemplate("/usr/src/app/doc/Notification_regular.docx")

    doc.render(context)
    doc.save('/usr/src/app/notification' + str(notification_number) + '.docx')
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream
