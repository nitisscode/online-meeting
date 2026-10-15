from urllib.parse import parse_qs

from channels.db import database_sync_to_async

from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication



class JWTAuthMiddleware:
   def __init__(self, inner):
      self.inner = inner
      self.authenticator = JWTAuthentication()

   async def __call__(self, scope, receive, send):
      try:
         token = parse_qs(scope["query_string"].decode()).get("token", [None])[0]
         user, token_exp = await self.authenticate(token)
         return await self.inner({**scope, "user": user, "token_exp": token_exp}, receive, send)
      except Exception as e:
         print(e)


   @database_sync_to_async
   def authenticate(self, token):
      if not token:
         return AnonymousUser(), None
      
      try:
         token = self.authenticator.get_validated_token(token)
         return self.authenticator.get_user(token), token["exp"]

      except AuthenticationFailed:
         return AnonymousUser(), None