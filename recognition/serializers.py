

from rest_framework import serializers
from .models import Photo, Wedding

class WeddingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wedding
        fields = '__all__'


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = '__all__'