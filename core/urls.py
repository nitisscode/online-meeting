from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include

from apps.meetings.urls import urlpatterns as meetings_urls
from apps.users.urls import urlpatterns as users_urls
from apps.chat.urls import urlpatterns as chat_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", include(users_urls)),
    path("meetings/", include(meetings_urls)),
    path("chat/", include(chat_urls)),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
