from docxtpl import DocxTemplate
from docx2pdf import convert

print("Выберите тип собрания\n1 - Внеочередное очное\n2 - Очное\n3 - Внеочередное заочное")
type = int(input())

if type == 1:
    print("Введите тип кооператива ")
    cooperative_type = input()
    print("Введите ФИО участника")
    member_name = input()
    print("Введите название кооператива")
    cooperative_name = input()
    print("Введите адрес кооператива")
    cooperative_address = input()
    print("Введите телефон кооператива")
    cooperative_telephone_number = input()
    print("Введите адрес эл. почты кооператива")
    cooperative_email_address = input()
    print("Введите номер уведомления")
    notification_number = int(input())
    if cooperative_type == 'жилищный':
        short_cooperative_type = 'ЖК'
    else:
        short_cooperative_type = 'ЖCК'
    l = len(cooperative_type)
    cooperative_type = cooperative_type[:l-2] + 'ого'
    print("Введите время проведения собрания")
    date_time = input()
    print("Введение вопрос 1) собрания")
    question_1 = input()
    print("Введение вопрос 2) собрания")
    question_2 = input()
    print("Введение вопрос 3) собрания")
    question_3 = input()
    print("Введите адрес проведения собрания")
    meeting_address = input()
    print("Введите приложение 1")
    filename_1 = input()
    print("Введите приложение 2")
    filename_2 = input()
    print("Введите приложение 3")
    filename_3 = input()
    print("Введите ФИО Председателя")
    chairman_name = input()

    doc = DocxTemplate("template_1.docx") 

    context = { 'cooperative_type' : cooperative_type,
                'member_name' : member_name,
                'cooperative_name' : cooperative_name,
                'cooperative_address' : cooperative_address,
                'cooperative_telephone_number' : cooperative_telephone_number,
                'cooperative_email_address' : cooperative_email_address,
                'notification_number' : notification_number,
                'short_cooperative_type' : short_cooperative_type,
                'cooperative_name' : cooperative_name,
                'date_time' : date_time,
                'question_1' : question_1,
                'question_2' : question_2,
                'question_3' : question_3,
                'meeting_address' : meeting_address,
                'filename_1' : filename_1,
                'filename_2' : filename_2,
                'filename_3' : filename_3,
                'chairman_name' : chairman_name }
    

    doc.render(context)
    doc.save('notification.docx')

elif type == 2:
    print("Введите тип кооператива ")
    cooperative_type = input()
    print("Введите ФИО участника")
    member_name = input()
    print("Введите название кооператива")
    cooperative_name = input()
    print("Введите адрес кооператива")
    cooperative_address = input()
    print("Введите телефон кооператива")
    cooperative_telephone_number = input()
    print("Введите адрес эл. почты кооператива")
    cooperative_email_address = input()
    print("Введите номер уведомления")
    notification_number = int(input())
    if cooperative_type == 'жилищный':
        short_cooperative_type = 'ЖК'
    else:
        short_cooperative_type = 'ЖCК'
    l = len(cooperative_type)
    cooperative_type = cooperative_type[:l-2] + 'ого'
    print("Введите время проведения собрания")
    date_time = input()
    print("Введение вопрос 1) собрания")
    question_1 = input()
    print("Введение вопрос 2) собрания")
    question_2 = input()
    print("Введение вопрос 3) собрания")
    question_3 = input()
    print("Введите адрес проведения собрания")
    meeting_address = input()
    print("Введите приложение 1")
    filename_1 = input()
    print("Введите приложение 2")
    filename_2 = input()
    print("Введите приложение 3")
    filename_3 = input()
    print("Введите ФИО Председателя")
    chairman_name = input()

    doc = DocxTemplate("template_2.docx") 

    context = { 'cooperative_type' : cooperative_type,
                'member_name' : member_name,
                'cooperative_name' : cooperative_name,
                'cooperative_address' : cooperative_address,
                'cooperative_telephone_number' : cooperative_telephone_number,
                'cooperative_email_address' : cooperative_email_address,
                'notification_number' : notification_number,
                'short_cooperative_type' : short_cooperative_type,
                'cooperative_name' : cooperative_name,
                'date_time' : date_time,
                'question_1' : question_1,
                'question_2' : question_2,
                'question_3' : question_3,
                'meeting_address' : meeting_address,
                'filename_1' : filename_1,
                'filename_2' : filename_2,
                'filename_3' : filename_3,
                'chairman_name' : chairman_name }
    

    doc.render(context)
    doc.save('notification.docx')
    
else:
    print("Введите тип кооператива ")
    cooperative_type = input()
    print("Введите ФИО участника")
    member_name = input()
    print("Введите название кооператива")
    cooperative_name = input()
    print("Введите адрес кооператива")
    cooperative_address = input()
    print("Введите телефон кооператива")
    cooperative_telephone_number = input()
    print("Введите адрес эл. почты кооператива")
    cooperative_email_address = input()
    print("Введите номер уведомления")
    notification_number = int(input())
    if cooperative_type == 'жилищный':
        short_cooperative_type = 'ЖК'
    else:
        short_cooperative_type = 'ЖCК'
    l = len(cooperative_type)
    cooperative_type = cooperative_type[:l-2] + 'ого'
    print("Введите дату проведения собрания")
    date = input()
    print("Введение вопрос 1) собрания")
    question_1 = input()
    print("Введение вопрос 2) собрания")
    question_2 = input()
    print("Введение вопрос 3) собрания")
    question_3 = input()
    print("Введите срок отправки  бюллетеней")
    date_time = input()
    print("Введите приложение 1")
    filename_1 = input()
    print("Введите приложение 2")
    filename_2 = input()
    print("Введите приложение 3")
    filename_3 = input()
    print("Введите ФИО Председателя")
    chairman_name = input()

    doc = DocxTemplate("template_2.docx") 

    context = { 'cooperative_type' : cooperative_type,
                'member_name' : member_name,
                'cooperative_name' : cooperative_name,
                'cooperative_address' : cooperative_address,
                'cooperative_telephone_number' : cooperative_telephone_number,
                'cooperative_email_address' : cooperative_email_address,
                'notification_number' : notification_number,
                'short_cooperative_type' : short_cooperative_type,
                'cooperative_name' : cooperative_name,
                'date' : date,
                'question_1' : question_1,
                'question_2' : question_2,
                'question_3' : question_3,
                'date_time' : date_time,
                'filename_1' : filename_1,
                'filename_2' : filename_2,
                'filename_3' : filename_3,
                'chairman_name' : chairman_name }
    

    doc.render(context)
    doc.save('notification.docx')

