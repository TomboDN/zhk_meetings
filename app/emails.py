import os
import threading

from django.core.mail import EmailMessage, send_mass_mail
from zhk_meetings_app.models import CooperativeMember


class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()

        
def send_protocol(cooperative_meeting, protocol, member_email):
    msg = 'Здравствуйте! Сервис для проведения общих собраний членов жилищных кооперативов "Умное собрание" предлагает ознакомиться с информацией в приложении.'
    if cooperative_meeting.meeting_type == "regular":
        subject = "Протокол очередного собрания"
    elif cooperative_meeting.meeting_type == "irregular" and cooperative_meeting.meeting_format == "intramural":
        subject = "Протокол внеочередного очного собрания"
    elif cooperative_meeting.meeting_type == "irregular" and cooperative_meeting.meeting_format == "extramural":
        subject = "Протокол внеочередного заочного собрания"

    from_email = os.environ.get("EMAIL_HOST_USER")

    mail = EmailMessage(
        subject,
        msg,
        from_email,
        [member_email],
    )

    mail.attach('Протокол.pdf', protocol.getvalue(),
                'application/pdf')

    EmailThread(mail).start()


def send_bulletin(bulletin, member_email):
    msg = 'Здравствуйте! Сервис для проведения общих собраний членов жилищных кооперативов "Умное собрание" предлагает ознакомиться с информацией в приложении.'
    subject = 'Бюллетень для голосования на внеочередном заочном собрании'

    from_email = os.environ.get("EMAIL_HOST_USER")

    mail = EmailMessage(
        subject,
        msg,
        from_email,
        [member_email],
    )

    mail.attach('Бюллетень.pdf', bulletin.getvalue(),
                'application/pdf')

    EmailThread(mail).start()


def send_notification_email(cooperative_meeting, notification, user_attachments, member_email):
    msg = 'Здравствуйте! Сервис для проведения общих собраний членов жилищных кооперативов "Умное собрание" предлагает ознакомиться с информацией в приложении.'
    if cooperative_meeting.meeting_type == "regular":
        subject = "Уведомление об очередном собрании"
    elif cooperative_meeting.meeting_type == "irregular" and cooperative_meeting.meeting_format == "intramural":
        subject = "Уведомление о внеочередном очном собрании"
    elif cooperative_meeting.meeting_type == "irregular" and cooperative_meeting.meeting_format == "extramural":
        subject = "Уведомление о внеочередном заочном собрании"

    from_email = os.environ.get("EMAIL_HOST_USER")

    mail = EmailMessage(
        subject,
        msg,
        from_email,
        [member_email],
    )

    mail.attach('Уведомление.pdf', notification.getvalue(),
                'application/pdf')

    for file in user_attachments:
        content = None
        for chunk in file.chunks():
            if content is None:
                content = chunk
            else:
                content += chunk
        mail.attach(file.name, content, file.content_type)

    EmailThread(mail).start()


def send_mass_email(email_list):
    print(email_list)
    send_mass_mail(email_list, fail_silently=False)


def send_requirement(cooperative_meeting, requirement_file):
    cooperative = cooperative_meeting.cooperative
    cooperative_members = CooperativeMember.objects.filter(cooperative=cooperative)
    members_emails = set(member.email_address for member in cooperative_members)
    cooperative_emails = {cooperative.cooperative_email_address, cooperative.auditor_email_address}
    to_list = members_emails.union(cooperative_emails)

    msg = 'Здравствуйте! Сервис для проведения общих собраний членов жилищных кооперативов "Умное собрание" предлагает ознакомиться с информацией в приложении.'
    if cooperative_meeting.meeting_type == "irregular" and cooperative_meeting.meeting_format == "intramural":
        subject = "Требование о созыве внеочередного очного общего собрания"
    elif cooperative_meeting.meeting_type == "irregular" and cooperative_meeting.meeting_format == "extramural":
        subject = "Требование о созыве внеочередного заочного общего собрания"

    from_email = os.environ.get("EMAIL_HOST_USER")
    to_email = to_list

    mail = EmailMessage(
        subject,
        msg,
        from_email,
        to_email,
    )

    mail.attach('Требование.pdf', requirement_file.getvalue(),
                'application/pdf')

    EmailThread(mail).start()


def send_decision(cooperative_meeting, decision_file):
    cooperative = cooperative_meeting.cooperative
    cooperative_members = CooperativeMember.objects.filter(cooperative=cooperative)
    members_emails = set(member.email_address for member in cooperative_members)
    cooperative_emails = {cooperative.cooperative_email_address, cooperative.auditor_email_address}
    to_list = members_emails.union(cooperative_emails)

    msg = 'Здравствуйте! Сервис для проведения общих собраний членов жилищных кооперативов "Умное собрание" предлагает ознакомиться с информацией в приложении.'
    if cooperative_meeting.conduct_decision:
        subject = "Решение о проведении внеочередного общего собрания"
    else:
        subject = "Решение об отказе в проведении внеочередного общего собрания"

    from_email = os.environ.get("EMAIL_HOST_USER")
    to_email = to_list

    mail = EmailMessage(
        subject,
        msg,
        from_email,
        to_email,
    )

    mail.attach('Решение о проведении собрания.pdf', decision_file.getvalue(),
                'application/pdf')

    EmailThread(mail).start()
