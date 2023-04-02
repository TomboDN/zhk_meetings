import os

from django.core.mail import EmailMessage
from zhk_meetings_app.models import CooperativeMember


def send_notification(cooperative_meeting, user_attachments):
    cooperative = cooperative_meeting.cooperative
    cooperative_members = CooperativeMember.objects.filter(cooperative=cooperative)
    members_emails = set(member.email_address for member in cooperative_members)
    cooperative_emails = {cooperative.cooperative_email_address, cooperative.auditor_email_address}
    to_list = members_emails.union(cooperative_emails)

    if cooperative_meeting.meeting_type == "regular":
        subject = "Уведомление об очередном собрании"
        msg = ...
    elif cooperative_meeting.meeting_type == "irregular" and cooperative_meeting.meeting_format == "intramural":
        subject = "Уведомление о внеочередном очном собрании"
        msg = ...
    elif cooperative_meeting.meeting_type == "irregular" and cooperative_meeting.meeting_format == "extramural":
        subject = "Уведомление о внеочередном заочном собрании"
        msg = ...

    from_email = os.environ.get("EMAIL_HOST_USER")
    to_email = to_list

    mail = EmailMessage(
        subject,
        msg,
        from_email,
        to_email,
    )

    # TODO notification add

    for file in user_attachments:
        mail.attach(file.name, file.read(), file.content_type)

    email_res = mail.send()

    return email_res
