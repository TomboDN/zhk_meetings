from docxtpl import DocxTemplate
import datetime

def strings_creating(elements):
    elements_string = ''
    for index, element in enumerate(elements):
        elements_string = elements_string + str(index + 1) + '. ' + element + '\n'
    return elements_string


print("Выберите тип собрания\n1 - Внеочередное очное\n2 - Очное\n3 - Внеочередное заочное")
type = int(input())

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
notification_number = input()
if cooperative_type == 'жилищный':
    short_cooperative_type = 'ЖК'
else:
    short_cooperative_type = 'ЖCК'
l = len(cooperative_type)
cooperative_type = cooperative_type[:l-2] + 'ого'
if type == 3:
    print("Введите дату проведения собрания")
    date = input()
else:
    print("Введите время проведения собрания")
    date_time = input()
print("Введите вопросы для рассмотрения; в конце списка вопросов введите \'end\'")
questions = list()
question = input()
while not question == 'end':
    questions.append(question)
    question = input()
if type == 3:
    print("Введите срок отправки  бюллетеней")
    date_time = input()
else:
    print("Введите адрес проведения собрания")
    meeting_address = input()
print("Введите приложения для рассмотрения; в конце списка приложений введите \'end\'")
filenames = list()
filename = input()
while not filename == 'end':
    filenames.append(filename)
    filename = input()
print("Введите ФИО Председателя")
chairman_name = input()

today_date = datetime.date.today().strftime("%d.%m.%Y")

questions_string = strings_creating(questions)

filenames_string = strings_creating(filenames)

context = { 'cooperative_type' : cooperative_type,
                'member_name' : member_name,
                'cooperative_name' : cooperative_name,
                'cooperative_address' : cooperative_address,
                'cooperative_telephone_number' : cooperative_telephone_number,
                'cooperative_email_address' : cooperative_email_address,
                'date_time' : date_time,
                'notification_number' : notification_number,
                'short_cooperative_type' : short_cooperative_type,
                'cooperative_name' : cooperative_name,
                'questions' : questions_string,
                'filenames' : filenames_string,
                'chairman_name' : chairman_name,
                'today_date' :  today_date}

if type == 1:  
    doc = DocxTemplate("template_1.docx") 
    context['meeting_address'] = meeting_address
    
elif type == 2:
    doc = DocxTemplate("template_2.docx")
    context['meeting_address'] = meeting_address

else:
    doc = DocxTemplate("template_3.docx")
    context['date'] = date

doc.render(context)
doc.save('notification.docx')

