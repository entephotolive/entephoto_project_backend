

from django.urls import path
from .views import upload_images, scan_face,create_wedding

urlpatterns = [
    path('create-wedding/', create_wedding),
    path('upload-images/', upload_images),
    path('scan-face/', scan_face),
]




