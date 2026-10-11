from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import OTPAuthentication, OTPPurpose, User


class OTPLoginTests(APITestCase):
   email = "otp-user@example.com"

   def setUp(self):
      self.user = User.objects.create(
         username="otpuser",
         email=self.email,
         password="StrongPass123!",
      )
      self.request_url = reverse("otp-request")
      self.verify_url = reverse("otp-verify")

   def request_otp(self, purpose=OTPPurpose.LOGIN):
      response = self.client.post(
         self.request_url,
         {"email": self.email, "purpose": purpose},
         format="json",
      )
      self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
      return response.data["otp"]

   def verify_otp(self, otp, purpose=OTPPurpose.LOGIN):
      return self.client.post(
         self.verify_url,
         {"email": self.email, "purpose": purpose, "otp": otp},
         format="json",
      )

   def test_request_otp_creates_record(self):
      otp = self.request_otp()

      self.assertEqual(len(otp), 4)
      self.assertTrue(
         OTPAuthentication.objects.filter(email=self.email, purpose=OTPPurpose.LOGIN, is_used=False).exists()
      )

   def test_request_otp_unknown_email(self):
      response = self.client.post(
         self.request_url,
         {"email": "nobody@example.com", "purpose": OTPPurpose.LOGIN},
         format="json",
      )

      self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

   def test_verify_otp_returns_tokens(self):
      otp = self.request_otp()

      response = self.verify_otp(otp)

      self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
      self.assertIn("access", response.data)
      self.assertIn("refresh", response.data)
      self.assertEqual(response.data["user"]["email"], self.email)

      self.user.refresh_from_db()
      self.assertIsNotNone(self.user.last_login)
      self.assertTrue(OTPAuthentication.objects.get(email=self.email).is_used)

   def test_access_token_works_on_me_endpoint(self):
      otp = self.request_otp()
      access = self.verify_otp(otp).data["access"]

      self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
      response = self.client.get(reverse("me"))

      self.assertEqual(response.status_code, status.HTTP_200_OK)
      self.assertEqual(response.data["email"], self.email)

   def test_otp_cannot_be_reused(self):
      otp = self.request_otp()
      self.assertEqual(self.verify_otp(otp).status_code, status.HTTP_200_OK)

      response = self.verify_otp(otp)

      self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

   def test_wrong_otp_rejected(self):
      otp = self.request_otp()
      wrong_otp = "0000" if otp != "0000" else "1111"

      response = self.verify_otp(wrong_otp)

      self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
      self.assertEqual(response.data["error"], "Invalid OTP")

   def test_expired_otp_rejected(self):
      otp = self.request_otp()
      OTPAuthentication.objects.filter(email=self.email).update(
         expires_at=timezone.now() - timedelta(seconds=1)
      )

      response = self.verify_otp(otp)

      self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
      self.assertEqual(response.data["error"], "OTP expired")

   def test_only_latest_otp_is_valid(self):
      first_otp = self.request_otp()
      second_otp = self.request_otp()

      if first_otp != second_otp:
         self.assertEqual(self.verify_otp(first_otp).status_code, status.HTTP_400_BAD_REQUEST)
      self.assertEqual(self.verify_otp(second_otp).status_code, status.HTTP_200_OK)

   def test_non_login_purpose_does_not_issue_tokens(self):
      otp = self.request_otp(purpose=OTPPurpose.PASSWORD_RESET)

      response = self.verify_otp(otp, purpose=OTPPurpose.PASSWORD_RESET)

      self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
      self.assertNotIn("access", response.data)

   def test_missing_otp_field(self):
      response = self.client.post(
         self.verify_url,
         {"email": self.email, "purpose": OTPPurpose.LOGIN},
         format="json",
      )

      self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
      self.assertIn("otp", response.data)
