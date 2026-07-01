from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import dashboard_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='dashboard'),
    path('accounts/', include('accounts.urls')),
    path('questions/', include('questions.urls')),
    path('exams/', include('exams.urls')),
    path('results/', include('results.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
