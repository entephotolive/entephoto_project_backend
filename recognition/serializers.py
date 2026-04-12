from rest_framework import serializers
from .models import Image, Wedding


class WeddingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wedding
        fields = ['id', 'name', 'created_at']


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'wedding', 'image_url', 'uploadthing_key', 'uploaded_at']