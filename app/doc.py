import datetime

from docxtpl import DocxTemplate


def strings_creating(elements):
    elements_string = ''
    for index, element in enumerate(elements):
        elements_string = elements_string + str(index + 1) + '. ' + element + '\n'
    return elements_string


def docs_filling(type, format, notification_number, fio, meeting, files):
    hours = str(meeting.time).split(':')[0]
    minutes = str(meeting.time).split(':')[1]    

    filenames = []
    for file in files:
        filenames.append(file.name)
   
    filenames_string = strings_creating(filenames)

    today_date = datetime.date.today().strftime("%d.%m.%Y")
    
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
                'notification_number' : notification_number,
                'date' : meeting.date,
                'hours' : hours,
                'minutes' : minutes,
                'questions' : questions_string,
                'filenames' : filenames_string,
                'chairman_name' : meeting.cooperative.chairman_name,
                'today_date' :  today_date }
    
    if type == 'regular':
        doc = DocxTemplate("/usr/src/app/doc/template_1.docx")
        context['meeting_address'] = meeting.place
    
    elif type == 'irregular' and format == 'intramural':
        doc = DocxTemplate("/usr/src/app/doc/template_2.docx") 
        context['meeting_address'] = meeting.place

    else:
        doc = DocxTemplate("/usr/src/app/doc/template_3.docx")

    doc.render(context)
    doc.save('/usr/src/app/notification'+str(notification_number)+'.docx')

