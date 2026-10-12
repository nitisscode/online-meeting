from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from apps.users.models import OTPPurpose


def send_otp_email(email, purpose, otp):
   purpose_label = OTPPurpose(purpose).label
   expiry_minutes = settings.OTP_EXPIRY_SECONDS // 60

   html_message = render_to_string("email/otp_email.html", {
      "purpose": purpose_label,
      "otp": otp,
      "expiry_minutes": expiry_minutes,
   })

   send_mail(
      subject=f"Your {purpose_label} OTP",
      message=f"Your {purpose_label} OTP is {otp}. It expires in {expiry_minutes} minutes.",
      from_email=settings.DEFAULT_FROM_EMAIL,
      recipient_list=[email],
      html_message=html_message,
   )

   return True
