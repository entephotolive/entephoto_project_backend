

from django.urls import path
from .views import get_images_by_event, list_weddings, upload_images, scan_face,create_wedding,delete_wedding

urlpatterns = [
    path('create-wedding/', create_wedding),
    path('upload-images/', upload_images),
    path('scan-face/', scan_face),
    path('weddings/', list_weddings),
    path('delete-wedding/<int:id>/', delete_wedding),
    path('images/<int:event_id>/', get_images_by_event),
]




