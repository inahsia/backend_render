"""
URL Configuration for Red Ball Cricket Academy
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse


def home(request):
    return HttpResponse("Backend is running successfully 🎉")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),  # 👈 Root URL — this fixes the 404 at /
    path('api/', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
