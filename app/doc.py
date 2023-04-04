import datetime
import io

from docxtpl import DocxTemplate


def strings_creating(elements):
    elements_string = '\n\t'
    for index, element in enumerate(elements):
        elements_string = elements_string + str(index + 1) + '. ' + element + '\n\t'
    return elements_string


def create_decision(decision_number, meeting):
    today_date = datetime.date.today().strftime("%d.%m.%Y")
    
    number = str(decision_number) + '/' + today_date.split('.')[2][2:]

    questions_list = meeting.questions
    questions = []
    for question in questions_list.all():
        questions.append(question.question)
    
    questions_string = strings_creating(questions)

    context = { 'number' : number,
                'cooperative_name' : meeting.cooperative.cooperative_name,
                'cooperative_address' : meeting.cooperative.cooperative_address,
                'cooperative_itn' : meeting.cooperative.cooperative_itn,
                'cooperative_telephone_number' : meeting.cooperative.cooperative_telephone_number,
                'cooperative_email_address' : meeting.cooperative.cooperative_email_address,
                'initiator': meeting.initiator,
                'date' : meeting.date,
                'today_date' : today_date,
                'chairman_name' : meeting.cooperative.chairman_name }
    
    if meeting.conduct_decision == True:
        doc = DocxTemplate("/usr/src/app/doc/Decision_1.docx")
        context['meeting_format'] = meeting.meeting_format
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
            name += member.fio + '\n'
            name_type += 'Член Кооператива:\n\n'
            sign_name += '________________________ ' + member.fio + '\n\n'
        #for member in representatives:
        #    name += member.representative + '\n'
        #    name_type += 'Представитель члена Кооператива:\n'
        #    sign_name += '________________________ ' + member.representative + '\n\n'
    
    today_date = datetime.date.today().strftime("%d.%m.%Y")
    
    questions_list = meeting.questions
    questions = []
    for question in questions_list.all():
        questions.append(question.question)
    
    questions_string = strings_creating(questions)

    context = { 'name' : name,
                'cooperative_name' : meeting.cooperative.cooperative_name,
                'reason' : meeting.reason,
                'questions' : questions_string,
                'today_date' : today_date,
                'name_type' : name_type,
                'sign_name' : sign_name }
    
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

    
def docs_filling(notification_number, pk, fio, meeting, files):
    hours = str(meeting.time).split(':')[0]
    minutes = str(meeting.time).split(':')[1]    

    filenames = []
    for file in files:
        filenames.append(file.name)
   
    filenames_string = strings_creating(filenames)

    today_date = datetime.date.today().strftime("%d.%m.%Y")

    number = str(notification_number) + '-' + str(pk) + '/' + today_date.split('.')[2][2:]
    
    questions_list = meeting.questions
    questions = []
    for question in questions_list.all():
        questions.append(question.question)
    
    questions_string = strings_creating(questions)

    context = { 'member_name' : fio,
                'cooperative_name' : meeting.cooperative.cooperative_name,
                'cooperative_address' : meeting.cooperative.cooperative_address,
                'cooperative_telephone_number' : meeting.cooperative.cooperative_telephone_number,
                'cooperative_email_address' : meeting.cooperative.cooperative_email_address,
                'notification_number' : number,
                'date' : meeting.date,
                'hours' : hours,
                'minutes' : minutes,
                'questions' : questions_string,
                'filenames' : filenames_string,
                'chairman_name' : meeting.cooperative.chairman_name,
                'today_date' :  today_date }
    
    if meeting.meeting_type == 'regular':
        doc = DocxTemplate("/usr/src/app/doc/template_1.docx")
        context['meeting_address'] = meeting.place
    
    elif meeting.meeting_type == 'irregular' and meeting.meeting_format == 'intramural':
        doc = DocxTemplate("/usr/src/app/doc/template_2.docx") 
        context['meeting_address'] = meeting.place

    else:
        doc = DocxTemplate("/usr/src/app/doc/template_3.docx")

    doc.render(context)
    doc.save('/usr/src/app/notification'+str(notification_number)+'.docx')
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream

