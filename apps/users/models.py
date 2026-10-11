from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from core.models import CoreModel
from .hashers import get_otp_expiry_time, hash_otp

class OTPPurpose(models.IntegerChoices):
    LOGIN = 0
    EMAIL_VERIFICATION = 1
    PASSWORD_RESET = 2


class UserManager(BaseUserManager):
    def create(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required.")

        if not email:
            raise ValueError("Email is required.")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )


class User(CoreModel, AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email


class OTPAuthentication(CoreModel):
    email = models.EmailField(db_index=True)
    hashed_otp = models.CharField(max_length=64)
    expires_at = models.DateTimeField(default=get_otp_expiry_time)
    purpose = models.IntegerField(choices=OTPPurpose.choices)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "OTP authentication"
        verbose_name_plural = "OTP authentications"

        indexes = [
            models.Index(fields=["email", "purpose"]),
        ]

    def __str__(self) -> str:
        return self.email

    def is_expired(self) -> bool:
        return self.expires_at < timezone.now()

    def mark_as_used(self):
        self.is_used = True
        self.save(update_fields=["is_used"])
