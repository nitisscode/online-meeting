from django.contrib.auth import authenticate
from django.db.models import Q

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.users.models import User
from apps.users.models import OTPPurpose

class UserResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = fields


class UserSignUpSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password", "confirm_password"]
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True, "allow_blank": False},
            "username": {"required": True, "allow_blank": False},
            "first_name": {"required": True, "allow_blank": False},
        }

    def validate(self, attrs):
        if User.objects.filter(email=attrs.get("email")).exists():
            raise serializers.ValidationError({"email": "Email already exists."})

        if User.objects.filter(username=attrs.get("username")).exists():
            raise serializers.ValidationError({"username": "Username already exists."})

        if attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        return User.objects.create(**validated_data, password=password)


class UserLoginSerializer(TokenObtainPairSerializer):
    
   def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.fields[self.username_field].label = "Email or Username"

   def validate(self, attrs):
      identifier = attrs.get("email")
      password = attrs.get("password")

      user = User.objects.filter(
         Q(email__iexact=identifier) | Q(username__iexact=identifier)
      ).first()

      if user is None:
         raise AuthenticationFailed("No active user found with this email or username.")

      user = authenticate(
         request=self.context.get("request"),
         username=identifier,
         password=password,
      )
      if user is None:
         raise AuthenticationFailed("Incorrect email or password.")

      if not user.is_active:
         raise AuthenticationFailed("Your account is inactive. Contact support.")

      attrs["email"] = user.email

      data = super().validate(attrs)
      return data

   @classmethod
   def get_token(cls, user):
      token = super().get_token(user)
      token["email"] = user.email
      token["username"] = user.username
      return token


class OTPAuthenticationSerializer(serializers.Serializer):
   email = serializers.EmailField(required=True)
   purpose = serializers.ChoiceField(choices=OTPPurpose.choices, required=True)


class OTPVerifySerializer(serializers.Serializer):
   email = serializers.EmailField(required=True)
   purpose = serializers.ChoiceField(choices=OTPPurpose.choices, required=True)
   otp = serializers.CharField(required=True, min_length=4, max_length=4)


class MeSerializer(serializers.ModelSerializer):
   class Meta:
      model = User
      fields = ["id", "username", "email", "first_name", "last_name"]
      read_only_fields = fields