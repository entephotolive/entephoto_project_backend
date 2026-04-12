from django.contrib import admin

from django.contrib import admin
from .models import Wedding, Image, FaceEncoding
from .services.face_encode import encode_faces

            
from .tasks import process_image_faces   

# Wedding Admin
@admin.register(Wedding)
class WeddingAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


#  FaceEncoding Admin
@admin.register(FaceEncoding)
class FaceEncodingAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'created_at')


#  Image Admin (THIS IS WHERE save_model GOES)
@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'wedding', 'uploaded_at')

    def save_model(self, request, obj, form, change):
        """
        This runs when you upload image from admin
        """
        super().save_model(request, obj, form, change)

        # Only process on new upload (not edit)
        if not change:
            #  Send to background worker
            process_image_faces.delay(obj.id)            