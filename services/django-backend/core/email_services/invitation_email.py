from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from core.models import Meeting

def send_invitation_email(meeting_id):
   try:
      meeting = Meeting.objects.prefetch_related("participants__user").get(id=meeting_id)
   except Meeting.DoesNotExist:
      return False
   
   recipients = [
      p.user.email for p in meeting.participants.all() if p.user.email
   ]

   if not recipients:
      return False

   meeting_name = meeting.title
   meeting_date = meeting.scheduled_at.strftime("%B %d, %Y") if meeting.scheduled_at else "TBD"
   meeting_time = meeting.scheduled_at.strftime("%I:%M %p") if meeting.scheduled_at else "TBD"
   message = render_to_string("email/invitation_email.html", {
      "meeting_name": meeting_name,
      "meeting_date": meeting_date,
      "meeting_time": meeting_time,
      "meeting_code": meeting.meeting_code,
   })
   
   send_mail(
      subject=f"Invitation to {meeting_name}",
      from_email=settings.DEFAULT_FROM_EMAIL,
      recipient_list=recipients,
      html_message=message,
   )