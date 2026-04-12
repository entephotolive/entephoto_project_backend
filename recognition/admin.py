from django.contrib import admin
from .models import Wedding, Image, FaceEncoding


@admin.register(Wedding)
class WeddingAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'wedding', 'image_url', 'uploaded_at')
    list_select_related = ('wedding',)
    readonly_fields = ('image_url', 'uploadthing_key', 'uploaded_at')


@admin.register(FaceEncoding)
class FaceEncodingAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'created_at')
    list_select_related = ('image',)