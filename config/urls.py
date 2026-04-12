from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('recognition.urls')),
]

# No static/media URL serving needed — photos are on UploadThing CDN