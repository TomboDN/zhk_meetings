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


def create_bulletin(meeting, member, terminated_members, accepted_members, notification_number, pk):
    tpl = DocxTemplate("/usr/src/app/doc/Bulletin.docx")

    bulletin_number = 'Б-' + str(notification_number) + str(pk) + '/' + meeting.date.strftime("%d.%m.%Y").split('.')[2][2:]  

    context = {'bulletin_number': bulletin_number,
               'cooperative_name': meeting.cooperative.cooperative_name,
               'cooperative_address': meeting.cooperative.cooperative_address,
               'cooperative_itn': meeting.cooperative.cooperative_itn,
               'name': member.fio,
               'voices': []}

    context = {
        'voices': [],
    }

    questions_list = meeting.questions
    chosen_questions = []
    for question in questions_list.all():
        chosen_questions.append(question.question)

    i = 1
    for question in chosen_questions:
        if question == 'Прекращение полномочий отдельных членов правления':
            for member in terminated_members:
                d = {
                        'question': str(i)+'. '+'Досрочное прекращение полномочий члена Правления жилищного кооператива '+ member.fio + '.',
                    }
                context['voices'].append(d)
                i += 1
        elif question == 'Принятие решения о приеме граждан в члены кооператива':
            for member in accepted_members:
                d = {
                        'question': str(i)+'. '+'Принятие решения о приеме ' + member.fio + ' в члены Жилищного кооператива.',
                    }
                context['voices'].append(d)
                i += 1
        elif question == 'Утверждение годового отчета кооператива и годовой бухгалтерской (финансовой) отчетности кооператива':
            d = {
                    'question': str(i)+'. '+'Утверждение годового отчета кооператива и годовой бухгалтерской (финансовой) отчетности кооператива.',
                }
            context['voices'].append(d)
            i += 1
        else:
            i += 1
            continue


    jinja_env = jinja2.Environment(autoescape=True)
    tpl.render(context, jinja_env)
    tpl.save('/usr/src/app/Bulletin.docx')
    file_stream = io.BytesIO()
    tpl.save(file_stream)
    file_stream.seek(0)
    return file_stream


no_quorum_new_meeting = {
    True: "В связи с отсутствием кворума для рассмотрения вопросов повестки дня в предусмотренный "
          "Уставом кооператива срок будет проведено повторное общее собрание членов жилищного "
          "кооператива по той же повестке дня. Члены Кооператива будут уведомлены о времени и месте "
          "проведения повторного общего собрания в сроки и порядки, установленные Уставом "
          "кооператива.",
    False: "Повторное общее собрание членов жилищного кооператива по той же повестке дня проводиться "
           "не будет."
}


decisions = {
    'acception_true': '\n\tВ соответствии со ст. 121 ЖК РФ принять в члены жилищного кооператива “',
    'acception_false': '\n\tОтказать в принятии в члены жилищного кооператива “',
    'termination_true': '\n\tДосрочно прекратить полномочия члена правления ЖК “',
    'termination_false': '\n\tОтказать в досрочном прекращении полномочий члена правления ЖК “',
    'report_true': '\n\tУтвердить годовой отчет и годовую бухгалтерскую (финансовую) отчетность ЖК “'
}


def create_protocol(cooperative_member, meeting, convert_name, attendants, sub_questions, asked_questions,
                    terminated_members, accepted_members, reorganization_accepted_members, new_meeting=None):
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

        for sub_question in sub_questions:
            if sub_question.question_id == question.pk:
                speech += str(number) + '.  По вопросу повестки дня выступил: ' + sub_question.speaker
                speech += '\n\tОсновные тезисы выступления: ' + sub_question.theses
                speech += '\n\tБыли заданы вопросы:'
                number_2 = 1
                for asked_question in asked_questions:
                    if asked_question.sub_question.id == sub_question.pk:
                        speech += '\n\t\t' + str(number_2) + ') ' + asked_question.question
                        number_2 += 1

                speech += '\n\n\tПо вопросу повестки дня голосовали:\n\t'
                speech += 'За - ' + str(sub_question.votes_for) + ', '
                speech += 'Против - ' + str(sub_question.votes_against) + ', '
                speech += 'Воздержался - ' + str(sub_question.votes_abstained)
                speech += '\n\n\tПо вопросу повестки дня постановили:'
                if sub_question.decision:
                    #speech += '\n\tРешение принято\n'
                    if question.question == 'Принятие решения о приеме граждан в члены кооператива':
                        for member in accepted_members:
                            speech += decisions['acception_true'] + meeting.cooperative.cooperative_name + '” ' + member.fio
                    elif question.question == 'Прекращение полномочий отдельных членов правления':
                        for member in terminated_members:
                            speech += decisions['termination_true'] + meeting.cooperative.cooperative_name + '” ' + member.fio + ' c ' + member.date.strftime("%d.%m.%Y")
                    elif question.question == 'Утверждение годового отчета кооператива и годовой бухгалтерской (финансовой) отчетности кооператива':
                            speech += decisions['report_true'] + meeting.cooperative.cooperative_name + '”'
                    else:
                        continue
                else:
                    #speech += '\n\tРешение не принято\n'
                    if question.question == 'Принятие решения о приеме граждан в члены кооператива':
                        for member in accepted_members:
                            speech += decisions['acception_false'] + meeting.cooperative.cooperative_name + '” ' + member.fio
                    elif question.question == 'Прекращение полномочий отдельных членов правления':
                        for member in terminated_members:
                            speech += decisions['termination_false'] + meeting.cooperative.cooperative_name + '” ' + member.fio + ' c ' + member.date.strftime("%d.%m.%Y")
                    else:
                        continue

        speech += '\n'
        number += 1
        full_speech += speech
        speech = ''

    questions_string = strings_creating(0, questions)

    context = {'cooperative_name': meeting.cooperative.cooperative_name,
               'cooperative_address': meeting.cooperative.cooperative_address,
               'cooperative_itn': meeting.cooperative.cooperative_itn,
               'cooperative_email_address': meeting.cooperative.cooperative_email_address,
               'cooperative_telephone_number': meeting.cooperative.cooperative_telephone_number,
               'date': meeting.date,
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

    if new_meeting is not None:
        context['new_meeting'] = no_quorum_new_meeting[new_meeting]

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

    number = 'Р-' + str(decision_number) + '/' + today_date.split('.')[2][2:]

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

    number = 'У-' + str(notification_number) + str(pk) + '/' + today_date.split('.')[2][2:]

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
