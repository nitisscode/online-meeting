from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.users.serializers import MeSerializer, UserSignUpSerializer, UserLoginSerializer


class UserSignUpView(CreateAPIView):
   serializer_class = UserSignUpSerializer
   permission_classes = [AllowAny]



class UserLoginView(TokenObtainPairView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]



class MeAPIView(RetrieveAPIView):
   serializer_class = MeSerializer

   def get(self, request, *args, **kwargs):
      return Response(MeSerializer(request.user).data)
