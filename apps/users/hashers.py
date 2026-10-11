import hashlib
import hmac
import secrets

from datetime import timedelta, datetime

from django.conf import settings
from django.utils import timezone


@staticmethod
def generate_otp() -> str:
   return f"{secrets.randbelow(10000):04d}"


@staticmethod
def hash_otp(otp: str, email: str, purpose: int) -> str:
   """Create a keyed HMAC digest bound to the email and purpose."""
   message = f"{email.strip().lower()}:{otp}:{purpose}"

   return hmac.new(
      settings.SECRET_KEY.encode(),
      message.encode("utf-8"),
      hashlib.sha256,
   ).hexdigest()



@staticmethod
def verify_otp(otp: str, email: str, purpose: int, stored_otp: str) -> bool:
   """Verify an OTP against a stored digest."""

   user_hash = hash_otp(otp, email, purpose)

   return hmac.compare_digest(user_hash, stored_otp)
  


def get_otp_expiry_time(date_time: datetime = None) -> datetime:
   if date_time is None:
      date_time = timezone.now()

   return date_time + timedelta(seconds=settings.OTP_EXPIRY_SECONDS)
