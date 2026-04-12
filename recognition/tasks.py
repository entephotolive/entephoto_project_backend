from celery import shared_task
from .models import Image, FaceEncoding
from .services.face_encode import encode_faces


@shared_task
def process_image_faces(image_id):
    try:
        image_obj = Image.objects.get(id=image_id)

        encodings = encode_faces(image_obj.image.path)

        if not encodings:
            return "No faces found"

        for enc in encodings:
            FaceEncoding.objects.create(
                image=image_obj,
                encoding=enc.tobytes()
            )

        return f"{len(encodings)} faces saved"

    except Exception as e:
        return str(e)