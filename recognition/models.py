from django.db import models


class Wedding(models.Model):
    """Represents a wedding/event session."""
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Image(models.Model):
    """
    Stores metadata for an uploaded photo.
    The actual file lives on UploadThing CDN — we only store the URL and key.
    """
    wedding = models.ForeignKey(Wedding, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=500)           # UploadThing CDN URL
    uploadthing_key = models.CharField(max_length=255)    # UploadThing file key (for deletion)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.id} — {self.wedding.name}"


class FaceEncoding(models.Model):
    """
    Stores a 128-dimension face encoding (as raw bytes) for one face in an image.
    One Image can have multiple FaceEncoding rows (one per detected face).
    """
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='faces')
    encoding = models.BinaryField()                       # numpy float64 array → bytes
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Face {self.id} (Image {self.image_id})"