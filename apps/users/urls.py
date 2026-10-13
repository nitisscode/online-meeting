from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView, TokenBlacklistView

from apps.users.views import (
    MeAPIView, 
    OTPAuthView, 
    RequestOTPView, 
    UserLoginView, 
    UserSignUpView, 
    ForgotPasswordView, 
    ResetPasswordView
)

urlpatterns = [
    path("signup/", UserSignUpView.as_view(), name="signup"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("token/blacklist/", TokenBlacklistView.as_view(), name="token-blacklist"),
    path("otp/request/", RequestOTPView.as_view(), name="otp-request"),
    path("otp/verify/", OTPAuthView.as_view(), name="otp-verify"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),

    path("me/", MeAPIView.as_view(), name="me"),
]
