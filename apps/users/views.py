from django.contrib.auth.models import update_last_login

from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.users.serializers import (
   MeSerializer, 
   UserSignUpSerializer, 
   UserLoginSerializer,
   OTPAuthenticationSerializer,
   OTPVerifySerializer
)
from apps.users.models import OTPAuthentication, User, OTPPurpose
from apps.users.hashers import generate_otp, get_otp_expiry_time, hash_otp, verify_otp

class UserSignUpView(CreateAPIView):
   serializer_class = UserSignUpSerializer
   permission_classes = [AllowAny]



class UserLoginView(TokenObtainPairView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]


class RequestOTPView(CreateAPIView):
   serializer_class = OTPAuthenticationSerializer
   permission_classes = [AllowAny]

   def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        purpose = serializer.validated_data["purpose"]

        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)
        except User.MultipleObjectsReturned:
            return Response({"error": "Multiple users found"}, status=status.HTTP_400_BAD_REQUEST)

        otp = generate_otp()
        hashed_otp = hash_otp(otp, email, purpose)

        otp_authentication = OTPAuthentication.objects.create(
            email=email,
            purpose=purpose,
            expires_at=get_otp_expiry_time(),
            hashed_otp=hashed_otp,
        )

        #send_otp_email(email, otp)

        return Response(
            {
                "email": email,
                "purpose": purpose,
                "otp": otp,
            },
            status=status.HTTP_201_CREATED,
        )

        


class OTPAuthView(CreateAPIView):
   serializer_class = OTPVerifySerializer
   permission_classes = [AllowAny]

   def create(self, request, *args, **kwargs):
      serializer = self.get_serializer(data=request.data)
      serializer.is_valid(raise_exception=True)

      email = serializer.validated_data["email"]
      purpose = serializer.validated_data["purpose"]
      otp = serializer.validated_data["otp"]

      if purpose != OTPPurpose.LOGIN:
         return Response({"error": "Invalid Request"}, status=status.HTTP_400_BAD_REQUEST)


      otp_auth = (
         OTPAuthentication.objects
         .filter(email=email, purpose=purpose, is_used=False)
         .order_by("-created_at")
         .first()
      )

      if otp_auth is None:
         return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

      if otp_auth.is_expired():
         return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)
      
      is_valid = verify_otp(otp, email, purpose, otp_auth.hashed_otp)

      if not is_valid:
         return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

      try:
         user = User.objects.get(email=email, is_active=True)
      except User.DoesNotExist:
         return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

      otp_auth.mark_as_used()

      token = UserLoginSerializer.get_token(user)
      
      update_last_login(None, user)

      return Response(
         {
            "refresh": str(token),
            "access": str(token.access_token),
            "user": MeSerializer(user).data,
         },
         status=status.HTTP_200_OK,
      )




class MeAPIView(RetrieveAPIView):
   serializer_class = MeSerializer

   def get(self, request, *args, **kwargs):
      return Response(MeSerializer(request.user).data)
