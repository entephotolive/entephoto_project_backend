
from django.db import models


class Wedding(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


#  Stores actual image
class Image(models.Model):
    wedding = models.ForeignKey(Wedding, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to='weddings/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.id} - {self.wedding.name}"


#  Stores each detected face encoding
class FaceEncoding(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="faces")
    encoding = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Face {self.id} (Image {self.image.id})"