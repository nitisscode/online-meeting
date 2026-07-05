from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include

from apps.users.urls import urlpatterns as users_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", include(users_urls)),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
